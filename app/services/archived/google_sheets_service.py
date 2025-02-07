from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
from typing import Optional
from openai import OpenAI
import os
import json


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


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
    
def find_section_start(data, row_index):
    """
    Identifies the start of the section by locating the nearest header row before a given row.
    :param data: The full sheet data.
    :param row_index: The row index containing the date entry.
    :return: The row index of the corresponding header row.
    """
    while row_index > 0:
        row_index -= 1
        if "DATE" in data[row_index]:  # Look for the repeating section header
            return row_index
    return None  # Return None if no header is found


def find_best_matching_column(headers, query_metric):
    """
    Determines the best column for a given data type from a list of headers.

    :param headers: The list of column headers in the current section.
    :param data_type: The extracted data type from the command.
    :return: The column index if found, else None.
    """

    prompt = f"""
    You are an AI that maps user-provided metric names to spreadsheet column headers.

    Given the following column headers from a Google Sheet:
    {headers}

    Identify the **most relevant column** for the metric: "{query_metric}"

    Respond with a JSON object in this format:
    {{"matched_column: "COLUMNN_NAME_HERE", "confirmed" : true # true if the match is highly confident, false otherwise}}

    """

    response = client.chat.completions.create(
        model="gpt-4",  # Use GPT-4 for better reasoning
        messages=[{"role": "system", "content": "You are an AI assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0  # Ensure deterministic outputs
    )

    try:
        llm_response = json.loads(response.choices[0].message.content)
        matched_column = llm_response.get("matched_column", "").strip().lower().replace("\n", " ")
        confirmed = llm_response.get("confirmed", False)

        # If the LLM confirms the match, find the index
        if confirmed:
            headers_normalized = {header.lower().replace("\n", " ").strip(): i for i, header in enumerate(headers)}
            return headers_normalized.get(matched_column)
        return None  # No confirmed match found
    except json.JSONDecodeError:
        return None  # LLM response was invalid


    
def get_sheet_data(service, spreadsheet_id, range_name):
    """Retrieve all data from the Google Sheet."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        return result.get("values", [])
    except Exception as e:
        return None, {"status": "error", "message": str(e)}


def find_date_row(data):
    """Find the row containing today's date."""
    today = normalize_date(datetime.now().strftime("%a %d/%m/%y"))
    return next((i for i, row in enumerate(data) if len(row) > 2 and row[2] == today), None)


def get_update_values(headers, parameters):
    """Match each parameter to its corresponding column index."""
    update_values = {}
    for param_name, param_value in parameters.items():
        if param_value is not None:
            col_index = find_best_matching_column(headers, param_name)
            if col_index is not None:
                update_values[col_index] = param_value
    return update_values


def perform_batch_update(service, spreadsheet_id, range_name, update_values, date_row):
    """Perform batch updates for all matched parameters in Google Sheets."""
    update_requests = [
        {
            "range": f"{range_name.split('!')[0]}!{chr(65 + col_index)}{date_row + 1}",
            "values": [[value]]
        }
        for col_index, value in update_values.items()
    ]

    if not update_requests:
        return {"status": "error", "message": "No valid columns found for the provided parameters."}

    body = {"valueInputOption": "RAW", "data": update_requests}
    update_result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()

    return {"status": "success", "updated_cells": len(update_values)}


def google_sheets_service(weight, steps: Optional[int] = 0, cardio:  Optional[int] = 0, calories_consumed:  Optional[int] = 0, protein:  Optional[int] = 0):
    """Main function to update Google Sheets with provided values."""
    try:
        # Step 1: Retrieve sheet data
        data = get_sheet_data(service, SPREADSHEET_ID, RANGE_NAME)
        if not data:
            return {"status": "error", "message": "No data found in the sheet."}

        # Step 2: Identify the correct section by locating today's date
        date_row = find_date_row(data)
        if date_row is None:
            return {"status": "error", "message": "Could not locate today's date in the sheet."}

        # Step 3: Extract headers from the detected section
        section_start = find_section_start(data, date_row)
        if section_start is None:
            return {"status": "error", "message": "Could not identify the header row for this section."}

        headers = data[section_start]

        # Step 4: Construct update values based on provided parameters
        parameters = {
            "weight": weight,
            "steps": steps,
            "cardio": cardio,
            "calories_consumed": calories_consumed,
            "protein": protein,
        }
        update_values = get_update_values(headers, parameters)

        if not update_values:
            return {"status": "error", "message": "No valid columns found for the provided parameters."}

        # Step 5: Perform batch updates
        return perform_batch_update(service, SPREADSHEET_ID, RANGE_NAME, update_values, date_row)

    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON response from LLM."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
