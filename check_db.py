# Create a quick check_db.py script
import sqlite3
import os

# Check if the database file exists
db_path = "logs/crm.db"
if os.path.exists(db_path):
    print(f"Database file found at {db_path}")
    
    # Connect and check record count
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        print(f"Found {count} log records in database")
        
        cursor.execute("SELECT category, COUNT(*) FROM logs GROUP BY category")
        categories = cursor.fetchall()
        print("Log counts by category:")
        for category, count in categories:
            print(f"  {category}: {count}")
            
    except Exception as e:
        print(f"Error accessing database: {e}")
else:
    print(f"Database file not found at {db_path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in logs directory: {os.listdir('logs') if os.path.exists('logs') else 'logs directory not found'}")