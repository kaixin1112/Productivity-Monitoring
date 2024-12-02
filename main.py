import tkinter as tk
from tkinter import messagebox
import socket
from cam import CAM_ROI

def get_ip_address():
    """Retrieve the IP address of the laptop."""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "Unavailable"

def clear_frame():
    """Clear all widgets from the root window."""
    for widget in root.winfo_children():
        widget.destroy()

def main_page():
    """Render the main page."""
    clear_frame()
    top_frame = tk.Frame(root, bg="lightgray")
    top_frame.pack(fill="x", pady=10)

    # Display IP address
    tk.Label(
        top_frame, 
        text=f"IP Address: {get_ip_address()}", 
        font=("Arial", 20), 
        bg="lightgray"
    ).pack(side="left", padx=10)

    # Content Frame
    content_frame = tk.Frame(root, bg="lightgray")
    content_frame.pack(expand=True)

    # Role buttons
    tk.Button(
        content_frame, 
        text="Operator", 
        font=("Arial", 25), 
        width=15, 
        command=operator_page, 
        bg="blue", 
        fg="white"
    ).pack(pady=20)

    tk.Button(
        content_frame, 
        text="Engineer", 
        font=("Arial", 25), 
        width=15, 
        command=engineer_page, 
        bg="green", 
        fg="white"
    ).pack(pady=20)

def operator_page():
    """Render the operator page."""
    clear_frame()
    tk.Label(root, text="Operator Page", font=("Arial", 30), bg="lightgray").pack(pady=50)
    tk.Button(root, text="Back", font=("Arial", 20), command=main_page, bg="gray", fg="white").pack()

def engineer_page():
    """Render the engineer page with login functionality."""
    clear_frame()
    tk.Label(root, text="Engineer Login", font=("Arial", 30), bg="lightgray").pack(pady=20)

    tk.Label(root, text="Username:", font=("Arial", 20), bg="lightgray").pack(pady=10)
    username_entry = tk.Entry(root, font=("Arial", 20))
    username_entry.pack(pady=5)

    tk.Label(root, text="Password:", font=("Arial", 20), bg="lightgray").pack(pady=10)
    password_entry = tk.Entry(root, font=("Arial", 20), show="*")
    password_entry.pack(pady=5)

    def login():
        username = username_entry.get()
        password = password_entry.get()
        if username == "admin" and password == "password":
            messagebox.showinfo("Login Successful", "Welcome, Engineer!")
            engineer_dashboard()  # Navigate to another page
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password!")

    tk.Button(root, text="Login", font=("Arial", 20), command=login, bg="blue", fg="white").pack(pady=20)
    tk.Button(root, text="Back", font=("Arial", 20), command=main_page, bg="gray", fg="white").pack(pady=10)

