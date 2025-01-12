import dropbox.exceptions
from flask import Flask, render_template, request, redirect, url_for, Response, session, send_from_directory
from datetime import datetime, timedelta
import cv2
import os
import webbrowser
from threading import Timer
import numpy as np
import time
import dropbox
import json
from dropbox import DropboxOAuth2FlowNoRedirect
from product import Product
import threading

app = Flask(__name__)
app.secret_key = '1q2w3e4r5t6y7u8i9o0p1a2s3d4f5g6h7j8k9l0z1x2c3v4b5n6m'

# Initialize the production tracker
tracker = Product()

# Enable auto-reloading of templates
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'uploads' # Directory to store uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Dropbox configuration
APP_KEY = '0dk65hrsvki6x6n'
APP_SECRET = 'ulsinrwcjxqg0uq'
TOKEN_FILE = 'dropbox_tokens.json'

def save_tokens(access_token, refresh_token, expires_at):
    token_data = {
        'access_token':access_token,
        'refresh_token':refresh_token,
        'expires_at':expires_at.isoformat()
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def is_token_expired(expires_at):
    expires_at_dt = datetime.fromisoformat(expires_at)
    return datetime.now() >= expires_at_dt

def refresh_access_token(refresh_token):
    try:
        # Create a temporary Dropbox client to refresh the token
        dbx = dropbox.Dropbox(
            oauth2_refresh_token = refresh_token,
            app_key=APP_KEY,
            app_secret=APP_SECRET,
        )
        
        # Access the new token information
        new_access_token = dbx._oauth2_access_token # Get the refreshed access token
        expires_at = datetime.now() + timedelta(hours=4)
        save_tokens(new_access_token, refresh_token, expires_at)
        print("Token refreshed successfully!")

        return new_access_token
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

def get_valid_access_token():
    tokens = load_tokens()
    print(f"Loaded tokens: {tokens}")

    if tokens is None:
        # First-time setup
        auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type='offline')
        auth_url = auth_flow.start()
        print(f"\nPlease visit this URL to authorize the app: {auth_url}")
        print("\nAfter authorization, copy the authorization code and paste it below. ")
        auth_code = input("Enter the authorization code: ").strip()

        try:
            token_response = auth_flow.finish(auth_code)
            expires_at = datetime.now() + timedelta(hours=4)
            save_tokens(
                token_response.access_token,
                token_response.refresh_token,
                expires_at
            )
            return token_response.access_token
        except Exception as e:
            print(f"Error in authorization: {e}")
            return None

    if is_token_expired(tokens['expires_at']):
        print("Token is expired, attempting to refresh...")
        refreshed_token = refresh_access_token(tokens['refresh_token'])
        print(f"Refreshed token: {refreshed_token}")
        return refreshed_token
    
    print("Using existing token...")
    return tokens['access_token']

# Initialize Dropbox client
access_token = get_valid_access_token()
if access_token:
    dbx = dropbox.Dropbox(
        oauth2_access_token=access_token,
        oauth2_refresh_token=load_tokens().get('refresh_token'),
        app_key=APP_KEY,
        app_secret=APP_SECRET,
    )
    print("Dropbox client initialized successfully!")
else:
    raise Exception("Failed to initialize Dropbox client")

# Hardcoded credentials for demonstration
STAFF_CREDENTIALS = {
    "admin": "password123",
    "user1": "mypassword",
    "flex1": "flex1pass"
}

def ensure_folder_exists(folder_path):
    try:
        dbx.files_get_metadata(folder_path)
    except dropbox.exceptions.ApiError as e:
        if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path() and e.error.get_path().is_not_found():
            dbx.files_create_folder_v2(folder_path)
        else:
            raise

