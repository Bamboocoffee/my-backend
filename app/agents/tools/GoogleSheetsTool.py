# 3rd Party Tools
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain_core.callbacks import (AsyncCallbackManagerForToolRun,CallbackManagerForToolRun)
from langchain_core.tools import BaseTool
from openai import OpenAI

# Helpers
from typing import Optional, Type, List
from pydantic import BaseModel, Field, root_validator
from datetime import datetime
import os
import json

class GoogleSheetsInput(BaseModel):
    """
    Defines the expected input schema for logging user health data into Google Sheets.
    
    Attributes:
        weight (float): The user's logged weight in kg.
        steps (float): The user's logged steps for the day.
        cardio (float): The user's logged calories burnt for the day.
        protein (float): The user's logged protein intake for the day.
        calories_consumed (float): The user's logged calorie intake for the day.
        sleep_duration (str): The total sleep duration for the user
        sleep_score (float): The user's logged sleep quality.
        HRV (float): The user's logged HRV.
    """
    weight: Optional[float] = Field(0, description="The user's logged weight in kg.")
    steps: Optional[float] = Field(0, description="The user's logged steps for the day.")
    cardio: Optional[float] = Field(0, description="The user's logged calories burnt for the day.")
    protein: Optional[float] = Field(0, description="The user's logged proteinn intake for the day.")
    calories_consumed: Optional[float] = Field(0, description="The user's logged calorie intake for the day.")
    sleep_duration: Optional[str] = Field("", description="The total sleep duration for the user.")
    sleep_score: Optional[float] = Field(0, description="The user's logged sleep quality.")
    HRV: Optional[float] = Field(0, description="The user's logged HRV.")
    
