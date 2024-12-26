import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import socket
from cam import CAM_ROI
import os, ast
import json
from app import ProductivityApp
import threading

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


# Inside the operator_page function
def operator_page():
    """Render the operator page."""
    clear_frame()

    # Define a function to run the Flask app in a separate thread
    def run_flask_app():
        local_ip = ProductivityApp().get_local_ip()
        app = ProductivityApp(host=local_ip, port=2102)
        app.run(use_reloader=False)  # Pass use_reloader to the inner Flask app's run

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # Render Operator Page UI
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

    def load_existing_data():
        """Load data from a JSON file and populate the rows."""
        file_path = "camera_data.json"
        if not os.path.exists(file_path):
            add_row()
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to load settings. File may be corrupted.")
            add_row()  # Ensure at least one row exists
            return

        # Populate rows with loaded data
        for row_index, (row_id, settings) in enumerate(data.items()):
            add_row()
            rows[row_index][1].set(settings.get("Camera ID", ""))
            rows[row_index][2].set(settings.get("Camera Type", "USB Camera"))
            rows[row_index][3].set(settings.get("Technique", "Pose Estimation"))

    def access_camera(row_index):
        """Access the camera based on user input."""
        try:
            camera_id = rows[row_index][1].get()
            camera_type = rows[row_index][2].get()
            technique = rows[row_index][3].get()

            if camera_type == "USB Camera":
                camera_id = int(camera_id)  # USB Cameras likely have integer IDs
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
        """Save all row data to a JSON file if it has changed."""
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

        file_path = "camera_data.json"

        # Check if data has changed
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    existing_data = json.load(f)
                    if existing_data == data:
                        print("Data is the same, no need to save.")
                        return
                except json.JSONDecodeError:
                    print("Error reading existing data. Overwriting file.")

        # Save data to file
        if data.get("ID_1", {}).get("Camera ID", ""):
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Data Saved", "Camera settings have been saved to 'camera_data.json'")

    def add_row():
        """Add a new row of input widgets."""
        row = len(rows)

        row_frame = tk.Frame(settings_frame, bg=app_bg, padx=5, pady=5, relief=tk.GROOVE, borderwidth=2)
        row_frame.grid(row=row, column=0, columnspan=5, pady=5, sticky="nsew")

        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=3)
        row_frame.grid_columnconfigure(3, weight=2)
        row_frame.grid_columnconfigure(4, weight=3)

        # Row ID
        row_id_label = tk.Label(row_frame, text=f"ID_{row + 1}", font=("Arial", 12), bg=app_bg)
        row_id_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Camera Type
        camera_var = tk.StringVar(value="USB Camera")
        camera_menu = tk.OptionMenu(row_frame, camera_var, "USB Camera", "IP Address")
        camera_menu.config(font=("Arial", 12), width=15)
        camera_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Camera ID (Default to USB Camera with dropdown)
        camera_id_var = tk.StringVar(value="0")
        camera_id_menu = tk.OptionMenu(row_frame, camera_id_var, *[str(i) for i in range(8)])
        camera_id_menu.config(font=("Arial", 12), width=15)
        camera_id_menu.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Technique
        technique_var = tk.StringVar(value="Person Detection")
        technique_menu = tk.OptionMenu(row_frame, technique_var, "Person Detection", "Pose Estimation", "Object Detection (Cam)", "Object Detection (Vid)", "Hand Skeleton")
        technique_menu.config(font=("Arial", 12), width=20)
        technique_menu.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # File Selection Button (make it larger)
        file_path_var = tk.StringVar()
        file_button = tk.Button(
            row_frame,
            text="Select File",
            font=("Arial", 12),  # Increased font size
            bg="lightblue",
            command=lambda: choose_file(file_path_var),
            state=tk.DISABLED,  # Initially disabled
        )
        file_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        # Enable/Disable File Button Based on Technique
        def update_file_button(*args):
            if "Object Detection" in technique_var.get():
                file_button.config(state=tk.NORMAL)
            else:
                file_button.config(state=tk.DISABLED)

        technique_var.trace_add("write", update_file_button)

        # Update Camera Type
        def update_camera_type(*args):
            if camera_var.get() == "IP Address":
                camera_id_var.set("")
                ip_address = simpledialog.askstring("Enter IP Address", "Please enter the IP Camera's address:")
                if ip_address:
                    camera_id_var.set(ip_address)
                else:
                    camera_var.set("USB Camera")  # Revert to USB Camera if no IP is provided
            else:
                camera_id_var.set("0")
                # Reinstate dropdown
                camera_id_menu = tk.OptionMenu(row_frame, camera_id_var, *[str(i) for i in range(8)])
                camera_id_menu.config(font=("Arial", 12), width=15)
                camera_id_menu.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        camera_var.trace_add("write", update_camera_type)

        # Add to the row frame
        access_button = tk.Button(
            row_frame,
            text="Access",
            font=("Arial", 12),
            bg="lightblue",
            command=lambda idx=row: access_camera(idx),  # Pass the current row index
        )
        access_button.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="nsew")

        # Append all widgets and variables for the row to the rows list
        rows.append([row_frame, camera_id_var, camera_var, technique_var, file_path_var, access_button])

    def choose_file(file_path_var):
        """Open a file selection dialog."""
        file_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("JSON Files", "*.json")],  # Add file types as needed
        )
        if file_path:
            file_path_var.set(file_path)

    def remove_row():
        """Remove the last row of widgets."""
        if rows:
            last_row = rows.pop()
            last_row[0].destroy()

    # Save Each Camera ROI in txt File
    def save_ROI():
        """Save all settings to a file and proceed to the next step."""
        # Define default values
        default_camera_type = "USB Camera"
        default_camera_id = "0"
        default_technique = "Person Detection"

        all_defaults = True  # Assume all rows are default initially

        for row in rows:
            camera_type = row[2].get()
            camera_id = row[1].get()
            technique = row[3].get()

            # Check if any value is not default
            if camera_type != default_camera_type or camera_id != default_camera_id or technique != default_technique:
                all_defaults = False
                break

        if all_defaults:
            print("All settings are default. Skipping save.")
            access_step()  # Skip saving and go to the next step
            return

        # Save data if not all rows are default
        save_data()
        access_step()  # Proceed to the next step


    def create_layout():
        """Set up the overall layout of the dashboard."""
        global app_bg
        app_bg = root.cget("bg")
        root.configure(bg=app_bg)

        # Top Frame
        top_frame = tk.Frame(root, bg="lightgray")
        top_frame.pack(fill="x", pady=10)

        # IP Address Label
        tk.Label(top_frame, text=f"IP Address: {get_ip_address()}", font=("Arial", 20), bg="lightgray").pack(side="left", padx=10)

        # Return Button
        return_button = tk.Button(
            top_frame, 
            text="Return", 
            font=("Arial", 14, "bold"), 
            bg="lightcoral", 
            activebackground="red", 
            command=main_page
        )
        return_button.pack(side="right", padx=10)

        # Create a Text widget for multi-colored title
        title = tk.Text(root, height=1, width=30, font=("Arial", 16, "bold"), bg=app_bg, bd=0, highlightthickness=0)
        title.tag_configure("black1", foreground="black", background="yellow")
        title.tag_configure("black", foreground="black")
        # Insert the text with tags for different colors
        title.insert("1.0", "| ", "black")
        title.insert("1.2", "Camera Setting", "black1")
        title.insert("1.17", " | ", "black")
        title.insert("1.19", "Step Setting", "black")
        title.insert("1.32", " |", "black")
        # Disable editing
        title.configure(state="disabled")
        title.pack(pady=10)

        # Settings Frame
        global settings_frame
        settings_frame = tk.Frame(root, padx=20, pady=20, relief=tk.FLAT, borderwidth=0, bg=app_bg)  # Flat frame without border
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
        load_existing_data()

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
            button_frame, text="Next", font=("Arial", 14), bg="lightyellow", activebackground="lightyellow", command=save_ROI
        ).pack(side="left", padx=10, fill="x", expand=True)


    # Call create_layout when initializing the dashboard
    create_layout()


    #*******************************************************#
    # Second Page
    # Load camera data from file (not using JSON)
    def load_camera_data():
        """
        Load camera data from camera_data.json file.
        Returns a dictionary of camera settings.
        """
        try:
            with open("camera_data.json", "r") as file:
                data = json.load(file)  # Parse JSON directly
            return data  # Return the parsed dictionary
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format in camera_data.json.")
            return {}


    def get_roi_cam_length(camera_id):
        """Retrieve the length of the ROI_CAM list."""
        filename = f"ROI_CAM_{camera_id}.txt"
        try:
            with open(filename, "r") as file:
                content = file.read()
            roi_var = content.split("=", 1)[1].strip()
            roi_list = ast.literal_eval(roi_var)
            return len(roi_list)
        except FileNotFoundError:
            messagebox.showerror("Error", f"{filename} not found.")
        except (ValueError, SyntaxError):
            messagebox.showerror("Error", f"Invalid format in {filename}.")
        return 0


    global camera_data
    # Transform data to lists
    camera_data = load_camera_data()
    camera_ids = list(camera_data.keys())
    camera_indexs = [camera_data[cid]["Camera ID"] for cid in camera_ids]
    camera_types = [camera_data[cid]["Camera Type"] for cid in camera_ids]
    techniques = [camera_data[cid]["Technique"] for cid in camera_ids]
    file_paths = [camera_data[cid]["File Path"] for cid in camera_ids]

    # Global variables
    global rows_1
    rows_1 = []


    def add_row_1():
        """Add a new row to the settings frame."""
        global rows_1
        row1 = []

        # Create a single sky-blue frame for the row
        row_frame = tk.Frame(settings_frame, bg="skyblue", relief=tk.RIDGE, borderwidth=2)
        row_frame.grid(row=len(rows_1), column=0, padx=5, pady=(5, 0), sticky="ew")

        # Configure settings_frame and row_frame to expand
        settings_frame.grid_columnconfigure(0, weight=1)  # Allow row_frame to stretch
        row_frame.grid_columnconfigure(0, weight=1)  # Step label
        row_frame.grid_columnconfigure(1, weight=2)  # Camera ID Dropdown
        row_frame.grid_columnconfigure(2, weight=2)  # ROI Dropdown
        row_frame.grid_columnconfigure(3, weight=2)  # Object Input
        row_frame.grid_columnconfigure(4, weight=4)  # Msg fields (✓ & X)

        # Step Label
        step_label = tk.Label(row_frame, text=f"Step {len(rows_1) + 1}:", font=("Arial", 12, "bold"), bg="skyblue")
        step_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        row1.append(row_frame)  # Keep frame for removal later
        row1.append(step_label)

        # Camera ID Dropdown
        cam_var = tk.StringVar(value="Select Camera")
        cam_dropdown = ttk.Combobox(row_frame, textvariable=cam_var, font=("Arial", 12), state="readonly")

        # Reload camera data dynamically
        global camera_data
        camera_data = load_camera_data()
        camera_indexs = [camera_data[cid]["Camera ID"] for cid in camera_ids]
        cam_dropdown['values'] = camera_indexs
        cam_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # ROI Dropdown (to be dynamically updated)
        roi_var = tk.StringVar(value="Select ROI")
        roi_dropdown = ttk.Combobox(row_frame, textvariable=roi_var, font=("Arial", 12))
        roi_dropdown.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        row1.append(roi_dropdown)

        # Update ROI dropdown based on Camera ID selection
        def update_roi_dropdown(event=None):
            selected_cam = cam_var.get()  # Get the selected camera
            if selected_cam:
                roi_length = get_roi_cam_length(selected_cam)  # Get ROI_CAM length
                roi_list = [f"ROI {i}" for i in range(1, roi_length + 1)]  # Generate ROI list
                roi_dropdown['values'] = roi_list  # Update dropdown values
                roi_var.set("Select ROI")  # Reset dropdown display
            else:
                roi_dropdown['values'] = []  # Clear values if no camera is selected


        cam_dropdown.bind("<<ComboboxSelected>>", update_roi_dropdown)

        # Object input
        obj_entry = tk.Entry(row_frame, font=("Arial", 12))
        obj_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        row1.append(obj_entry)

        # ✓ Msg Label and Text Box
        check_label = tk.Label(row_frame, text="✓ Msg:", font=("Arial", 12, "bold"), bg="skyblue")
        check_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        check_text = tk.Entry(row_frame, font=("Arial", 12))
        check_text.grid(row=1, column=1, columnspan=4, padx=5, pady=5, sticky="ew")
        row1.append(check_text)

        # X Msg Label and Text Box
        cancel_label = tk.Label(row_frame, text="X Msg:", font=("Arial", 12, "bold"), bg="skyblue")
        cancel_label.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="w")

        cancel_text = tk.Entry(row_frame, font=("Arial", 12))
        cancel_text.grid(row=2, column=1, columnspan=4, padx=5, pady=(0, 5), sticky="ew")
        row1.append(cancel_text)

        rows_1.append(row1)

        # Trigger canvas size update
        settings_frame.update_idletasks()


    def remove_row_1():
        """Remove the last row of widgets, leaving at least one."""
        global rows_1
        if len(rows_1) > 1:  # Ensure at least one row is left
            last_row = rows_1.pop()  # Remove the last row from the list
            last_row[0].destroy()  # Destroy the frame and its child widgets
        else:
            tk.messagebox.showinfo("Info", "At least one row must remain.")


    def save_settings():
        """Save the settings from all rows to a file only if valid data exists."""
        global rows_1
        settings_data = []

        for row in rows_1:
            try:
                # Ensure all fields have valid data
                if len(row) < 7:  # Ensure row has all expected widgets
                    continue

                camera_value = row[2].get().strip()
                roi_value = row[3].get().strip()
                object_value = row[4].get().strip()
                check_msg_value = row[5].get().strip()
                cancel_msg_value = row[6].get().strip()

                # Skip rows with empty critical fields (Camera, ROI, or Object)
                if not (camera_value or roi_value or object_value or check_msg_value or cancel_msg_value):
                    continue

                # Add row data to the list if it's valid
                row_data = {
                    "Camera": camera_value,
                    "ROI": roi_value,
                    "Object": object_value,
                    "Check Msg": check_msg_value,
                    "Cancel Msg": cancel_msg_value,
                }
                settings_data.append(row_data)
            except Exception as e:
                messagebox.showerror("Error", f"Error while reading row data: {e}")
                return

        # Check if settings_data is empty
        if not settings_data:
            return  # Skip saving process entirely

        # Save valid data to the JSON file
        try:
            with open("steps_data.json", "w") as file:
                json.dump(settings_data, file, indent=4)  # Pretty-print with indentation
            messagebox.showinfo("Success", "Steps have been saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")


    # From Access Step back to Main Page
    def return_main():
        save_settings()
        main_page()


    def return_camera():
        try:
            save_settings()  # Save settings before navigating
        except Exception as e:
            messagebox.showerror("Error", f"Error while saving settings: {e}")
        engineer_dashboard()  # Navigate to the camera page


    def access_step():
        clear_frame()
        global settings_frame
        global app_bg
        app_bg = root.cget("bg")
        root.configure(bg=app_bg)

        global camera_data
        camera_data = load_camera_data()

        # Top Frame
        top_frame = tk.Frame(root, bg="lightgray", relief=tk.FLAT, borderwidth=0)
        top_frame.pack(fill="x", pady=10)
        
        # IP Address Label
        tk.Label(top_frame, text=f"IP Address: {get_ip_address()}", font=("Arial", 20), bg="lightgray").pack(side="left", padx=10)

        # Return Button
        return_button = tk.Button(
            top_frame, 
            text="Return", 
            font=("Arial", 14, "bold"), 
            bg="lightcoral", 
            activebackground="red", 
            command=main_page
        )
        return_button.pack(side="right", padx=10)

        # Create a Text widget for multi-colored title
        title = tk.Text(root, height=1, width=30, font=("Arial", 16, "bold"), bg=app_bg, bd=0, highlightthickness=0)
        title.tag_configure("black1", foreground="black", background="yellow")
        title.tag_configure("black", foreground="black")
        # Insert the text with tags for different colors
        title.insert("1.0", "| ", "black")
        title.insert("1.2", "Camera Setting", "black")
        title.insert("1.17", " | ", "black")
        title.insert("1.19", "Step Setting", "black1")
        title.insert("1.32", " |", "black")
        # Disable editing
        title.configure(state="disabled")
        title.pack(pady=10)

        # Scrollable Settings Frame Setup
        settings_container = tk.Frame(root, bg="lightgray", relief=tk.FLAT, borderwidth=0)
        settings_container.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(settings_container, bg="lightgray", highlightthickness=0)  # Disable border highlight
        scroll_canvas.pack(side="left", fill="both", expand=True)

        # Add vertical scrollbar
        scrollbar = tk.Scrollbar(settings_container, orient="vertical", command=scroll_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure canvas to scroll with scrollbar
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scroll_canvas.bind(
            "<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        )

        # Frame inside Canvas for actual content
        settings_frame = tk.Frame(scroll_canvas, bg="lightgray", relief=tk.FLAT, borderwidth=0)  # Flat frame without border
        scroll_canvas.create_window((0, 0), window=settings_frame, anchor="nw")

        # Update scroll region whenever content changes
        def update_scroll_region():
            scroll_canvas.update_idletasks()  # Ensures the canvas updates before recalculating
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        # Initialize rows
        global rows_1
        rows_1 = []
        add_row_1()
        update_scroll_region()

        # Button Frame (outside the scrollable settings_frame)
        button_frame = tk.Frame(root, bg=app_bg, relief=tk.FLAT, borderwidth=0)
        button_frame.pack(fill="x", pady=10)

        tk.Button(
            button_frame, text="+", font=("Arial", 14), bg=app_bg, activebackground=app_bg, command=lambda: [add_row_1(), update_scroll_region()]
        ).pack(side="left", padx=10, fill="x", expand=True)

        tk.Button(
            button_frame, text="-", font=("Arial", 14), bg=app_bg, activebackground=app_bg, command=lambda: [remove_row_1(), update_scroll_region()]
        ).pack(side="left", padx=10, fill="x", expand=True)

        tk.Button(
            button_frame, text="Prev", font=("Arial", 14), bg="lightyellow", activebackground="lightyellow", command=return_camera
        ).pack(side="left", padx=10, fill="x", expand=True)


# Initialize the main window
root = tk.Tk()
root.title("Role-Based Navigation App")
root.geometry("1080x720")
root.configure(bg="lightgray")

# Start with the main page
main_page()

# Run the application
root.mainloop()