def get_or_create_shared_link(folder_path, file_name):
    try:
        # Check if a shared link already exists
        shared_links = dbx.sharing_list_shared_links(path=f"{folder_path}/{file_name}")
        if shared_links.links:
            # Return the first existing shared link
            return shared_links.links[0].url #.replace('?dl=0', '?raw=1') # Modify for direct image rendering
        
        # If no shared link exists, create a new one
        shared_link = dbx.sharing_create_shared_link_with_settings(f"{folder_path}/{file_name}")
        return shared_link.url
        #new_link = dbx.sharing_create_shared_link_with_settings(f"{folder_path}/{file_name}") 
        #return new_link.url.replace('?dl=0', '?raw=1') # Modify for direct image rendering
    except dropbox.exceptions.ApiError as e:
        print(f"Error retrieving or creating shared link for '{folder_path}/{file_name}' {e}")
        return None

# Ensure the FLEX folder exists
ensure_folder_exists('/FLEX')

def auto_refresh_token():
    """Function to periodically check and refresh the token"""
    while True:
        tokens = load_tokens()
        if tokens and is_token_expired(tokens['expires_at']):
            global dbx, access_token
            new_token = refresh_access_token(tokens['refresh_token'])
            if new_token:
                access_token = new_token
                dbx = dropbox.Dropbox(access_token)
        time.sleep(3600) # Check every hour

def upload_file_to_dropbox(local_file, dropbox_path, access_token):
    dbx = dropbox.Dropbox(access_token)
    try:
        with open(local_file, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"Uploaded {local_file} to {dropbox_path}")
    except Exception as e:
        print(f"Failed to upload file: {e}")

# Replace with your file and Dropbox details
local_file = "avg.txt"
dropbox_path = "/FLEX/avg.txt"
access_token = "your_dropbox_access_token"

upload_file_to_dropbox(local_file, dropbox_path, access_token)

def update_avg_file(completion_time):
    try:
        with open("avg.txt", "a") as file:
            file.write(f"{completion_time}\n")
        print(f"[DEBUG] Updated avg.txt with completion time: {completion_time}")
    except Exception as e:
        print(f"[ERROR] Error updating avg.txt: {e}")

def upload_avg_to_dropbox(dbx, folder_path='/FLEX'):
    file_path = "avg.txt"
    try:
        # Check if file exists locally
        if not os.path.exists(file_path):
            print(f"[ERROR] {file_path} does not exist.")
            return

        # Ensure the folder exists in Dropbox
        try:
            dbx.files_create_folder_v2(folder_path)
        except dropbox.exceptions.ApiError as e:
            if "conflict" in str(e):
                pass  # Folder already exists
            else:
                print(f"[ERROR] Unable to create folder {folder_path}: {e}")
                return

        # Upload the file
        with open(file_path, 'rb') as file:
            dbx.files_upload(
                file.read(),
                f"{folder_path}/{os.path.basename(file_path)}",
                mode=dropbox.files.WriteMode.overwrite
            )
        print(f"[DEBUG] Uploaded {file_path} to Dropbox successfully!")
    except dropbox.exceptions.ApiError as e:
        print(f"[ERROR] Dropbox API error: {e}")
    except Exception as e:
        print(f"[ERROR] General error while uploading {file_path}: {e}")
       
        

def calculate_average_from_dropbox_file(dbx, file_path):
    try:
        metadata, response = dbx.files_download(file_path)
        content = response.content.decode('utf-8')
        lines = content.splitlines()
        data = [float(line.strip()) for line in lines if line.strip().replace('.', '', 1).isdigit()]
        if not data:
            print("[DEBUG] avg.txt in Dropbox is empty or contains no valid numbers.")
            return 0
        avg_time = round(sum(data) / len(data), 2)
        return avg_time
    except dropbox.exceptions.ApiError as e:
        print(f"[ERROR] Unable to calculate average time from Dropbox: {e}")
        return 0
    
@app.route('/')
def index():
    return redirect(url_for('dashboard')) 

