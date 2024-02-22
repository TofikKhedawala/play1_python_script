from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from .config import *

def get_drive_link(file_path):
    drive_service = build('drive', 'v3', credentials=drive_credentials)
    folder_name = DRIVE_FILE_PATH
    folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folders = drive_service.files().list(q=folder_query).execute()
    if not folders.get('files'):
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        created_folder = drive_service.files().create(body=folder_metadata).execute()
        folder_id = created_folder.get('id')
    else:
        folder_id = folders['files'][0]['id']

    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id],
    }

    media = MediaFileUpload(file_path, mimetype='text/csv')
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    drive_service.permissions().create(
        fileId=uploaded_file['id'],
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    file_id = uploaded_file.get('id')
    shareable_link = f'https://drive.google.com/file/d/{file_id}/view?usp=sharing'

    return shareable_link

def delete_all_files_in_drive_folder(folder_name):

    drive_service = build('drive', 'v3', credentials=drive_credentials)
    folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folders = drive_service.files().list(q=folder_query).execute()

    if not folders.get('files'):
        print(f"Folder '{folder_name}' does not exist.")
        return None
    else:
        folder_id = folders['files'][0]['id']
        files_in_folder = drive_service.files().list(q=f"'{folder_id}' in parents").execute().get('files', [])
        print(f"Found {len(files_in_folder)} files in folder '{folder_name}':")

        for file in files_in_folder:
            try:
                print(f"Deleting file: {file['name']} (ID: {file['id']})")
                drive_service.files().delete(fileId=file['id']).execute()
                print(f"Deletion successful for file: {file['name']} (ID: {file['id']})")
            except Exception as e:
                print(f"Error deleting file: {file['name']} (ID: {file['id']}): {e}")

        return folder_id, len(files_in_folder)

# folder_name = "uploaded"
# result = delete_all_files_in_drive_folder(folder_name)
# print("Deletion result:", result)
