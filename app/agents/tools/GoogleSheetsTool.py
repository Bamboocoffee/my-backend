# 3rd Party Tools
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain_core.callbacks import (AsyncCallbackManagerForToolRun,CallbackManagerForToolRun)
from langchain_core.tools import BaseTool

# Helpers
from typing import Optional, Type, List
from pydantic import BaseModel, Field, root_validator
from datetime import datetime

class GoogleSheetsInput(BaseModel):
    weight: float = Field(..., description="The user's logged weight in kg.")
    
class CustomGoogleSheetsTool(BaseTool):
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

    
    def _get_sheet_data(self, sheet_range: str) -> List[List[str]]:
        """
        Fetches data from a Google Sheet within the specified range.

        Args:
            sheet_range (str): The range in A1 notation.

        Returns:
            List[List[str]]: The sheet's data.
        """
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=sheet_range
        ).execute()
        return result.get('values', [])
    
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
    
    def _run(self,
             weight: float
    ) -> str:
        """
        ... 
        """
        
        try:
            # Step 1: Retrieve all data from the sheet
            data = self._get_sheet_data(self.sheet_range)
            # Step 2: Get today's date normalized to match the sheet's format
            today = self._normalize_date(datetime.now().strftime('%a %d/%m/%y'))
            # Step 3: Find the row with today's date in the 3rd column and update the 4th column
            for i, row in enumerate(data):
                if len(row) > 2 and row[2] == today:  # Check if today's date matches in the 3rd column
                    update_range = f"{self.sheet_range.split('!')[0]}!D{i + 1}"  # D is the 4th column
                    body = {"values": [[weight]]}

                    # Update the weight in the 4th column
                    update_result = self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    return {
                        "status": "success", 
                        "message": f"Successfully updated the following cell: {update_result.get('updatedRange')}"
                        }
            return {"status": "error", "message": "No row with today's date found."}
        except Exception as e:
                return {"status": "error", "message": str(e)}
    