@app.route('/dashboard')
def dashboard():
    # Define the base folder for Dropbox
    base_folder = '/FLEX'
    avg_file_path = f"{base_folder}/avg.txt"
    ip_address = 192_168_43_229
    
    current_date = datetime.now().strftime('%d_%m_%Y')  # Current date for folder name
    date_folder_path = f"{base_folder}/{current_date}"

    # Fetch the number of images in the current date folder
    try:
        files = dbx.files_list_folder(date_folder_path).entries
        completed_products = len([
            file for file in files
            if isinstance(file, dropbox.files.FileMetadata) and file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ])
    except dropbox.exceptions.ApiError:
        # If folder doesn't exist, assume no completed products
        completed_products = 0
    except Exception as e:
        print(f"Error fetching files from Dropbox: {e}")
        completed_products = 0

    # Get daily stats
    stats = tracker.get_daily_stats(dbx, folder_path=base_folder)
    stats['completed'] = completed_products
    stats['remaining'] = max(0, stats['target'] - completed_products)

    # Ensure average time is calculated
    if 'avg_completion_time' not in stats or stats['avg_completion_time'] is None:
        stats['avg_completion_time'] = 0  # Default value if unavailable

    # Render the dashboard with stats
    return render_template('dashboard.html', stats=stats)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        password = request.form['password']
        if staff_id in STAFF_CREDENTIALS and STAFF_CREDENTIALS[staff_id] == password:
            session['logged_in'] = True
            return redirect(url_for('library'))
        else:
            return "Invalid Staff ID or Password", 403
    return render_template('login.html')

@app.route('/set-target', methods=['POST'])
def set_target():
    target = request.form.get('target', type=int)
    if target is not None:
        tracker.set_daily_target(target)
        return redirect(url_for('dashboard'))
    return "Invalid target value", 400

@app.route('/start-production', methods=['POST'])
def start_production():
    session['production_start_time'] = time.time()
    return redirect(url_for('dashboard'))

@app.route('/complete-production', methods=['POST'])
def complete_production():
    start_time = session.get('production_start_time')
    if start_time:
        completion_time = int(time.time() - start_time)
        product_type = request.form.get('product_type', 'default')
        operator_id = request.form.get('operator_id', 'unknown')

        tracker.record_completion(completion_time, product_type, operator_id)
        update_avg_file(completion_time)
        #session.pop('production_start_time', None)

        # Upload avg.txt to Dropbox
        try:
            tracker.upload_avg_to_dropbox(dbx, folder_path='/FLEX')
        except Exception as e:
            print(f"[ERROR] failed to upload avg.txt to Dropbox: {e}")

        session.pop('production_start_time', None)

    return redirect(url_for('dashboard'))

@app.route('/library', methods=['GET', 'POST'])
def library():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    # Define the base folder for Dropbox
    base_folder = '/FLEX'
    current_date = datetime.now().strftime('%d_%m_%Y')  # Current date for folder name
    date_folder_path = f"{base_folder}/{current_date}"  # Date-specific folder path

    # Ensure the folder for the current date exists in Dropbox
    try:
        try:
            dbx.files_list_folder(date_folder_path)
        except dropbox.exceptions.ApiError:
            dbx.files_create_folder_v2(date_folder_path)
            print(f"Created folder: {date_folder_path}")
    except Exception as e:
        print(f"Error ensuring folder exists: {e}")
        return {"error": "Failed to create folder"}, 500

    # Handle image upload
    if request.method == 'POST':
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file:
                try:
                    # Generate a new image name with a date and index
                    files = dbx.files_list_folder(date_folder_path).entries
                    index = len(files) + 1  # Increment index based on current files
                    new_file_name = f"{current_date}_{index}.jpg"  # Example: 12_01_2025_1.jpg

                    # Upload the image to the correct date folder
                    dbx.files_upload(
                        image_file.read(),
                        f"{date_folder_path}/{new_file_name}",
                        mode=dropbox.files.WriteMode.overwrite
                    )
                    print(f"Uploaded image as {new_file_name} to {date_folder_path}")
                    return redirect(url_for('library'))
                except Exception as e:
                    print(f"Error uploading image: {e}")
                    return {"error": "Failed to upload image"}, 500

    # Automatically move any stray images in /FLEX to their date folder
    try:
        base_files = dbx.files_list_folder(base_folder).entries
        for file in base_files:
            if isinstance(file, dropbox.files.FileMetadata) and file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                # Move the file to the current date folder
                source_path = f"{base_folder}/{file.name}"
                target_path = f"{date_folder_path}/{file.name}"
                dbx.files_move_v2(source_path, target_path)
                print(f"Moved {file.name} to {target_path}")
    except Exception as e:
        print(f"Error moving stray files to date folder: {e}")

    # Fetch all folders in the FLEX directory
    try:
        folders = dbx.files_list_folder(base_folder).entries
        date_folders = [
            {"name": folder.name, "path": folder.path_display}
            for folder in folders if isinstance(folder, dropbox.files.FolderMetadata)
        ]
    except Exception as e:
        print(f"Error retrieving folders: {e}")
        date_folders = []

    # If the user submits a search query
    query = request.args.get('query', '').strip().lower()
    if query:
        date_folders = [
            folder for folder in date_folders if query in folder["name"].lower()
        ]

    # Render the library page with the folders
    return render_template('library.html', date_folders=date_folders, query=query)


