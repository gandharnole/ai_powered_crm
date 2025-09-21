# sample_data_generator.py
import sqlite3
import random
import datetime
import json
import uuid
from pathlib import Path
import time

# Ensure log directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Connect to database
conn = sqlite3.connect("logs/crm.db")
cursor = conn.cursor()

# Create logs table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    level TEXT,
    category TEXT,
    message TEXT,
    customer_id TEXT,
    vehicle_id TEXT,
    operation_id TEXT,
    user_id TEXT,
    details TEXT
)
''')
conn.commit()

# Sample data
customer_ids = [f"CUST-{i:04d}" for i in range(1, 51)]
vehicle_ids = [f"VEH-{i:04d}" for i in range(1, 101)]
service_ids = [f"SRV-{i:04d}" for i in range(1, 201)]
user_ids = [f"USER-{i:02d}" for i in range(1, 11)]

vehicle_models = ["Sedan X", "SUV Pro", "Compact Y", "Luxury Z", "Electric Future", "Hybrid Max"]
service_types = ["Oil Change", "Tire Rotation", "Brake Service", "Regular Maintenance", "Battery Replacement", "Air Filter"]
sales_stages = ["LEAD", "CONTACT", "TEST_DRIVE", "NEGOTIATION", "PURCHASE", "DELIVERY"]
esg_actions = ["Solar Panel Installation", "LED Lighting Upgrade", "Water Recycling System", "EV Charging Stations", "Paperless Service Records", "Energy Audit"]

# Generate logs for the past 30 days
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=30)
current_date = start_date

print("Generating sample log data...")

# Helper function to generate a random timestamp between two dates
def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)

# Clear existing data
cursor.execute("DELETE FROM logs")
conn.commit()

# Generate system logs
print("Generating system logs...")
for _ in range(50):
    timestamp = random_date(start_date, end_date).isoformat()
    level = random.choice(["INFO", "INFO", "INFO", "WARN", "ERROR"])
    message = f"System {random.choice(['startup', 'config change', 'backup', 'update', 'health check'])}"
    operation_id = str(uuid.uuid4())
    details = json.dumps({
        "component": random.choice(["database", "api", "frontend", "auth", "scheduler"]),
        "status": "success" if level == "INFO" else "failed"
    })
    
    cursor.execute('''
    INSERT INTO logs (timestamp, level, category, message, operation_id, details)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, level, "SYSTEM", message, operation_id, details))

# Generate customer logs
print("Generating customer logs...")
for customer_id in customer_ids:
    # Registration
    reg_date = random_date(start_date, end_date - datetime.timedelta(days=3))
    cursor.execute('''
    INSERT INTO logs (timestamp, level, category, message, customer_id, operation_id, user_id, details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg_date.isoformat(),
        "INFO",
        "CUSTOMER",
        "Customer registration",
        customer_id,
        str(uuid.uuid4()),
        random.choice(user_ids),
        json.dumps({
            "name": f"Customer {customer_id.split('-')[1]}",
            "email": f"customer{customer_id.split('-')[1]}@example.com",
            "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "preferences": random.sample(["SUV", "Electric", "Luxury", "Compact", "Hybrid"], k=random.randint(1, 3))
        })
    ))
    
    # Profile updates
    if random.random() < 0.7:  # 70% chance of profile update
        update_date = random_date(reg_date, end_date)
        cursor.execute('''
        INSERT INTO logs (timestamp, level, category, message, customer_id, operation_id, user_id, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            update_date.isoformat(),
            "INFO",
            "CUSTOMER",
            "Customer profile update",
            customer_id,
            str(uuid.uuid4()),
            random.choice(user_ids),
            json.dumps({
                "updated_fields": random.sample(["email", "phone", "address", "preferences"], k=random.randint(1, 3)),
                "reason": random.choice(["customer request", "data verification", "marketing opt-in"])
            })
        ))

# Generate sales logs
print("Generating sales logs...")
for i, customer_id in enumerate(random.sample(customer_ids, 40)):  # 40 customers in sales pipeline
    vehicle_id = random.choice(vehicle_ids)
    
    # Create a complete sales journey for some customers
    stages_count = random.randint(1, len(sales_stages))
    journey_stages = sales_stages[:stages_count]
    
    last_date = start_date
    for stage in journey_stages:
        stage_date = random_date(last_date, min(last_date + datetime.timedelta(days=7), end_date))
        
        cursor.execute('''
        INSERT INTO logs (timestamp, level, category, message, customer_id, vehicle_id, operation_id, user_id, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stage_date.isoformat(),
            "INFO",
            "SALES",
            f"Sales event: {stage}",
            customer_id,
            vehicle_id,
            str(uuid.uuid4()),
            random.choice(user_ids),
            json.dumps({
                "model": random.choice(vehicle_models),
                "status": "successful" if stage != "NEGOTIATION" else random.choice(["successful", "pending", "needs_followup"]),
                "notes": f"Customer interested in {random.choice(['financing', 'leasing', 'cash purchase'])}"
            })
        ))
        
        last_date = stage_date

# Generate inventory logs
print("Generating inventory logs...")
for _ in range(60):
    timestamp = random_date(start_date, end_date).isoformat()
    change_type = random.choice(["received", "allocated", "sold", "transferred"])
    vehicle_id = random.choice(vehicle_ids) if change_type in ["allocated", "sold", "transferred"] else None
    
    cursor.execute('''
    INSERT INTO logs (timestamp, level, category, message, vehicle_id, operation_id, details)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        "INFO",
        "INVENTORY",
        f"Inventory {change_type}",
        vehicle_id,
        str(uuid.uuid4()),
        json.dumps({
            "model": random.choice(vehicle_models),
            "quantity": 1,
            "location": random.choice(["main_showroom", "north_branch", "service_center", "warehouse"]),
            "value": random.randint(25000, 75000)
        })
    ))

