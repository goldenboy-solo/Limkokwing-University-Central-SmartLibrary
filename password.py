# set_passwords.py
from db import get_connection, hash_password

users_passwords = {
    "SOLOMON": "admin123",
    "SAIDU": "lib123",
    "JANE": "member123",
    "MIKE": "member123",
    "CHRISTIAN": "member123",
    "ALFRED": "member123",
    "ANDY": "member123",
    "AMAX": "member123",
    "SAJOR": "member123",
    "ABDUL": "member123"
}

conn = get_connection()
if conn:
    cur = conn.cursor()
    for username, pwd in users_passwords.items():
        cur.execute("UPDATE users SET password_hash = %s WHERE username = %s",
                    (hash_password(pwd), username))
    conn.commit()
    cur.close()
    conn.close()
    print("Passwords set.")
else:
    print("DB connection failed.")
