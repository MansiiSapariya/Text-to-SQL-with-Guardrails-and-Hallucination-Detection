import urllib.request
import tempfile
import psycopg2
import os
from app.config import settings

def main():
    url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_PostgreSql.sql"
    print("Downloading Chinook database...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as temp_file:
        urllib.request.urlretrieve(url, temp_file.name)
        sql_file = temp_file.name
    
    print("Connecting to database...")
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if Artist table exists
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'Artist');")
    if cursor.fetchone()[0]:
        print("Database already seeded. Skipping.")
    else:
        print("Executing SQL script...")
        with open(sql_file, "r", encoding="utf-8") as f:
            sql = f.read()
            cursor.execute(sql)
        print("Database seeded successfully.")
    
    cursor.close()
    conn.close()
    os.remove(sql_file)

if __name__ == "__main__":
    main()
