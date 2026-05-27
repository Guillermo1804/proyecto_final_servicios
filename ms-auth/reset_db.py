import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=13307,
        user='root',
        password='root_password'
    )
    cursor = conn.cursor()
    print('Dropping and recreating agm_auth_db...')
    cursor.execute('DROP DATABASE IF EXISTS agm_auth_db;')
    cursor.execute('CREATE DATABASE agm_auth_db;')
    conn.commit()
    cursor.close()
    conn.close()
    print('Database agm_auth_db reset successfully.')
except Exception as e:
    print(f'Error: {e}')