def engineer_dashboard():
    clear_frame()
    def access_camera(row_index):
        """Access the camera based on user input."""
        try:
            # Get Camera ID from Entry widget
            camera_id = int(rows[row_index][1].get())  # ID Entry widget
            # Get Camera Type from StringVar
            camera_type = rows[row_index][2].get()    # StringVar for camera type
            # Get Technique from StringVar
            technique = rows[row_index][3].get()      # StringVar for technique

            # Optional: Get file path if Object Detection is selected
            file_path = ""
            if technique == "Object Detection" and len(rows[row_index]) > 4:
                file_path = rows[row_index][4].get()  # Entry widget for file path
                print(f"File Path: {file_path}")

            # Example interaction
            if camera_type == "USB Camera":
                messagebox.showinfo("Success", f"Accessed USB Camera ID: {camera_id} using {technique}")
                CAM_ROI(camera_id)
            elif camera_type == "IP Address":
                messagebox.showinfo("Success", f"Accessed IP Camera at {camera_id} using {technique}")
            else:
                raise ValueError("Invalid camera type")

        except ValueError as ve:
            messagebox.showerror("Input Error", f"Invalid input: {ve}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to access camera: {str(e)}")


    def save_data():
        """Save all row data to a dictionary text file."""
        data = {}
        for row_index, row in enumerate(rows):
            camera_id = row[1].get()
            camera_type = row[2].get()
            technique = row[3].get()
            file_path = row[4].get() if len(row) > 4 else None

            data[f"ID_{row_index + 1}"] = {
                "Camera ID": camera_id,
                "Camera Type": camera_type,
                "Technique": technique,
                "File Path": file_path,
            }

        # Save to a text file
        with open("camera_data.txt", "w") as f:
            f.write(str(data))
        messagebox.showinfo("Data Saved", "Camera settings have been saved to 'camera_data.txt'")

    def add_row():
        """Add a new row of input widgets."""
        row = len(rows)

        # Create a container frame for the row
        row_frame = tk.Frame(settings_frame, bg="lavender", padx=5, pady=5, relief=tk.GROOVE, borderwidth=2)
        row_frame.grid(row=row, column=0, columnspan=5, pady=5, sticky="nsew")

        # Configure grid weights for dynamic resizing
        row_frame.grid_columnconfigure(0, weight=1)  # Row ID column
        row_frame.grid_columnconfigure(1, weight=2)  # ID entry column
        row_frame.grid_columnconfigure(2, weight=2)  # Camera type column
        row_frame.grid_columnconfigure(3, weight=2)  # Technique column
        row_frame.grid_columnconfigure(4, weight=3)  # File path column

        # Row ID Label
        row_id_label = tk.Label(row_frame, text=f"ID_{row + 1}", font=("Arial", 12), bg="lavender")
        row_id_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Camera ID Entry
        id_entry = tk.Entry(row_frame, font=("Arial", 12))
        id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Dropdown for USB Camera / IP Address
        camera_var = tk.StringVar(value="USB Camera")
        camera_menu = tk.OptionMenu(row_frame, camera_var, "USB Camera", "IP Address")
        camera_menu.config(font=("Arial", 12))
        camera_menu.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Dropdown for Technique Selection
        technique_var = tk.StringVar(value="Pose Estimation")
        technique_menu = tk.OptionMenu(row_frame, technique_var, "Pose Estimation", "Object Detection")
        technique_menu.config(font=("Arial", 12))
        technique_menu.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Optional File Path Entry
        file_path_entry = tk.Entry(row_frame, font=("Arial", 12), state=tk.DISABLED)
        file_path_entry.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        # Enable file path entry when Object Detection is selected
        def update_file_path(*args):
            if technique_var.get() == "Object Detection":
                file_path_entry.config(state=tk.NORMAL)
            else:
                file_path_entry.delete(0, tk.END)
                file_path_entry.config(state=tk.DISABLED)

        technique_var.trace_add("write", update_file_path)

        # Access Button
        access_button = tk.Button(
            row_frame,
            text="Access",
            font=("Arial", 12),
            bg="lightblue",
            activebackground="lightblue",
            command=lambda idx=row: access_camera(idx),
        )
        access_button.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")

        # Store widgets and variables for the row
        rows.append([row_frame, id_entry, camera_var, technique_var, file_path_entry])

    def remove_row():
        """Remove the last row of widgets."""
        if rows:
            # Retrieve the last row
            last_row = rows.pop()

            # Destroy all widget objects in the row
            for widget in last_row:
                if isinstance(widget, tk.Widget):  # For widgets like Entry, Label, OptionMenu, Button
                    widget.destroy()

    def create_layout():
        """Set up the overall layout of the dashboard."""
        global app_bg
        app_bg = root.cget("bg")
        root.configure(bg=app_bg)

        # Top Frame
        top_frame = tk.Frame(root, bg="lightgray")
        top_frame.pack(fill="x", pady=10)
        tk.Label(top_frame, text=f"IP Address: {get_ip_address()}", font=("Arial", 20), bg="lightgray").pack(side="left", padx=10)

        # Title Label
        tk.Label(root, text="Camera Setting", font=("Arial", 16, "bold"), fg="green", bg=app_bg).pack(pady=10)

        # Settings Frame
        global settings_frame
        settings_frame = tk.Frame(root, padx=20, pady=20, relief=tk.RIDGE, borderwidth=2, bg=app_bg)
        settings_frame.pack(fill="both", expand=True)

        # Configure grid for settings_frame
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(2, weight=1)
        settings_frame.grid_columnconfigure(3, weight=1)
        settings_frame.grid_columnconfigure(4, weight=1)

        # Add initial row
        global rows
        rows = []
        add_row()

        # Button Frame
        button_frame = tk.Frame(root, bg=app_bg)
        button_frame.pack(fill="x", pady=10)

        tk.Button(
            button_frame, text="+", font=("Arial", 14), bg=app_bg, activebackground=app_bg, command=add_row
        ).pack(side="left", padx=10, fill="x", expand=True)

        tk.Button(
            button_frame, text="-", font=("Arial", 14), bg=app_bg, activebackground=app_bg, command=remove_row
        ).pack(side="left", padx=10, fill="x", expand=True)

        tk.Button(
            button_frame, text="Save Data", font=("Arial", 14), bg="lightgreen", activebackground="lightgreen", command=save_data
        ).pack(side="left", padx=10, fill="x", expand=True)

    # Call create_layout when initializing the dashboard
    create_layout()


# Initialize the main window
root = tk.Tk()
root.title("Role-Based Navigation App")
root.geometry("1080x720")
root.configure(bg="lightgray")

# Start with the main page
main_page()

# Run the application
root.mainloop()