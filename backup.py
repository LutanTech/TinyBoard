import os
import schedule
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
import shutil
from googleapiclient.http import MediaFileUpload

load_dotenv()

# Configs
DB_FILE = 'instance/main.db'
BACKUP_NAME = f"main_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")


def upload_to_gdrive():
    backup_name = f"main_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
    try:
        print(f"📦 Creating backup: {backup_name}")
        shutil.copy(DB_FILE, backup_name)

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        drive_service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': backup_name,
            'parents': [FOLDER_ID]
        }
        with open(backup_name, 'rb') as f:
            media = MediaFileUpload(f.name, mimetype='application/x-sqlite3')
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        send_email("✅ Backup Successful", f"Your DB backup `{backup_name}` was uploaded to Google Drive successfully.")
        print("✅ Backup and email sent successfully!")

        retries = 10
        while retries > 0:
            try:
                print(f"🧹 Trying to delete: {backup_name}")
                time.sleep(5)
                if os.path.exists(backup_name):
                    os.remove(backup_name)
                    print(f"🗑️ Deleted: {backup_name}")
                break
            except PermissionError:
                retries -= 1
                print(f"⚠️ Delete failed. Retrying... {retries} left")
                time.sleep(5)
                if retries == 0:
                    send_email(f"💥 Final fail: could not delete {backup_name}", "Error")

    except Exception as e:
        send_email("❌ DB Backup Failed", f"Something went wrong: {e}")
        print("Backup failed:", e)

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)


# 📆 Schedule at midnight
schedule.every().day.at("00:00").do(upload_to_gdrive)

if __name__ == "__main__":
    print("📅 Backup scheduler started... waiting for midnight...")
    while True:
        schedule.run_pending()
        time.sleep(60)
