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
        """Registra un mensaje en la conversación"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        row = [
            conversation_id,
            timestamp,
            str(user_id),  # Asegurar que user_id sea string
            role,
            message,
            message_type,
            tokens_used,
            response_time,
            model_version
        ]
        
        try:
            self.sheet.append_row(row)
            logger.info(f"Mensaje registrado para usuario {user_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Error al registrar mensaje: {str(e)}")
            raise

    def get_conversation_history(self, user_id, limit=20):
        """Recupera los últimos mensajes de un usuario"""
        try:
            # Obtener todas las filas
            all_rows = self.sheet.get_all_records()
            
            # Filtrar por user_id
            user_messages = []
            for row in all_rows:
                if str(row.get('user_id', '')) == str(user_id):  # Convertir ambos a string para comparación
                    # Asegurarse de que tenga todos los campos necesarios
                    if all(key in row for key in ['timestamp', 'role', 'message']):
                        user_messages.append(row)
            
            # Ordenar por timestamp de forma ascendente (los más antiguos primero)
            user_messages.sort(key=lambda x: x['timestamp'])
            
            # Retornar los últimos 'limit' mensajes en orden cronológico
            return user_messages[-limit:]
            
        except Exception as e:
            logger.error(f"Error al recuperar historial: {str(e)}")
            return []