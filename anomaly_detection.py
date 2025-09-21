import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import json
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetection:
    def __init__(self, db_path="logs/crm.db"):
        self.conn = sqlite3.connect(db_path)
        self.model = None
        self.scaler = None
    
    def detect_system_anomalies(self, days=7, contamination=0.05):
        """
        Detect anomalies in system logs based on patterns and frequencies
        """
        # Get system logs for the specified time period
        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT * FROM logs 
        WHERE category = 'SYSTEM' AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        system_logs = pd.read_sql_query(query, self.conn, params=(since,))
        
        if len(system_logs) < 10:  # Need minimum sample size
            return {
                "status": "insufficient_data",
                "message": f"Not enough system logs in the past {days} days for anomaly detection"
            }
        
        # Extract features
        features = []
        for _, log in system_logs.iterrows():
            # Basic features
            timestamp = pd.to_datetime(log['timestamp'])
            hour_of_day = timestamp.hour
            day_of_week = timestamp.dayofweek
            
            # Level as numeric
            level_map = {"INFO": 1, "WARN": 2, "ERROR": 3}
            level_num = level_map.get(log['level'], 0)
            
            # Extract details if available
            detail_fields = 0
            try:
                details = json.loads(log['details'])
                detail_fields = len(details)
            except:
                pass
            
            # Add features
            features.append([
                hour_of_day, 
                day_of_week, 
                level_num,
                detail_fields
            ])
        
        # Convert to numpy array
        X = np.array(features)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train isolation forest model
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.model.fit(X_scaled)
        
        # Predict anomalies
        predictions = self.model.predict(X_scaled)
        system_logs['is_anomaly'] = np.where(predictions == -1, True, False)
        
        # Get anomalous logs
        anomalies = system_logs[system_logs['is_anomaly'] == True]
        
        # Analyze anomalies
        anomaly_summary = {
            "total_logs_analyzed": len(system_logs),
            "anomalies_detected": len(anomalies),
            "anomaly_percentage": round(len(anomalies) / len(system_logs) * 100, 2),
            "anomaly_logs": anomalies[['timestamp', 'level', 'message', 'details']].to_dict('records'),
            "recommendations": self._generate_anomaly_recommendations(anomalies)
        }
        
        return anomaly_summary
    
    def detect_customer_behavior_anomalies(self, days=30, contamination=0.05):
        """
        Detect unusual customer behaviors that might indicate issues or opportunities
        """
        # Get customer interaction logs
        since = (datetime.now() - timedelta(days=days)).isoformat()
        query = """
        SELECT * FROM logs 
        WHERE (category = 'CUSTOMER' OR category = 'SALES' OR category = 'SERVICE')
        AND timestamp >= ?
        AND customer_id IS NOT NULL
        ORDER BY timestamp ASC
        """
        customer_logs = pd.read_sql_query(query, self.conn, params=(since,))
        
        if len(customer_logs) < 20:  # Need minimum sample size
            return {
                "status": "insufficient_data",
                "message": f"Not enough customer logs in the past {days} days for anomaly detection"
            }
        
        # Aggregate by customer
        customer_stats = {}
        
        for customer_id in customer_logs['customer_id'].unique():
            customer_data = customer_logs[customer_logs['customer_id'] == customer_id]
            
            # Calculate features
            interactions = len(customer_data)
            categories = customer_data['category'].value_counts().to_dict()
            recent_days = (datetime.now() - pd.to_datetime(customer_data['timestamp'].max())).days
            
            # Service satisfaction if available
            satisfaction_scores = []
            for _, log in customer_data.iterrows():
                if log['category'] == 'SERVICE':
                    try:
                        details = json.loads(log['details'])
                        if 'satisfaction_score' in details:
                            satisfaction_scores.append(details['satisfaction_score'])
                    except:
                        pass
            
            avg_satisfaction = np.mean(satisfaction_scores) if satisfaction_scores else None
            
            # Store features
            customer_stats[customer_id] = [
                interactions,
                categories.get('CUSTOMER', 0),
                categories.get('SALES', 0),
                categories.get('SERVICE', 0),
                recent_days,
                avg_satisfaction if avg_satisfaction is not None else 3.0  # Default if no data
            ]
        
        # Convert to matrix
        customers = list(customer_stats.keys())
        features = np.array([customer_stats[cid] for cid in customers])
        
        # Handle missing data
        features = np.nan_to_num(features)
        
        # Scale features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Train isolation forest
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(features_scaled)
        
        # Detect anomalies
        predictions = model.predict(features_scaled)
        anomaly_indices = np.where(predictions == -1)[0]
        anomaly_customers = [customers[i] for i in anomaly_indices]
        
        # Analyze anomalous customers
        anomaly_details = []
        for cid in anomaly_customers:
            cust_logs = customer_logs[customer_logs['customer_id'] == cid]
            stats = customer_stats[cid]
            
            # Determine what makes this customer unusual
            unusual_aspects = []
            if stats[0] > np.percentile([s[0] for s in customer_stats.values()], 90):
                unusual_aspects.append("Unusually high interaction count")
            if stats[0] < np.percentile([s[0] for s in customer_stats.values()], 10) and stats[0] > 0:
                unusual_aspects.append("Unusually low interaction count")
            if stats[2] > np.percentile([s[2] for s in customer_stats.values()], 90):
                unusual_aspects.append("High sales activity")
            if stats[3] > np.percentile([s[3] for s in customer_stats.values()], 90):
                unusual_aspects.append("High service utilization")
            if stats[4] < 2:  # Very recent activity
                unusual_aspects.append("Very recent activity")
            if stats[5] < 2.5:  # Low satisfaction
                unusual_aspects.append("Low satisfaction scores")
            if stats[5] > 4.8:  # Perfect satisfaction
                unusual_aspects.append("Exceptionally high satisfaction")
                
            anomaly_details.append({
                "customer_id": cid,
                "interaction_count": int(stats[0]),
                "customer_events": int(stats[1]),
                "sales_events": int(stats[2]),
                "service_events": int(stats[3]),
                "days_since_last_interaction": int(stats[4]),
                "avg_satisfaction": round(stats[5], 2),
                "unusual_aspects": unusual_aspects,
                "recent_logs": cust_logs.head(5)[['timestamp', 'category', 'message']].to_dict('records')
            })
            
        return {
            "total_customers_analyzed": len(customers),
            "anomalies_detected": len(anomaly_customers),
            "anomaly_percentage": round(len(anomaly_customers) / len(customers) * 100, 2),
            "anomaly_details": anomaly_details
        }
    
    def _generate_anomaly_recommendations(self, anomalies):
        """Generate recommendations based on detected anomalies"""
        recommendations = []
        
        # Check for error patterns
        error_count = len(anomalies[anomalies['level'] == 'ERROR'])
        if error_count > 0:
            recommendations.append(
                f"Investigate {error_count} system errors detected as anomalies"
            )
        
        # Check for unusual timing
        hour_counts = pd.to_datetime(anomalies['timestamp']).dt.hour.value_counts()
        unusual_hours = hour_counts[hour_counts > 1].index.tolist()
        if unusual_hours:
            recommendations.append(
                f"Review system activity during unusual hours: {', '.join(map(str, unusual_hours))}"
            )
        
        # Generic recommendations
        if len(anomalies) > 5:
            recommendations.append(
                "Consider reviewing system health metrics for potential issues"
            )
            
        if not recommendations:
            recommendations.append(
                "No specific recommendations based on detected anomalies"
            )
            
        return recommendations