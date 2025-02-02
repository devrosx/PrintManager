import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    """Authenticate and return the Google Drive API service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_and_convert_to_gdoc(service, file_path):
    """Upload a DOC/DOCX file and convert it to Google Docs format."""
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.google-apps.document'  # Convert to Google Docs format
    }
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"File '{file_name}' uploaded and converted to Google Docs with ID: {file.get('id')}")
    return file.get('id')

def export_gdoc_to_pdf(service, file_id, output_file_path):
    """Export a Google Docs file to PDF."""
    request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
    fh = io.FileIO(output_file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    print(f"File exported and saved as '{output_file_path}'")

def delete_file(service, file_id):
    """Delete a file from Google Drive."""
    service.files().delete(fileId=file_id).execute()
    print(f"File with ID '{file_id}' deleted from Google Drive.")

def convert_doc_to_pdf(doc_file_path):
    """Main function to convert a DOC/DOCX file to PDF."""
    # Authenticate and create Google Drive service
    service = authenticate_google_drive()

    # Upload the DOC/DOCX file and convert it to Google Docs format
    gdoc_id = upload_and_convert_to_gdoc(service, doc_file_path)

    # Generate the output PDF file name
    file_name = os.path.basename(doc_file_path)  # Get the input file name
    file_name_without_ext = os.path.splitext(file_name)[0]  # Remove the extension
    pdf_file_path = f"{file_name_without_ext}.pdf"  # Add .pdf extension

    # Export the Google Docs file to PDF
    export_gdoc_to_pdf(service, gdoc_id, pdf_file_path)

    # Delete the Google Docs file from Google Drive
    delete_file(service, gdoc_id)

    return pdf_file_path

if __name__ == '__main__':
    # Path to your DOC/DOCX file
    doc_file_path = 'example.docx'  # Replace with your file path

    # Convert the file to PDF
    pdf_file_path = convert_doc_to_pdf(doc_file_path)
    print(f"PDF saved at: {pdf_file_path}")