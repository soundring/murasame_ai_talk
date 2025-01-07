from google.oauth2.service_account import Credentials
import gspread
from typing import List, Dict, Any

class GoogleSheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_name: str):
        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        self.gc = gspread.authorize(credentials)
        self.spreadsheet = self.gc.open(spreadsheet_name)
        
    def get_worksheet(self, index: int):
        return self.spreadsheet.get_worksheet(index)
        
    def append_row(self, worksheet_index: int, row_data: List[Any]):
        worksheet = self.get_worksheet(worksheet_index)
        worksheet.append_row(row_data)
        
    def get_all_values(self, worksheet_index: int) -> List[List[str]]:
        worksheet = self.get_worksheet(worksheet_index)
        return worksheet.get_all_values()
        
    def get_cell_value(self, worksheet_index: int, cell: str) -> str:
        worksheet = self.get_worksheet(worksheet_index)
        return worksheet.get(cell)[0][0]