# Generate service logs
print("Generating service logs...")
for service_id in service_ids[:100]:  # Only use first 100 service IDs
    customer_id = random.choice(customer_ids)
    vehicle_id = random.choice(vehicle_ids)
    service_type = random.choice(service_types)
    
    # Schedule
    schedule_date = random_date(start_date, end_date - datetime.timedelta(days=2))
    cursor.execute('''
    INSERT INTO logs (timestamp, level, category, message, service_id, customer_id, vehicle_id, operation_id, details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        schedule_date.isoformat(),
        "INFO",
        "SERVICE",
        "Service SCHEDULED",
        service_id,
        customer_id,
        vehicle_id,
        str(uuid.uuid4()),
        json.dumps({
            "service_type": service_type,
            "scheduled_date": (schedule_date + datetime.timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
            "estimated_time": f"{random.randint(30, 120)} minutes",
            "notes": random.choice(["Regular maintenance", "Customer reported issue", "Warranty service", ""])
        })
    ))
    
    # Other service events with 80% chance
    if random.random() < 0.8:
        check_in_date = schedule_date + datetime.timedelta(days=random.randint(1, 5))
        if check_in_date <= end_date:
            cursor.execute('''
            INSERT INTO logs (timestamp, level, category, message, service_id, customer_id, vehicle_id, operation_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                check_in_date.isoformat(),
                "INFO",
                "SERVICE",
                "Service CHECK_IN",
                service_id,
                customer_id,
                vehicle_id,
                str(uuid.uuid4()),
                json.dumps({
                    "service_type": service_type,
                    "technician": random.choice(user_ids),
                    "mileage": random.randint(5000, 80000)
                })
            ))
            
            # Completion with 75% chance
            if random.random() < 0.75:
                complete_date = check_in_date + datetime.timedelta(hours=random.randint(1, 8))
                if complete_date <= end_date:
                    satisfaction = round(random.uniform(3.0, 5.0), 1)
                    cursor.execute('''
                    INSERT INTO logs (timestamp, level, category, message, service_id, customer_id, vehicle_id, operation_id, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        complete_date.isoformat(),
                        "INFO",
                        "SERVICE",
                        "Service COMPLETED",
                        service_id,
                        customer_id,
                        vehicle_id,
                        str(uuid.uuid4()),
                        json.dumps({
                            "service_type": service_type,
                            "duration_minutes": random.randint(30, 240),
                            "parts_used": random.randint(0, 3),
                            "satisfaction_score": satisfaction,
                            "followup_required": satisfaction < 4.0
                        })
                    ))

# Generate ESG logs
print("Generating ESG logs...")
esg_score = 65.0  # Starting ESG score
for i in range(10):
    action = random.choice(esg_actions)
    timestamp = random_date(start_date, end_date).isoformat()
    improvement = round(random.uniform(0.5, 3.0), 1)
    previous_score = esg_score
    esg_score += improvement
    
    cursor.execute('''
    INSERT INTO logs (timestamp, level, category, message, operation_id, details)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        "INFO",
        "ESG",
        f"ESG action: {action}",
        str(uuid.uuid4()),
        json.dumps({
            "metrics": {
                "previousScore": previous_score,
                "newScore": esg_score,
                "category": random.choice(["Environmental", "Social", "Governance"]),
                "cost": random.randint(5000, 50000),
                "ROI_months": random.randint(6, 36)
            },
            "recommendations": [
                {
                    "id": f"REC-{random.randint(100, 999)}",
                    "description": random.choice([
                        "Install solar panels on service center roof",
                        "Implement water recycling in car wash",
                        "Switch to biodegradable cleaning products",
                        "Replace dealership lighting with LED",
                        "Offer EV charging for customers"
                    ]),
                    "estimatedImpact": f"+{round(random.uniform(0.3, 2.0), 1)} points"
                }
            ]
        })
    ))

conn.commit()
print(f"Sample data generation complete! Generated logs for {len(customer_ids)} customers.")
print("You can now run your Streamlit app to see the visualizations.")