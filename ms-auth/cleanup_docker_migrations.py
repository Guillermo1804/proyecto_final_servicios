import mysql.connector
from mysql.connector import Error

def cleanup():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=13307,
            database='agm_auth_db',
            user='root',
            password='root_password'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("TRUNCATE TABLE django_migrations;")
            connection.commit()
            print("Successfully truncated django_migrations table.")
            cursor.close()
            connection.close()
    except Error as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    cleanup()
