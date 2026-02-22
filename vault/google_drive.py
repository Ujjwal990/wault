"""
Google Drive integration using OAuth2 (user credentials).
Files are stored in YOUR Google account's Drive (15 GB free, forever).

One-time setup:
  1. Google Cloud Console → Credentials → Create OAuth2 "Desktop app" credentials
  2. Download JSON → save as client_secrets.json in project root
  3. Run locally: python generate_token.py
  4. Upload the generated token.json to PythonAnywhere ~/wault/token.json
"""

import os
import io
import mimetypes
from django.conf import settings

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_drive_service():
    if not DRIVE_AVAILABLE:
        raise RuntimeError("google-api-python-client not installed.")

    token_file = settings.GOOGLE_DRIVE_TOKEN_FILE
    if not os.path.exists(token_file):
        raise FileNotFoundError(
            f"token.json not found at {token_file}. "
            "Run generate_token.py on your local machine, then upload token.json to the server."
        )

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Auto-refresh if expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(token_file, 'w') as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("Token is invalid. Re-run generate_token.py and re-upload token.json.")

    return build('drive', 'v3', credentials=creds)


def get_or_create_subfolder(service, folder_name, parent_id):
    query = (
        f"name='{folder_name}' and "
        f"'{parent_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and "
        "trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    meta = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    folder = service.files().create(body=meta, fields='id').execute()
    return folder['id']


def upload_file(file_obj, filename, member_name, category_name):
    service = get_drive_service()
    root_id = settings.GOOGLE_DRIVE_FOLDER_ID

    member_folder_id = get_or_create_subfolder(service, member_name, root_id)
    cat_folder_id = get_or_create_subfolder(service, category_name, member_folder_id)

    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    file_obj.seek(0)
    content = file_obj.read()
    file_size = len(content)

    file_metadata = {'name': filename, 'parents': [cat_folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
    ).execute()

    file_id = uploaded.get('id')

    # Make viewable by anyone with the link
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
    ).execute()

    file_info = service.files().get(fileId=file_id, fields='id, webViewLink').execute()
    view_url = file_info.get('webViewLink', '')

    return file_id, view_url, file_size


def download_file(file_id):
    service = get_drive_service()
    file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()
    filename = file_info.get('name', 'document')
    mime_type = file_info.get('mimeType', 'application/octet-stream')

    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    buf.seek(0)
    return buf.read(), mime_type, filename


def delete_file(file_id):
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
