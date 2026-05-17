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
    
    print('Dropping all tables in agm_auth_db...')
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
    cursor.execute('SHOW TABLES;')
    tables = cursor.fetchall()
    for (table_name,) in tables:
        print(f'Dropping table {table_name}')
        cursor.execute(f'DROP TABLE IF EXISTS {table_name};')
    
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
    conn.commit()
    
    cursor.close()
    conn.close()
    print('Database wiped clean.')
except Exception as e:
    print(f'Error: {e}')
