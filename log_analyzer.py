import pandas as pd
import json
import sqlite3
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self, db_path="logs/crm.db"):
        self.conn = sqlite3.connect(db_path)
        
    def get_logs_by_category(self, category, limit=100):
        query = "SELECT * FROM logs WHERE category = ? ORDER BY timestamp DESC LIMIT ?"
        return pd.read_sql_query(query, self.conn, params=(category, limit))
    
    def get_logs_by_customer(self, customer_id, limit=100):
        query = "SELECT * FROM logs WHERE customer_id = ? ORDER BY timestamp DESC LIMIT ?"
        return pd.read_sql_query(query, self.conn, params=(customer_id, limit))
    
    def get_logs_by_timeframe(self, hours=24):
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM logs WHERE timestamp >= ? ORDER BY timestamp DESC"
        return pd.read_sql_query(query, self.conn, params=(since,))
    
    def get_customer_journey(self, customer_id):
        query = """
        SELECT timestamp, category, message, details
        FROM logs 
        WHERE customer_id = ? 
        ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, self.conn, params=(customer_id,))
        return df
    
    def get_esg_actions(self):
        query = "SELECT * FROM logs WHERE category = 'ESG' ORDER BY timestamp DESC"
        return pd.read_sql_query(query, self.conn)
    
    def get_service_events(self, days=30):
        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT * FROM logs 
        WHERE category = 'SERVICE' AND timestamp >= ?
        ORDER BY timestamp DESC
        """
        return pd.read_sql_query(query, self.conn, params=(since,))
    
    def get_sales_funnel_metrics(self, days=30):
        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT message, COUNT(*) as count
        FROM logs 
        WHERE category = 'SALES' AND timestamp >= ?
        GROUP BY message
        """
        return pd.read_sql_query(query, self.conn, params=(since,))
    
    def get_log_volume_by_day(self, days=30):
        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT date(timestamp) as day, category, COUNT(*) as count
        FROM logs 
        WHERE timestamp >= ?
        GROUP BY day, category
        ORDER BY day
        """
        return pd.read_sql_query(query, self.conn, params=(since,))
    
    def get_inventory_logs(self, days=30):

        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT * FROM logs 
        WHERE category = 'INVENTORY' AND timestamp >= ?
        ORDER BY timestamp DESC
        """
        return pd.read_sql_query(query, self.conn, params=(since,))
