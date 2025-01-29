import re
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI

# Import relevant functionality
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

class GoogleSheetAgent:
    def __init__(self, service_account_file: str, spreadsheet_id: str, range_name: str):
        """
        Initialize the GoogleSheetAgent with API credentials and Google Sheet details.
        
        :param service_account_file: Path to the service account JSON file.
        :param spreadsheet_id: The ID of the target Google Sheet.
        :param range_name: The range in the Google Sheet where data will be updated.
        """
        self.service_account_file = service_account_file
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.service = self._get_google_sheets_service()

    def _get_google_sheets_service(self):
        """
        Set up the Google Sheets API client.
        """
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file(self.service_account_file, scopes=SCOPES)
        return build('sheets', 'v4', credentials=credentials)

    def _normalize_date(date_str):
        """
        Normalize a date string by removing leading zeros from the month.
        Example: 'Mon 13/05/24' -> 'Mon 13/5/24'
        """
        try:
            dt = datetime.strptime(date_str.strip(), '%a %d/%m/%y')
            return dt.strftime('%a %-d/%-m/%y')  # Remove leading zeros from day and month
        except ValueError:
            return None
    
    def update_sheet(self, weight: str):
        """
        Append the weight to the Google Sheet.
        
        :param weight: The weight value to update in the sheet.
        """
        values = [[weight]]
        body = {'values': values}
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return f"Updated Google Sheet with weight: {weight}" 

    @staticmethod
    def extract_weight(message: str) -> str:
        """
        Extract the weight value from the input message using regex.
        
        :param message: The user message containing the weight.
        :return: Extracted weight as a string or an error message if not found.
        """
        match = re.search(r'\b(\d+\.?\d*)\s?(kgs?|kilograms?)\b', message.lower())
        if match:
            return match.group(1)
        return "Could not find weight in the message."

    def create_agent(self):
        """
        Create a LangChain agent with tools for parsing and updating the Google Sheet.
        """
        
        parse_tool = Tool(
            name="Extract Weight",
            func=lambda message: self.extract_weight(message),
            description="Extracts weight from a message in kg."
        )

        update_sheet_tool = Tool(
            name="Update Google Sheet",
            func=lambda weight: self.update_sheet(weight),
            description="Updates the Google Sheet with the extracted weight."
        )

        llm = ChatOpenAI(model="gpt-4", temperature=0)
        tools = [parse_tool, update_sheet_tool]

        return initialize_agent(
            tools=tools,
            llm=llm,
            agent="zero-shot-react-description",
            verbose=True
        )

# Example Usage
if __name__ == "__main__":
    # Initialize the GoogleSheetAgent
    service_account_file = "path_to_your_service_account.json"
    spreadsheet_id = "your_spreadsheet_id"
    range_name = "Sheet1!A1:B1"

    agent_instance = GoogleSheetAgent(service_account_file, spreadsheet_id, range_name)
    agent = agent_instance.create_agent()

    # Example message
    message = "I recorded 92 kgs on the scales this morning."
    response = agent.run(message)
    print("Agent Response:", response)