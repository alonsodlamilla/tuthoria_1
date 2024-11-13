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
        try:
            # Obtener credenciales desde variable de entorno
            google_creds = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
            if not google_creds:
                raise ValueError("No se encontraron las credenciales en GOOGLE_SHEETS_CREDENTIALS_FILE")
            
            # Crear archivo temporal con las credenciales
            credentials_path = '/tmp/google_credentials.json'
            with open(credentials_path, 'w') as f:
                f.write(google_creds)
            
            print(f"Credenciales temporales creadas en: {credentials_path}")
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                credentials_path,
                ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
            )
            
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open(os.getenv('GOOGLE_SHEETS_NAME')).sheet1
            
        except Exception as e:
            print(f"Error al cargar credenciales: {str(e)}")
            raise

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