@app.route('/library/<folder_name>', methods=['GET'])
def view_folder(folder_name):
    folder_path = f'/FLEX/{folder_name}'
    try:
        # Fetch all files in the folder
        files = dbx.files_list_folder(folder_path).entries
        image_links = [
            {
                "name": file.name,
                "url": get_or_create_shared_link(folder_path, file.name)
            }
            for file in files if file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        print(f"Retrieved images: {image_links}")
    except Exception as e:
        print(f"Error retrieving images from folder '{folder_path}': {e}")
        image_links = []

    # Render the template to display images in the selected folder
    return render_template('images.html', image_links=image_links, folder_name=folder_name)


@app.route('/get_average_time', methods=['GET'])
def get_average_time():
    # Calculate the updated stats
    folder_path = '/FLEX'
    try:
       
        avg_completion_time = tracker.calculate_average_from_file("avg.txt")
        return {"average_time": avg_completion_time}, 200
    except Exception as e:
        print(f"Error fetching average time: {e}")
        return {"average_time": 0}, 500


@app.route('/library/<device_ip>/<date>', methods=['GET'])
def view_images_in_folder(device_ip, date):
    folder_path = f'/FLEX/{device_ip}/{date}'
    try:
        files = dbx.files_list_folder(folder_path).entries
        image_links = [
            {"name": file.name, "url": get_or_create_shared_link(folder_path, file.name)}
            for file in files if file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
    except Exception as e:
        image_links = []
        print(f"Error retrieving images: {e}")

    return render_template('images.html', image_links=image_links, folder_date=date)


@app.route('/FLEX/<device_ip>/<date>', methods=['GET'])
def get_images_by_date(device_ip, date):

    # Base folder for FLEX images
    folder_path = f'/FLEX/{device_ip}/{date}'

    try:
        # Ensure the folder exists in Dropbox
        try:
            files = dbx.files_list_folder(folder_path).entries
        except dropbox.exceptions.ApiError as e:
            return {"error": f"Folder '{folder_path}' not found."}, 404

        # Filter and collect image links
        image_links = [
            {"name": file.name, "url": get_or_create_shared_link(folder_path, file.name)}
            for file in files if file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]

        # If no images are found
        if not image_links:
            return {"message": f"No images found for {device_ip} on {date}"}, 200

        return {"images": image_links}, 200

    except Exception as e:
        print(f"Error retrieving images: {e}")
        return {"error": "An error occurred while processing your request."}, 500

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('dashboard'))

@app.route('/redirect-to-date')
def redirect_to_date():
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Dynamic IP and port based on date
    dynamic_ip = "192.168.31.187"
    dynamic_port = 2100 + int(today.split('-')[-1])

    # Redirect to the dynamic server
    return redirect(f"http://{dynamic_ip}:{dynamic_port}", code=302)

# Function to run the main server
def run_main_server():
    app.run(host="192.168.31.187", port=2100, debug=True)

# Function to create and run a dynamic server
def create_dynamic_server(ip, port, folder_name):
    dynamic_app = Flask(folder_name)

    @dynamic_app.route('/')
    def serve_date_folder():
        return f"Serving content for folder: {folder_name}."

    dynamic_app.run(host=ip, port=port, debug=True)
                   
# Open browser automatically after server starts
def open_browser():
    webbrowser.open_new("http://127.0.0.1:2102")

#print("Before starting Flask app")
if __name__ == '__main__':
      
      tracker = Product()
      tracker.set_daily_target(50)
      print("Daily target set to 50.")

       # Start token refresh thread
      from threading import Thread
      threading.Thread(target=run_main_server, daemon=True).start()

      refresh_thread = Thread(target=auto_refresh_token, daemon=True)
      refresh_thread.start()

      # Start the dynamic server for today's date
      today = datetime.now().strftime('%Y-%m-%d')
      dynamic_ip = "192.168.31.187"
      dynamic_port = 2100 + int(today.split('-')[-1])
      threading.Thread(
          target=create_dynamic_server,
          args=(dynamic_ip, dynamic_port, today),
          daemon=True
      ).start()

      print(f"Main server running on {dynamic_ip}:2100")
      print(f"Dynamic server running on {dynamic_ip}:{dynamic_port}")

 
      Timer(1, open_browser).start() # Open the browser after 1 second
      print("Starting Flask server...")

      # Replace '127.0.0.1' with your local IP address
      app.run(debug=True, host='0.0.0.0', port=2102) # 0.0.0.0 allows connections from any device
      print("Flask server started")




































































































































@app.route('/library', methods=['GET', 'POST'])
def library():

    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    # Simulated data for testing purposes
    image_links = [
        {"name": "example1.jpg", "link": "https://via.placeholder.com/200"},
        {"name": "example2.jpg", "link": "https://via.placeholder.com/200"},
    ]

    # Define the folder path

    folder_path = '/FLEX'

    if request.method == 'POST':
        if 'image_file' in request.files: 
            image_file = request.files['image_file']
            if image_file:
                # Upload the image to the specific Dropbox folder
                try:
                    dbx.files_upload(image_file.read(), f'{folder_path}/{image_file.filename}', mode=dropbox.files.WriteMode.overwrite)
                    return redirect(url_for('library'))
                except Exception as e:
                    return f"Error uploading to Dropbox: {e}"
                
    # Fetch files from the specific folder
    try:
        files = dbx.files_list_folder(folder_path).entries
        image_links = []
        for file in files:
            if isinstance(file, dropbox.files.FileMetadata) and file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif' )):
                link = get_or_create_shared_link(folder_path, file.name)
                if link:
                    image_links.append({'name': file.name, 'link': link})

        return render_template('library.html', image_links=image_links)
    except Exception as e:
        return f"Error retrieving files from Dropbox: {e}"
                                                                                                                          
@app.route('/capture-image')
def capture_image():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return "Camera not available", 500
  
    try:
        success, frame = camera.read()
        if success:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_filename = f"capture_{timestamp}.jpg"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"capture_{timestamp}.jpg")
            cv2.imwrite(image_path, frame)

            folder_path = '/FLEX'

            # Upload the image to Dropbox
            try:
                with open(image_path, "rb") as f:
                     dbx.files_upload(f.read(), f'{folder_path}/{image_filename}', mode=dropbox.files.WriteMode.overwrite)
                return redirect(url_for('dashboard'))
            except Exception as e:
                return f"Error uploading to Dropbox: {e}"
        else:
            return "Failed to capture image", 500 
    finally:
        camera.release()
  
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('dashboard'))
                   
# Open browser automatically after server starts
def open_browser():
    webbrowser.open_new("http://127.0.0.1:2102")

#print("Before starting Flask app")
if __name__ == '__main__':
      
      tracker = Product()
      tracker.set_daily_target(50)
      print("Daily target set to 50.")

       # Start token refresh thread
      from threading import Thread
      refresh_thread = Thread(target=auto_refresh_token, daemon=True)
      refresh_thread.start()
 
      Timer(1, open_browser).start() # Open the browser after 1 second
      print("Starting Flask server...")

      # Replace '127.0.0.1' with your local IP address
      app.run(debug=True, host='0.0.0.0', port=2102) # 0.0.0.0 allows connections from any device
      print("Flask server started")