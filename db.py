# db.py
import pyodbc
import logging

logger = logging.getLogger(__name__)

db_server = ""
db_port = ""
db_name = ""
db_user = ""
db_password = ""

def connect_to_db():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_server},{db_port};"
            f"DATABASE={db_name};"
            f"UID={db_user};"
            f"PWD={db_password};"
            f"TrustServerCertificate=yes;"
        )
        return conn
    except Exception:
        logger.exception("Ошибка при подключении к базе данных:")
        return None
