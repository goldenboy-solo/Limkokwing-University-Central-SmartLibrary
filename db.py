# db.py
import psycopg2
from passlib.hash import pbkdf2_sha256
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="smartlibrary",
            user="postgres",
            password="solo@001",
            host="localhost",
            port="5432"
        )
        # ensure the SmartLibrary schema is first in search_path
        cur = conn.cursor()
        cur.execute("SET search_path TO SmartLibrary, public;")
        cur.close()
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None

def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)

def verify_password(password: str, hash_value: str) -> bool:
    try:
        return pbkdf2_sha256.verify(password, hash_value)
    except Exception:
        return False
