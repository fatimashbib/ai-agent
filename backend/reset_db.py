import os
from database.session import Base, engine

# Delete old database files
db_path = "/app/db/ai-agent.db"  # or "./db/ai-agent.db" for relative path
for ext in ["", "-wal", "-shm"]:
    try:
        os.remove(f"{db_path}{ext}")
    except FileNotFoundError:
        pass

# Create new database
Base.metadata.create_all(engine)
print("✅ Database reset complete - fresh database created!")