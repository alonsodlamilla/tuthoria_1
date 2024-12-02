from typing import Optional, Tuple, Dict
import os
import logging
import psycopg2
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)


class DBService:
    def __init__(self):
        self.db_config = {
            "host": os.environ.get("DB_HOST", "postgres"),
            "database": os.environ.get("DB_NAME", "docente_bot"),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", "secret"),
        }

    def get_connection(self):
        return psycopg2.connect(**self.db_config)

    async def get_user_state(self, user_id: str) -> Tuple[str, Dict[str, str]]:
        """Get user state and context"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute(
                        """
                        SELECT current_state, anio, curso, seccion 
                        FROM user_states 
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )
                    data = cur.fetchone()

                    if not data:
                        cur.execute(
                            "INSERT INTO user_states (user_id) VALUES (%s) RETURNING current_state",
                            (user_id,),
                        )
                        conn.commit()
                        return "INICIO", {}

                    return data["current_state"], {
                        "anio": data["anio"],
                        "curso": data["curso"],
                        "seccion": data["seccion"],
                    }
        except Exception as e:
            logger.error(f"Error in get_user_state: {str(e)}")
            raise

    async def update_user_state(
        self, user_id: str, state: str, context: Dict[str, str]
    ):
        """Update user state and context"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE user_states 
                        SET current_state = %s, anio = %s, curso = %s, seccion = %s
                        WHERE user_id = %s
                        """,
                        (
                            state,
                            context.get("anio"),
                            context.get("curso"),
                            context.get("seccion"),
                            user_id,
                        ),
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error in update_user_state: {str(e)}")
            raise

    async def log_conversation(self, user_id: str, message: str, response: str):
        """Log conversation to history"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO conversation_history (user_id, message, response)
                        VALUES (%s, %s, %s)
                        """,
                        (user_id, message, response),
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error in log_conversation: {str(e)}")
            raise
