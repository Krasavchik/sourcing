import os
from sqlalchemy import create_engine, text

# Get your connection string from the environment variable
db_url = os.getenv("SUPABASE_DB_URL")
print("Using DB URL:", db_url)

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection successful! Result:", result.scalar())
except Exception as e:
    print("Connection failed:", e)