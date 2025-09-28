#!/usr/bin/env python3
"""
image_publisher.py

Iterates subfolders that contain a non-empty "scaled" subfolder.
- Uploads all .zip files inside each "scaled" to Google Drive under /scaled/<FolderName>/
- Empties the local "scaled" folder (deletes all files, keeps folder)
- Makes the Drive folder public (link-anyone viewer)
- Creates a PDF with the share link: download-instructions-<FolderName>.pdf
- Uploads that PDF into the same Drive folder

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib reportlab fpdf

Auth files:
    google-drive-credentials.json  (OAuth client credentials - Desktop App)
    token.json                     (created automatically on first run)

Usage:
    python image_publisher.py
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple

# Google Drive API
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --------------------------- Config ---------------------------------

SCOPES = ['https://www.googleapis.com/auth/drive']  # full Drive access (simplest/reliable)
CREDENTIALS_FILE = 'google-drive-credentials.json'
TOKEN_FILE = 'token.json'

# Root path in Drive where we create folders; 'root' means My Drive root
DRIVE_ROOT_PARENT_ID = 'root'

# Directories to exclude when scanning for folders
EXCLUDED_DIRS = {'.git', 'venv'}

# Local scanning root (current directory)
LOCAL_ROOT = Path('.').resolve()

LOG_LEVEL = os.environ.get("IMG_PUBLISHER_LOG_LEVEL", "INFO").upper()

# --------------------------------------------------------------------


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format='[%(levelname)s] %(message)s'
    )


def get_drive_service() -> any:
    """
    Build and return an authenticated Drive API service.
    """
    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Refreshing Drive auth token…")
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Place your OAuth client secrets (Desktop App) here."
                )
            logging.info("Launching OAuth flow in your browser…")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next runs
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


def drive_find_folder(service, name: str, parent_id: str) -> Optional[str]:
    """
    Return the folder ID if a folder with `name` exists under `parent_id`, else None.
    """
    # Escape single quotes in folder name for Drive query
    safe_name = name.replace("'", "\\'")
    query = (
        f"name = '{safe_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and trashed = false"
    )
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=10
    ).execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None


def drive_ensure_folder(service, name: str, parent_id: str) -> str:
    """
    Ensure a folder named `name` exists under `parent_id`. Return folder ID.
    """
    folder_id = drive_find_folder(service, name, parent_id)
    if folder_id:
        return folder_id

    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    folder = service.files().create(body=file_metadata, fields='id, name').execute()
    logging.info(f"Created Drive folder: {name} (id={folder['id']})")
    return folder['id']


def drive_upload_file(service, local_path: Path, parent_id: str) -> str:
    """
    Upload a file to Drive under parent_id. Returns file ID.
    """
    media = MediaFileUpload(local_path.as_posix(), resumable=True)
    metadata = {
        'name': local_path.name,
        'parents': [parent_id]
    }
    created = service.files().create(
        body=metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    logging.info(f"Uploaded: {local_path.name} (id={created['id']})")
    return created['id']


def drive_make_public_and_get_link(service, folder_id: str) -> str:
    """
    Make the folder link-visible to anyone with the link and return webViewLink.
    """
    # Create (or add another) permission for 'anyone' reader.
    service.permissions().create(
        fileId=folder_id,
        body={'type': 'anyone', 'role': 'reader', 'allowFileDiscovery': False},
    ).execute()

    # Get the webViewLink
    meta = service.files().get(fileId=folder_id, fields='id, webViewLink').execute()
    link = meta.get('webViewLink')
    if not link:
        raise RuntimeError("Failed to obtain webViewLink for folder.")
    return link


def create_pdf(filepath: Path, link: str, folder_name: str) -> None:
    """
    Create a simple PDF with the download instructions.
    Tries reportlab first; falls back to fpdf.
    """
    text = (
        "Thank you for your order!\n"
        "Your files can be downloaded here:\n"
        f"{link}\n"
    )

    try:
        # Preferred: reportlab (high quality)
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        c = canvas.Canvas(filepath.as_posix(), pagesize=LETTER)
        width, height = LETTER
        x_margin = 1 * inch
        y = height - 1.5 * inch
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x_margin, y, "Thank you for your order!")
        y -= 0.5 * inch
        c.setFont("Helvetica", 12)
        c.drawString(x_margin, y, "Your files can be downloaded here:")
        y -= 0.3 * inch
        # Long links can overflow; draw as a text object to wrap crude lines
        text_obj = c.beginText(x_margin, y)
        text_obj.setFont("Helvetica", 12)
        for line in wrap_text(link, max_chars=92):
            text_obj.textLine(line)
        c.drawText(text_obj)
        c.showPage()
        c.save()
        return
    except Exception as e1:
        logging.debug(f"reportlab generation failed ({e1}); trying fpdf…")

    try:
        # Fallback: fpdf
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=18)
        pdf.cell(0, 12, txt="Thank you for your order!", ln=1)
        pdf.ln(2)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, txt="Your files can be downloaded here:", ln=1)
        # MultiCell to wrap the long URL
        pdf.multi_cell(0, 8, txt=link)
        pdf.output(filepath.as_posix())
        return
    except Exception as e2:
        raise RuntimeError(
            "Failed to create PDF. Please install 'reportlab' or 'fpdf'."
        ) from e2


def wrap_text(s: str, max_chars: int) -> List[str]:
    """
    Simple hard wrap without breaking the URL structure too aggressively.
    """
    lines = []
    buf = ""
    for ch in s:
        buf += ch
        if len(buf) >= max_chars and ch in "/?=&-_.":
            lines.append(buf)
            buf = ""
    if buf:
        lines.append(buf)
    return lines


def scan_candidate_folders(root: Path) -> List[Tuple[Path, Path]]:
    """
    Return a list of (folder, scaled_subfolder) for all immediate subfolders
    under root that contain a non-empty 'scaled' subfolder.
    """
    candidates: List[Tuple[Path, Path]] = []
    for entry in root.iterdir():
        if entry.is_dir() and entry.name not in EXCLUDED_DIRS:
            scaled = entry / 'scaled'
            if scaled.is_dir():
                # "not empty" => contains at least one file or folder entry
                try:
                    if any(scaled.iterdir()):
                        candidates.append((entry, scaled))
                except PermissionError:
                    logging.warning(f"Skipping (no access): {scaled}")
    return candidates


def delete_all_files_in_folder(folder: Path) -> None:
    """
    Delete all files directly inside `folder` (not recursive). Keep folder.
    """
    count = 0
    for p in folder.iterdir():
        if p.is_file():
            try:
                p.unlink()
                count += 1
            except Exception as e:
                logging.error(f"Failed to delete {p}: {e}")
    logging.info(f"Deleted {count} files in {folder}")


def process_folder(service, parent_folder: Path, scaled_folder: Path) -> None:
    """
    Process one folder:
      - Ensure /scaled/<FolderName>/ on Drive
      - Upload all .zip files from scaled
      - Delete all files from scaled
      - Make Drive folder public, get link
      - Create PDF and upload it
    """
    folder_name = parent_folder.name
    logging.info(f"=== Processing: {folder_name} ===")

    # Ensure Drive path: /scaled/<FolderName>/
    drive_scaled_id = drive_ensure_folder(service, 'scaled', DRIVE_ROOT_PARENT_ID)
    drive_target_id = drive_ensure_folder(service, folder_name, drive_scaled_id)

    # Upload all .zip files
    zip_files = [p for p in scaled_folder.iterdir() if p.is_file() and p.suffix.lower() == '.zip']
    if zip_files:
        logging.info(f"Uploading {len(zip_files)} .zip file(s) to /scaled/{folder_name}/ …")
        for z in zip_files:
            try:
                drive_upload_file(service, z, drive_target_id)
            except HttpError as e:
                logging.error(f"Drive upload failed for {z.name}: {e}")
    else:
        logging.info("No .zip files found to upload.")

    # Empty the local scaled folder (delete every file)
    delete_all_files_in_folder(scaled_folder)

    # Make the folder public & get the share link
    link = drive_make_public_and_get_link(service, drive_target_id)
    logging.info(f"Share link: {link}")

    # Create PDF locally
    pdf_name = f"download-instructions-{folder_name}.pdf"
    pdf_path = parent_folder / pdf_name
    try:
        create_pdf(pdf_path, link, folder_name)
        logging.info(f"Created PDF: {pdf_path}")
    except Exception as e:
        logging.error(f"Failed to create PDF for {folder_name}: {e}")
        return

    # Upload PDF to Drive folder
    try:
        drive_upload_file(service, pdf_path, drive_target_id)
        logging.info(f"Uploaded PDF to Drive: /scaled/{folder_name}/{pdf_name}")
    except HttpError as e:
        logging.error(f"Drive upload failed for PDF {pdf_name}: {e}")


def main() -> int:
    setup_logging()
    logging.info(f"Scanning in: {LOCAL_ROOT}")

    try:
        service = get_drive_service()
    except Exception as e:
        logging.error(f"Auth/Drive setup failed: {e}")
        return 1

    candidates = scan_candidate_folders(LOCAL_ROOT)
    if not candidates:
        logging.info("No folders with a non-empty 'scaled' subfolder were found. Nothing to do.")
        return 0

    for parent, scaled in candidates:
        try:
            process_folder(service, parent, scaled)
        except Exception as e:
            logging.error(f"Unexpected error processing {parent.name}: {e}")

    logging.info("All done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
