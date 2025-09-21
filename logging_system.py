import structlog
import logging
import uuid
import datetime
import json
from pathlib import Path

# Ensure log directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(log_dir / "automotive_crm.log"),
        logging.StreamHandler()
    ]
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Base logger
logger = structlog.get_logger()

# Domain-specific loggers
customer_logger = logger.bind(category="CUSTOMER")
sales_logger = logger.bind(category="SALES")
inventory_logger = logger.bind(category="INVENTORY")
service_logger = logger.bind(category="SERVICE")
esg_logger = logger.bind(category="ESG")
system_logger = logger.bind(category="SYSTEM")

# Helper functions
def generate_operation_id():
    return str(uuid.uuid4())

# Logging functions
def log_customer_interaction(customer_id, action, details, user_id=None):
    customer_logger.info(
        f"Customer {action}",
        customer_id=customer_id,
        user_id=user_id,
        operation_id=generate_operation_id(),
        details=details
    )

def log_sales_event(event_type, customer_id=None, vehicle_id=None, details=None):
    sales_logger.info(
        f"Sales event: {event_type}",
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        operation_id=generate_operation_id(),
        details=details
    )

def log_inventory_change(change_type, vehicle_id=None, part_id=None, quantity=None, details=None):
    inventory_logger.info(
        f"Inventory {change_type}",
        vehicle_id=vehicle_id,
        part_id=part_id,
        quantity=quantity,
        operation_id=generate_operation_id(),
        details=details
    )

def log_service_event(service_id, event_type, customer_id=None, vehicle_id=None, details=None):
    service_logger.info(
        f"Service {event_type}",
        service_id=service_id,
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        operation_id=generate_operation_id(),
        details=details
    )

def log_esg_action(action_type, metrics=None, recommendations=None):
    esg_logger.info(
        f"ESG action: {action_type}",
        operation_id=generate_operation_id(),
        metrics=metrics,
        recommendations=recommendations
    )

def log_system_event(event_type, component=None, details=None):
    system_logger.info(
        f"System {event_type}",
        component=component,
        operation_id=generate_operation_id(),
        details=details
    )

# Database logging handler (for persistent storage)
class DatabaseLogHandler(logging.Handler):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self._ensure_table_exists()
        
    def _ensure_table_exists(self):
        cursor = self.conn.cursor()
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
        self.conn.commit()
        
    def emit(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            try:
                log_data = json.loads(record.getMessage())
                cursor = self.conn.cursor()
                cursor.execute('''
                INSERT INTO logs (
                    timestamp, level, category, message, customer_id, 
                    vehicle_id, operation_id, user_id, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_data.get('timestamp', datetime.datetime.now().isoformat()),
                    log_data.get('level', ''),
                    log_data.get('category', ''),
                    log_data.get('event', ''),
                    log_data.get('customer_id', ''),
                    log_data.get('vehicle_id', ''),
                    log_data.get('operation_id', ''),
                    log_data.get('user_id', ''),
                    json.dumps(log_data.get('details', {}))
                ))
                self.conn.commit()
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error processing log record: {e}")