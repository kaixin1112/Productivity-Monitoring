import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import socket
from cam import CAM_ROI
import os, ast
import json
import cv2
from deepface import DeepFace
from PIL import Image, ImageTk
import subprocess

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

# Create a directory to store registered user images
if not os.path.exists("registered_users"):
    os.makedirs("registered_users")

def run_script_thread():
    import threading
    def run_script():
        # Use subprocess to chain commands in CMD
        cmd = "D: && cd D:/Ching/Documents/Demo/Productivity-Monitoring && python finally.py"
        subprocess.run(cmd, shell=True)
    threading.Thread(target=run_script).start()

# Dummy database for storing user IDs and their image file paths
database = {}

# Load registered users into the database
def load_registered_users():
    for file_name in os.listdir("registered_users"):
        if file_name.endswith(".jpg"):
            user_id = file_name.split(".")[0]
            database[user_id] = os.path.join("registered_users", file_name)

load_registered_users()

def add_user(user_id, frame):
    # Save the user's picture
    file_path = os.path.join("registered_users", f"{user_id}.jpg")
    cv2.imwrite(file_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    database[user_id] = file_path

def authorize_and_register(user_id_entry, cap):
    auth_window = tk.Toplevel(root)
    auth_window.title("Authorization")
    auth_window.geometry("400x200")

    tk.Label(auth_window, text="Enter Username:", font=("Arial", 15)).pack(pady=5)
    username_entry = tk.Entry(auth_window, font=("Arial", 15))
    username_entry.pack(pady=5)

    tk.Label(auth_window, text="Enter Password:", font=("Arial", 15)).pack(pady=5)
    password_entry = tk.Entry(auth_window, font=("Arial", 15), show="*")
    password_entry.pack(pady=5)

    def verify_credentials():
        username = username_entry.get()
        password = password_entry.get()
        if username == "admin" and password == "password":  # Replace with secure authentication
            auth_window.destroy()
            capture_and_register(user_id_entry, cap)
        else:
            messagebox.showerror("Error", "Invalid credentials.")

    tk.Button(auth_window, text="Submit", font=("Arial", 15), command=verify_credentials).pack(pady=10)

def capture_and_register(user_id_entry, cap):
    user_id = user_id_entry.get()
    if not user_id:
        messagebox.showerror("Error", "Please enter a User ID.")
        return

    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "Failed to capture frame from camera.")
        return

    frame = cv2.flip(frame, 1)  # Flip the frame horizontally
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    add_user(user_id, rgb_frame)
    messagebox.showinfo("Success", f"User {user_id} registered successfully.")

def capture_and_login(user_id_entry, cap):
    user_id = user_id_entry.get()
    if not user_id:
        messagebox.showerror("Error", "Please enter a User ID.")
        return

    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "Failed to capture frame from camera.")
        return

    frame = cv2.flip(frame, 1)  # Flip the frame horizontally
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    if user_id in database:
        file_path = database[user_id]
        result = DeepFace.verify(img1_path=file_path, img2_path=rgb_frame, enforce_detection=False)
        if result["verified"]:
            cap.release()
            clear_frame()
            tk.Label(root, text=f"Login Successful: {user_id}", font=("Arial", 30), bg="lightgreen").pack(pady=20)

            # Close application after 3 seconds and run the script
            def close_and_run():
                root.quit()  # Stops the Tkinter event loop
                root.destroy()  # Closes the Tkinter window
                run_script_thread()

            root.after(3000, close_and_run)
            return

    cap.release()
    clear_frame()
    tk.Label(root, text=f"Invalid User: {user_id}", font=("Arial", 30), bg="lightcoral").pack(pady=20)
    tk.Button(root, text="Return to Main Page", font=("Arial", 20), command=main_page, bg="gray", fg="white").pack(pady=20)

def update_video_frame(video_label, cap):
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
    video_label.after(10, update_video_frame, video_label, cap)

