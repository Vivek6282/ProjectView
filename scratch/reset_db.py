import os
import pymysql
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

url = os.environ.get('DATABASE_URL')
p = urlparse(url)

db_config = {
    'host': p.hostname,
    'user': p.username,
    'password': p.password,
    'port': p.port,
    'database': p.path[1:],
    'ssl': {'ssl_mode': 'REQUIRED'}
}

conn = pymysql.connect(**db_config)
try:
    with conn.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            print(f"Dropping table {table}...")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}` CASCADE;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    print("All tables dropped successfully.")
finally:
    conn.close()
