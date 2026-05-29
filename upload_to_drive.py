#!/usr/bin/env python3
"""Upload a large file to Google Drive using resumable upload."""

import os
import json
import sys
from pathlib import Path

# pip install google-auth google-auth-oauthlib google-api-python-client
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FILE_PATH = '/workspaces/CloudSurf/profiles.zip'
CLIENT_SECRET = 'client_secret.json'
TOKEN_FILE = 'token.json'

def get_credentials():
    creds = None

    # Try loading existing token
    if Path(TOKEN_FILE).exists():
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("No valid token found. Starting OAuth flow...")
            print("NOTE: In Codespaces, use --no-browser flow below.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            # Use this for headless/Codespaces environments:
            creds = flow.run_local_server(port=0)

        # Save the new token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    return creds

def upload_file(creds, file_path):
    service = build('drive', 'v3', credentials=creds)
    file_name = Path(file_path).name
    file_size = os.path.getsize(file_path)

    print(f"\nUploading: {file_name}")
    print(f"Size: {file_size / 1024 / 1024:.1f} MB")

    media = MediaFileUpload(
        file_path,
        mimetype='application/zip',
        resumable=True,          # Critical for large files
        chunksize=10 * 1024 * 1024  # 10MB chunks
    )

    request = service.files().create(
        body={'name': file_name},
        media_body=media,
        fields='id, name, size'
    )

    print("Starting upload...\n")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            uploaded_mb = (status.resumable_progress or 0) / 1024 / 1024
            print(f"\r  Progress: {pct}%  ({uploaded_mb:.0f} MB / {file_size/1024/1024:.0f} MB)", end='', flush=True)

    print(f"\n\n✅ Upload complete!")
    print(f"   File: {response['name']}")
    print(f"   Drive ID: {response['id']}")
    print(f"   Link: https://drive.google.com/file/d/{response['id']}/view")

if __name__ == '__main__':
    creds = get_credentials()
    upload_file(creds, FILE_PATH)
