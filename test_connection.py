from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    # Create database engine
    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5}
    )

    # Test database connection
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    current_database() AS database,
                    current_user AS username,
                    inet_server_addr() AS server_ip,
                    inet_server_port() AS server_port
            """)
        )

        row = result.fetchone()

        print("SUCCESS: Connected to PostgreSQL!")
        print(f"Database: {row.database}")
        print(f"Username: {row.username}")
        print(f"Server IP: {row.server_ip}")
        print(f"Server Port: {row.server_port}")

except Exception as e:
    print("ERROR: Failed to connect to PostgreSQL!")
    print(f"Details: {e}")