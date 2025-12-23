import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist."""
    # Parse database URL to extract connection details
    # Default: mysql+pymysql://root:password@localhost/MessengerDB
    db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:Jay%401524869@localhost/MessengerDB')
    
    try:
        if 'mysql+pymysql://' in db_url:
            # Simple parsing for the sake of this script
            # Assumes format: mysql+pymysql://user:pass@host/dbname or similar
            # A more robust solution would use sqlalchemy.engine.url.make_url
            
            from sqlalchemy.engine.url import make_url
            url = make_url(db_url)
            
            host = url.host or 'localhost'
            user = url.username or 'root'
            password = url.password or ''
            database = url.database
            port = url.port or 3306
            
            print(f"Connecting to MySQL at {host} as {user}...")
            
            # Connect without selecting a database
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                port=port,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with conn.cursor() as cursor:
                    # Check if database exists
                    cursor.execute(f"SHOW DATABASES LIKE '{database}'")
                    result = cursor.fetchone()
                    
                    if not result:
                        print(f"Database '{database}' does not exist. Creating...")
                        cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        print(f"Database '{database}' created successfully.")
                    else:
                        print(f"Database '{database}' already exists.")
            finally:
                conn.close()
                
        else:
            print("Not using MySQL configuration. Skipping database creation.")
            
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Please ensure your MySQL server is running and credentials are correct.")

if __name__ == "__main__":
    create_database()
