import os
import dropbox
import dropbox.files
import socket
from datetime import datetime
import json

class DropboxUploader:
    def __init__(self, token_file):
        # Load the JSON file
        with open(token_file, 'r') as file:
            data = json.load(file)

        # Initialize Dropbox client
        self.dbx = dropbox.Dropbox(data["access_token"])

        # Validate the access token
        try:
            self.dbx.users_get_current_account()
            print("Access token is valid.")
        except dropbox.exceptions.AuthError as e:
            raise ValueError(f"Invalid access token: {e}")

    def create_folder_if_not_exists(self, folder_path):
        try:
            self.dbx.files_get_metadata(folder_path)
            print(f"Folder exists: {folder_path}")
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path():
                try:
                    self.dbx.files_create_folder_v2(folder_path)
                    print(f"Folder created: {folder_path}")
                except Exception as create_error:
                    print(f"Error creating folder: {create_error}")
            else:
                print(f"Error checking folder: {e}")

    def upload_single_file(self, file_name):
        if os.path.isfile(file_name):
            today_date = datetime.now().strftime("%d_%m_%Y")
            folder_path = f"/FLEX/{today_date}"

            # Check if the folder exists or create it if it doesn't
            try:
                self.dbx.files_get_metadata(folder_path)
                print(f"Folder exists: {folder_path}")
            except dropbox.exceptions.ApiError as e:
                if isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path():
                    try:
                        self.dbx.files_create_folder_v2(folder_path)
                        print(f"Folder created: {folder_path}")
                    except Exception as create_error:
                        print(f"Error creating folder: {create_error}")
                else:
                    print(f"Error checking folder: {e}")

            # Upload the file to the folder
            with open(file_name, "rb") as f:
                data = f.read()
                try:
                    self.dbx.files_upload(data, f"{folder_path}/{os.path.basename(file_name)}", mode=dropbox.files.WriteMode("overwrite"))
                    print(f"Uploaded: {file_name} to {folder_path}")
                except Exception as upload_error:
                    print(f"Error uploading file: {upload_error}")
        else:
            print(f"File not found: {file_name}")


if __name__ == '__main__':
    # Initialize the uploader
    uploader = DropboxUploader(token_file="dropbox_tokens.json")
    
    # Specify the file to upload
    file_to_upload = "your_file.jpg"  # Replace with the actual file path
    uploader.upload_single_file(file_to_upload)