def operator_page():
    clear_frame()

    tk.Label(root, text="Operator Page", font=("Arial", 30), bg="lightgray").pack(pady=10)

    frame = tk.Frame(root)
    frame.pack(pady=10)

    tk.Label(frame, text="User ID: ", font=("Arial", 15)).grid(row=0, column=0, padx=5)
    user_id_entry = tk.Entry(frame, font=("Arial", 15))
    user_id_entry.grid(row=0, column=1, padx=5)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    video_label = tk.Label(root)
    video_label.pack(pady=20)

    update_video_frame(video_label, cap)

    tk.Button(frame, text="Register", font=("Arial", 15), command=lambda: authorize_and_register(user_id_entry, cap)).grid(row=0, column=2, padx=5)
    tk.Button(frame, text="Login", font=("Arial", 15), command=lambda: capture_and_login(user_id_entry, cap)).grid(row=0, column=3, padx=5)

    def on_closing():
        cap.release()
        cv2.destroyAllWindows()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    tk.Button(root, text="Back", font=("Arial", 20), command=lambda: [cap.release(), main_page()], bg="gray", fg="white").pack(pady=20)


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
            camera_id = str(settings.get("Camera ID", "0"))  # Ensure Camera ID is a string
            camera_type = settings.get("Camera Type", "USB Camera")
            technique = settings.get("Technique", "Pose Estimation")

            # Set the Camera Type, Camera ID, and Technique
            rows[row_index][2].set(camera_type)  # Set Camera Type
            rows[row_index][3].set(technique)   # Set Technique

            # Make sure the camera_id is correctly set in the OptionMenu
            camera_id_var = rows[row_index][1]
            camera_id_var.set(camera_id)  # Set the Camera ID to the correct value

            # Get the camera_id_menu (which is the OptionMenu)
            camera_id_menu = rows[row_index][6]
            menu = camera_id_menu["menu"]
            
            # Update the camera_id_menu based on camera type
            if camera_type == "USB Camera":
                # Update the camera_id_menu with camera IDs from 0 to 7 (or whatever range you want)
                menu.delete(0, "end")  # Clear previous options
                for i in range(8):  # Set camera ID options
                    menu.add_command(label=str(i), command=lambda value=str(i): camera_id_var.set(value))
            elif camera_type == "IP Address":
                # Set an IP address value (you might want to handle this differently)
                camera_id_var.set(settings.get("Camera ID", ""))


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

    def add_row():
        """Add a new row of input widgets, limited to 3 rows."""
        row = len(rows)

        if len(rows) >= 3:
            messagebox.showwarning("Limit Reached", "You can only add up to 3 rows.")
            return

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

        # Camera ID (Initially set to 0, will be updated dynamically)
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
        rows.append([row_frame, camera_id_var, camera_var, technique_var, file_path_var, access_button, camera_id_menu])


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


    def load_steps_data():
        """Load steps data from steps_data.json and populate the rows."""
        global rows_1
        try:
            with open("steps_data.json", "r") as file:
                steps_data = json.load(file)  # Load JSON data
                print(f"Loaded steps data: {steps_data}")  # Debugging

            # Clear any existing rows
            for row in rows_1:
                row[0].destroy()  # Destroy the frame and its widgets
            rows_1.clear()

            # Populate rows with data
            for step in steps_data:
                add_row_1()  # Add a new empty row
                row = rows_1[-1]  # Get the last row added

                # Populate each input field with data
                row[1].set(step.get("Camera", ""))  # Camera Dropdown
                row[2].set(step.get("ROI", ""))     # ROI Dropdown
                row[3].insert(0, step.get("Object", ""))  # Object Input

        except FileNotFoundError:
            print("steps_data.json not found. Skipping load.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format in steps_data.json.")
        except Exception as e:
            messagebox.showerror("Error", f"Error while loading steps data: {e}")


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
        """Add a new row to the settings frame with a more systematic layout and longer text boxes for ✓ and X Msg."""
        global rows_1
        row1 = []

        # Create a single sky-blue frame for the row
        row_frame = tk.Frame(settings_frame, bg="skyblue", relief=tk.RIDGE, borderwidth=2)
        row_frame.grid(row=len(rows_1), column=0, padx=5, pady=(5, 0), sticky="ew")

        # Configure settings_frame and row_frame to expand
        settings_frame.grid_columnconfigure(0, weight=1)  # Allow row_frame to stretch
        row_frame.grid_columnconfigure(0, weight=1)  # Step label
        row_frame.grid_columnconfigure(1, weight=1)  # Labels
        row_frame.grid_columnconfigure(2, weight=2)  # Input fields
        row_frame.grid_columnconfigure(3, weight=1)  # Labels
        row_frame.grid_columnconfigure(4, weight=4)  # Input fields (longer ✓ and X Msg)

        # Step Label
        step_label = tk.Label(row_frame, text=f"Step {len(rows_1) + 1}:", font=("Arial", 12, "bold"), bg="skyblue")
        step_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        row1.append(row_frame)  # Keep frame for removal later

        # Camera ID Dropdown
        tk.Label(row_frame, text="Camera:", font=("Arial", 12, "bold"), bg="skyblue").grid(row=0, column=1, sticky="e")
        cam_var = tk.StringVar(value="Select Camera")
        cam_dropdown = ttk.Combobox(row_frame, textvariable=cam_var, font=("Arial", 12), state="readonly")
        cam_dropdown.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        row1.append(cam_var)

        # Reload camera data dynamically
        global camera_data
        camera_data = load_camera_data()
        camera_indexs = [camera_data[cid]["Camera ID"] for cid in camera_data.keys()]  # Get camera IDs from JSON
        cam_dropdown['values'] = camera_indexs  # Populate dropdown with camera IDs

        # ROI Dropdown
        tk.Label(row_frame, text="ROI:", font=("Arial", 12, "bold"), bg="skyblue").grid(row=0, column=3, sticky="e")
        roi_var = tk.StringVar(value="Select ROI")
        roi_dropdown = ttk.Combobox(row_frame, textvariable=roi_var, font=("Arial", 12), state="readonly")
        roi_dropdown.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        row1.append(roi_var)

        # Update ROI dropdown based on Camera ID selection
        def update_roi_dropdown(event=None):
            selected_cam = cam_var.get()  # Get the selected camera ID
            if selected_cam:
                # Try loading ROI_CAM_<index>.txt
                roi_filename = f"ROI_CAM_{selected_cam}.txt"
                try:
                    roi_length = get_roi_cam_length(selected_cam)  # Retrieve the length of ROI_CAM list
                    roi_list = [f"ROI {i}" for i in range(1, roi_length + 1)]  # Generate ROI options
                    roi_dropdown['values'] = roi_list  # Update dropdown values
                    roi_var.set("Select ROI")  # Reset dropdown display
                except FileNotFoundError:
                    print(f"{roi_filename} not found. Leaving ROI dropdown blank.")
                    roi_dropdown['values'] = []  # Leave blank if file is not found
                    roi_var.set("Select ROI")
                except Exception as e:
                    print(f"Error reading {roi_filename}: {e}")
                    roi_dropdown['values'] = []  # Handle unexpected errors
                    roi_var.set("Select ROI")
            else:
                roi_dropdown['values'] = []  # Clear values if no camera is selected
                roi_var.set("Select ROI")

        # Bind the selection event to update ROI dropdown
        cam_dropdown.bind("<<ComboboxSelected>>", update_roi_dropdown)

        # Object Input
        tk.Label(row_frame, text="Object:", font=("Arial", 12, "bold"), bg="skyblue").grid(row=1, column=1, sticky="e")
        obj_entry = tk.Entry(row_frame, font=("Arial", 12))
        obj_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        row1.append(obj_entry)

        # Append the row to rows_1
        rows_1.append(row1)

        # Trigger canvas size update
        settings_frame.update_idletasks()
        print(f"Row {len(rows_1)} added: {row1}")  # Debugging



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

        for idx, row in enumerate(rows_1):
            try:
                # Debug: Print row structure
                print(f"Row {idx + 1} structure: {row}")

                # Retrieve widget values
                camera_value = row[1].get().strip()  # Camera Dropdown Variable
                roi_value = row[2].get().strip()     # ROI Dropdown Variable
                object_value = row[3].get().strip()  # Object Input

                # Debug collected values
                print(f"Row {idx + 1} collected values:")
                print(f"Camera: {camera_value}, ROI: {roi_value}, Object: {object_value}")

                # Append valid row data
                row_data = {
                    "Camera": camera_value,
                    "ROI": roi_value,
                    "Object": object_value
                }
                settings_data.append(row_data)
            except Exception as e:
                messagebox.showerror("Error", f"Error while processing row {idx + 1}: {e}")
                return

        # Save data to JSON if valid rows exist
        if settings_data:
            try:
                with open("steps_data.json", "w") as file:
                    json.dump(settings_data, file, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Error saving settings: {e}")
        else:
            print("No valid data to save!")
            messagebox.showwarning("No Data", "No valid data to save!")


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
            command=return_main
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
        load_steps_data()
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
