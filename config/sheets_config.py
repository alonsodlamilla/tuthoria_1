import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
SPREADSHEET_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'TuThorIA - Chat History Test')