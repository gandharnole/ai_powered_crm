# Create a file called populate_db.py
import sqlite3
import datetime
import json
import uuid
import os
from pathlib import Path

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Connect to database
print("Connecting to database...")
conn = sqlite3.connect("logs/crm.db")
cursor = conn.cursor()

# Drop and recreate the table to ensure we're starting fresh
print("Creating tables...")
cursor.execute("DROP TABLE IF EXISTS logs")
cursor.execute('''
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    level TEXT,
    category TEXT,
    message TEXT,
    customer_id TEXT,
    vehicle_id TEXT,
    operation_id TEXT,
    user_id TEXT,
    details TEXT,
    service_id
)
''')
conn.commit()

# Insert a few test records
print("Inserting test records...")
test_records = [
    # System log
    {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO",
        "category": "SYSTEM",
        "message": "System startup",
        "operation_id": str(uuid.uuid4()),
        "details": json.dumps({"status": "success"})
    },
    # Customer log
    {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO",
        "category": "CUSTOMER", 
        "message": "Customer registration",
        "customer_id": "CUST-0001",
        "operation_id": str(uuid.uuid4()),
        "user_id": "USER-01",
        "details": json.dumps({"name": "John Doe", "email": "john@example.com"})
    },
    # Sales log
    {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO", 
        "category": "SALES",
        "message": "Sales event: TEST_DRIVE",
        "customer_id": "CUST-0001",
        "vehicle_id": "VEH-0001",
        "operation_id": str(uuid.uuid4()),
        "details": json.dumps({"model": "SUV Pro", "status": "completed"})
    },
    # Service log
    {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO",
        "category": "SERVICE",
        "message": "Service SCHEDULED",
        "service_id": "SRV-0001",
        "customer_id": "CUST-0001",
        "vehicle_id": "VEH-0001",
        "operation_id": str(uuid.uuid4()),
        "details": json.dumps({"service_type": "Oil Change", "scheduled_date": "2025-04-20"})
    },
    # ESG log
    {
        "timestamp": datetime.datetime.now().isoformat(),
        "level": "INFO",
        "category": "ESG",
        "message": "ESG action: Solar Panel Installation",
        "operation_id": str(uuid.uuid4()),
        "details": json.dumps({
            "metrics": {
                "previousScore": 65.0,
                "newScore": 67.2,
                "category": "Environmental"
            }
        })
    }
]

for record in test_records:
    # Create the SQL based on what fields are present
    fields = list(record.keys())
    placeholders = ", ".join(["?" for _ in fields])
    fields_str = ", ".join(fields)
    
    # Create parameter list in same order as fields
    params = [record[field] for field in fields]
    
    cursor.execute(f"INSERT INTO logs ({fields_str}) VALUES ({placeholders})", params)

conn.commit()
print("Inserted test records.")

# Verify data was inserted
cursor.execute("SELECT COUNT(*) FROM logs")
count = cursor.fetchone()[0]
print(f"Database now contains {count} records.")

cursor.execute("SELECT category, COUNT(*) FROM logs GROUP BY category")
categories = cursor.fetchall()
print("Log counts by category:")
for category, count in categories:
    print(f"  {category}: {count}")

conn.close()
print("Database prepared successfully!")