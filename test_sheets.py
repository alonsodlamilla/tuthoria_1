import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.sheets_manager import SheetsManager
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        sheets = SheetsManager()
        sheets.log_conversation(
            user_id="test",
            role="system",
            message="Test de conexión"
        )
        print("¡Conexión exitosa!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 