import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid
import time
import os
from dotenv import load_dotenv

load_dotenv()

class SheetsManager:
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Construir la ruta de manera dinámica
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(base_path, "openai-service", "credentials", "tuthoria-8d846ad64571.json")
        print(f"Intentando cargar credenciales desde: {credentials_path}")
        
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope)
        
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open(os.getenv('GOOGLE_SHEETS_NAME')).sheet1

    def log_conversation(self, user_id, role, message, message_type, 
                        tokens_used, response_time, model_version, 
                        conversation_id=None):
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        row = [
            conversation_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_id,
            role,
            message,
            message_type,
            tokens_used,
            response_time,
            model_version
        ]
        
        self.sheet.append_row(row)
        return conversation_id