class CustomGoogleSheetsTool(BaseTool):
    """
    A custom LangChain tool for interacting with Google Sheets.

    This tool enables the logging of structured data (such as health metrics)
    into a Google Spreadsheet, leveraging the Google Sheets API.

    Attributes:
        name (str): Tool identifier name.
        description (str): Description of the tool’s purpose.
        args_schema (Type[BaseModel]): Defines the expected input format.
        return_direct (bool): Whether to return values directly from the tool.
        spreadsheet_id (str): Google Sheets spreadsheet ID.
        sheet_range (str): The range to be accessed in the sheet.
        service_account_file (str): Path to the service account JSON file.
        scopes (List[str]): Google API scopes required for access.
        credentials (Optional[Credentials]): OAuth credentials for API access.
        service (Optional[build]): Authenticated Google Sheets API service object.
    """

    name: str = "GoogleSheetsTool"
    description: str = "useful for when you want to input values into spreadsheets"
    args_schema: Type[BaseModel] = GoogleSheetsInput 
    return_direct: bool = True

    # TODO 
    # 1) Move these to user supplied for a more dynamic / modular tool
    # 2) Remove validation function call (onnly relevant for debugging) 
    spreadsheet_id: str = Field(description="The ID of the spreadsheet to edit")
    sheet_range: str = Field(description="The range that we will be analyzing in the sheet")
    service_account_file: str = Field(..., description="Path to the service account JSON file")
    scopes: List[str] = Field(default=["https://www.googleapis.com/auth/spreadsheets"], 
                              description="A list of Google API scopes")

    # Tool Configuration {Do not need to appear in Base Class Definitions as not User-Supplied}
    credentials: Optional[Credentials] = None 
    service: Optional[build] = None
    client: Optional[OpenAI] = None

    @root_validator(pre=True)
    def validate_required_fields(cls, values):
        """Ensures required fields are present before initialization."""
        if not values.get("service_account_file"):
            raise ValueError("service_account_file is required but missing WHY WHY WHY.")
        return values

    
    def __init__(self, service_account_file: str, spreadsheet_id: str, sheet_range: str, scopes: Optional[list] = None, **kwargs):
        """
        Initialize the tool with configurations.

        See these docs for settings: https://python.langchain.com/docs/how_to/custom_tools/#subclass-basetool

        :param service_account_file: Path to the service account JSON file.
        :param sheet_range: Range that will be considered on the sheet.
        :param spreadsheet_id: (Optional) Default spreadsheet ID to use.
        :param scopes: (Optional) Default scopes for Google Sheets API.
        """

        super().__init__(service_account_file=service_account_file, spreadsheet_id=spreadsheet_id, sheet_range=sheet_range, scopes=scopes, **kwargs)
        # Authenticate with Google Sheets API
        self.credentials = Credentials.from_service_account_file(self.service_account_file, scopes=self.scopes)
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    
    def _normalize_date(self, date_str: str)  -> str:
        """
        Normalize a date string by removing leading zeros from the month.

        Example: 
            >>> 'Mon 13/05/24' -> 'Mon 13/5/24'
        """
        try:
            dt = datetime.strptime(date_str.strip(), '%a %d/%m/%y')
            return dt.strftime('%a %-d/%-m/%y')  # Remove leading zeros from day and month
        except ValueError:
            return None
    
    
    def _find_section_start(self, data, row_index):
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


    def _find_best_matching_column(self, headers, query_metric):
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

        response = self.client.chat.completions.create(
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

    
    def _get_sheet_data(self, service, spreadsheet_id, range_name):
        """Retrieve all data from the Google Sheet."""
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get("values", [])
        except Exception as e:
            raise Exception("Error getting all the data from the sheet: " + e)


    def _find_date_row(self, data):
        """Find the row containing today's date."""
        today = self._normalize_date(datetime.now().strftime("%a %d/%m/%y"))
        return next((i for i, row in enumerate(data) if len(row) > 2 and row[2] == today), None)


    def _get_update_values(self, headers, parameters) -> dict:
        """Match each parameter to its corresponding column index."""
        update_values = {}
        try:
            for param_name, param_value in parameters.items():
                if param_value is not None and param_value != 0 and param_value != "0" and param_value != "":
                    param_value = str(param_value)  # Convert any value to string before processing
                    col_index = self._find_best_matching_column(headers, param_name)
                    if col_index is not None:
                        update_values[col_index] = param_value
            return update_values
        except Exception as e:
            raise Exception("Error matching the parameter to it's colum index: " + e)
    

    def _perform_batch_update(self, service, spreadsheet_id, range_name, update_values, date_row) -> str:
        """Perform batch updates for all matched parameters in Google Sheets."""
        try:
            update_requests = []
            for col_index, value in update_values.items():
                try:
                    num_value = float(value)  # Convert to float if possible
                    if num_value > 0:
                        value = num_value  # Keep as number if valid
                except ValueError:
                    pass  # Leave it as string if conversion fails

                update_requests.append({
                    "range": f"{range_name.split('!')[0]}!{chr(65 + col_index)}{date_row + 1}",
                    "values": [[f"'{value}"]]  # Ensure values are treated as text
                })
            if not update_requests:
                return {"status": "error", "message": "No valid columns found for the provided parameters."}

            body = {"valueInputOption": "USER_ENTERED", "data": update_requests}
            update_result = service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()
            return "Success"
        except Exception as e:
            raise Exception("Error performing the batch updated: " + str(e))
    
    def _run(self,
            weight: Optional[float] = 0, steps: Optional[float] = 0, cardio:  Optional[float] = 0, 
            calories_consumed:  Optional[float] = 0, protein:  Optional[float] = 0, sleep_duration:  Optional[str] = 0, 
            sleep_score:  Optional[float] = 0, HRV:  Optional[float] = 0,
            *kwargs) -> str:
        """
        Logs user health data into a Google Sheet by finding today's date and updating the corresponding row.

        Args:
            weight (float): User's weight in kg.
            steps (float): Number of steps walked.
            cardio (float): Calories burnt.
            protein (float): Protein intake in grams.
            calories_consumed (float): Total calories consumed.
            sleep_duration (str): the total sleep duration 
            sleep_score (float): the total sleep quality
            HRV (float): The HRV logged by the user
            **kwargs: Additional parameters (not used in this function).

        Returns:
            str: Success message with updated cell reference, or an error message if unsuccessful. 
        """

        try:
        # Step 1: Retrieve sheet data
            data = self._get_sheet_data(self.service, self.spreadsheet_id, self.sheet_range)
            if not data:
                return {"status": "error", "message": "No data found in the sheet."}

            # Step 2: Identify the correct section by locating today's date
            date_row = self._find_date_row(data)
            if date_row is None:
                return {"status": "error", "message": "Could not locate today's date in the sheet."}

            # Step 3: Extract headers from the detected section
            section_start = self._find_section_start(data, date_row)
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
                    "sleep_duration": sleep_duration, 
                    "sleep_score": sleep_score,
                    "HRV": HRV
            }

            update_values = self._get_update_values(headers, parameters)
            print("These are the updated values")
            print(update_values)
            if not update_values:
                return {"status": "error", "message": "No valid columns found for the provided parameters."}

            # Step 5: Perform batch updates
            updated_cells = self._perform_batch_update(self.service, self.spreadsheet_id, self.sheet_range, update_values, date_row)
            return f"Nice work Stephen, I've updated the following required cells. Anything else I can help you with?"
        except json.JSONDecodeError:
          return {"status": "error", "message": "Invalid JSON response from LLM."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    