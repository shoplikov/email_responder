import time
import base64
import google.generativeai as genai
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
spreadsheet_link = os.getenv("SPREADSHEET_LINK")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = os.getenv("RANGE_NAME")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === AUTH ===
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# === GOOGLE SERVICES ===
sheets_service = build("sheets", "v4", credentials=credentials)
gmail_service = build("gmail", "v1", credentials=credentials)

# === INIT GEMINI ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# === MEMORY to avoid duplicate replies ===
processed_emails = set()

def get_form_responses():
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get("values", [])
    return rows

def ask_gemini(question):
    response = model.generate_content(question)
    return response.text.strip()

def send_email_smtp(recipient, subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)


def main_loop():
    while True:
        print("Checking for new responses...")
        responses = get_form_responses()
        for row in responses:
            if len(row) < 3:
                continue  # skip incomplete rows

            timestamp, email, question = row
            if email in processed_emails:
                continue

            print(f"Processing question from {email}: {question}")
            try:
                answer = ask_gemini(question)
                send_email_smtp(email, "Your Answer from AI Assistant", answer)
                print(f"Sent answer to {email}")
                processed_emails.add(email)
            except Exception as e:
                print(f"Error processing {email}: {e}")

        time.sleep(10)

if __name__ == "__main__":
    main_loop()