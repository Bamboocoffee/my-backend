from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Define your spreadsheet ID and range
SPREADSHEET_ID = '1Duy4XcvZzmk69HV4l0WPfoSO9UNbbtbX6IMMUOaZDQ4'  # Replace with your actual spreadsheet ID
RANGE_NAME = 'Daily Tracker!A1:Z11637'  # Specify the range to update (e.g., "Sheet1!A1:D5")

# Load service account credentials
SERVICE_ACCOUNT_FILE = 'google_service_account.json'  # Path to your JSON key file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
# Specifies the type of service version to use for the API
service = build('sheets', 'v4', credentials=credentials)


def normalize_date(date_str):
    """
    Normalize a date string by removing leading zeros from the month.
    Example: 'Mon 13/05/24' -> 'Mon 13/5/24'
    """
    try:
        dt = datetime.strptime(date_str.strip(), '%a %d/%m/%y')
        return dt.strftime('%a %-d/%-m/%y')  # Remove leading zeros from day and month
    except ValueError:
        return None


def google_sheets_service(weight):
    """
    Update the 'BODYWEIGHT (kg)' value for today's date in the correct week's block.
    :param spreadsheet_id: The ID of the spreadsheet.
    :param range_name: The range to search (e.g., 'Sheet1!A1:Z').
    :param weight: The weight value to update.
    :return: A dictionary with the status of the operation.
    """
    try:
        # Step 1: Retrieve all data from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        data = result.get('values', [])

        # Step 2: Get today's date normalized to match the sheet's format
        today = normalize_date(datetime.now().strftime('%a %d/%m/%y'))

        # Step 3: Find the row with today's date in the 3rd column and update the 4th column
        for i, row in enumerate(data):
            if len(row) > 2 and row[2] == today:  # Check if today's date matches in the 3rd column
                update_range = f"{RANGE_NAME.split('!')[0]}!D{i + 1}"  # D is the 4th column
                body = {"values": [[weight]]}

                # Update the weight in the 4th column
                update_result = service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=update_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                return update_result.get('updatedRange')
                # return {"status": "success", "message": update_result.get('updatedRange')}

        return {"status": "error", "message": "No row with today's date found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
