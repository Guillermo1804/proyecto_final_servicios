import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Try connecting without password as well since access was denied with "root_password"
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root_password",
            database="agm_auth_db"
        )
    except mysql.connector.Error:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="agm_auth_db"
        )
        
    cursor = conn.cursor()
    cursor.execute("DELETE FROM django_migrations")
    conn.commit()
    print("Successfully deleted all rows from django_migrations table.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    if "conn" in locals() and conn.is_connected():
        cursor.close()
        conn.close()
