from typing import Optional, Tuple, Dict
import os
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2.extras import DictCursor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DBService:
    def __init__(self):
        # PostgreSQL config
        self.pg_config = {
            "host": os.getenv("DB_HOST", "postgres"),
            "database": os.getenv("DB_NAME", "docente_bot"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "secret"),
        }

        # MongoDB config
        self.mongo_config = {
            "host": os.getenv("MONGO_HOST", "mongodb"),
            "port": int(os.getenv("MONGO_PORT", 27017)),
            "username": os.getenv("MONGO_USER", "admin"),
            "password": os.getenv("MONGO_PASSWORD", "secret123"),
        }

        # Validate configurations
        self._validate_config()

    def _validate_config(self):
        """Validate required environment variables"""
        required_vars = {
            "PostgreSQL": ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"],
            "MongoDB": ["MONGO_HOST", "MONGO_PORT", "MONGO_USER", "MONGO_PASSWORD"],
        }

        for service, vars in required_vars.items():
            missing = [var for var in vars if not os.getenv(var)]
            if missing:
                logger.warning(
                    f"Missing {service} environment variables: {', '.join(missing)}"
                )

    def get_pg_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.pg_config)
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise

    async def get_user_state(self, user_id: str) -> Tuple[str, Dict[str, str]]:
        """Get user state and context from PostgreSQL"""
        try:
            with self.get_pg_connection() as conn:
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
                            """
                            INSERT INTO user_states (user_id, current_state) 
                            VALUES (%s, 'INICIO') 
                            RETURNING current_state
                            """,
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
    ) -> None:
        """Update user state and context in PostgreSQL"""
        try:
            with self.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE user_states 
                        SET current_state = %s, 
                            anio = %s, 
                            curso = %s, 
                            seccion = %s
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

    async def log_conversation(self, user_id: str, message: str, response: str) -> None:
        """Log conversation to PostgreSQL history"""
        try:
            with self.get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO conversation_history 
                        (user_id, message, response, created_at) 
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        """,
                        (user_id, message, response),
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error in log_conversation: {str(e)}")
            raise
