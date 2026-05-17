import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=13307,
        user='root',
        password='root_password',
        database='agm_auth_db'
    )
    cursor = conn.cursor()
    
    print('Deleting from django_migrations...')
    cursor.execute('DELETE FROM django_migrations;')
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM django_migrations;')
    count = cursor.fetchone()[0]
    print(f'Remaining records in django_migrations: {count}')
    
    cursor.close()
    conn.close()
    print('Cleanup complete.')
except Exception as e:
    print(f'Error: {e}')
