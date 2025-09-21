import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import json
from datetime import datetime, timedelta
import sqlite3

class PredictiveAnalytics:
    def __init__(self, db_path="logs/crm.db"):
        self.conn = sqlite3.connect(db_path)
        self.model_path = "models"
        self.purchase_model = None
        self.service_model = None
    
    def _prepare_customer_features(self, customer_id):
        """Extract features for a customer based on their log history"""
        # Get all logs for this customer
        query = "SELECT * FROM logs WHERE customer_id = ?"
        customer_logs = pd.read_sql_query(query, self.conn, params=(customer_id,))
        
        if customer_logs.empty:
            return None
        
        # Extract features
        features = {}
        
        # Activity recency (days since last interaction)
        if not customer_logs.empty:
            latest_interaction = pd.to_datetime(customer_logs['timestamp']).max()
            features['days_since_last_interaction'] = (datetime.now() - latest_interaction).days
        else:
            features['days_since_last_interaction'] = 365  # Default for new customers
            
        # Interaction counts by category
        category_counts = customer_logs['category'].value_counts().to_dict()
        for category in ['CUSTOMER', 'SALES', 'SERVICE', 'ESG']:
            features[f'{category.lower()}_interaction_count'] = category_counts.get(category, 0)
            
        # Sales funnel progression
        sales_logs = customer_logs[customer_logs['category'] == 'SALES']
        if not sales_logs.empty:
            # Check highest funnel stage reached
            stages = ['LEAD', 'CONTACT', 'TEST_DRIVE', 'NEGOTIATION', 'PURCHASE', 'DELIVERY']
            stage_reached = 0
            for i, stage in enumerate(stages):
                if sales_logs['message'].str.contains(stage).any():
                    stage_reached = i + 1
            features['sales_funnel_stage'] = stage_reached
        else:
            features['sales_funnel_stage'] = 0
            
        # Service history
        service_logs = customer_logs[customer_logs['category'] == 'SERVICE']
        features['service_count'] = len(service_logs)
        
        # Average satisfaction score from service events
        satisfaction_scores = []
        for _, log in service_logs.iterrows():
            try:
                details = json.loads(log['details'])
                if 'satisfaction_score' in details:
                    satisfaction_scores.append(details['satisfaction_score'])
            except:
                pass
                
        features['avg_satisfaction'] = np.mean(satisfaction_scores) if satisfaction_scores else 3.0
        
        # Time since registration
        customer_reg = customer_logs[customer_logs['message'] == 'Customer registration']
        if not customer_reg.empty:
            reg_date = pd.to_datetime(customer_reg['timestamp'].iloc[0])
            features['days_since_registration'] = (datetime.now() - reg_date).days
        else:
            features['days_since_registration'] = 0
            
        return features
    
    def train_purchase_prediction_model(self):
        """Train a model to predict likelihood of purchase"""
        # Get all customers
        query = "SELECT DISTINCT customer_id FROM logs WHERE customer_id IS NOT NULL"
        customer_ids = pd.read_sql_query(query, self.conn)['customer_id'].tolist()
        
        # Prepare training data
        X = []
        y = []
        
        for customer_id in customer_ids:
            features = self._prepare_customer_features(customer_id)
            if features:
                # Check if customer has completed a purchase
                query = "SELECT * FROM logs WHERE customer_id = ? AND message LIKE '%PURCHASE%'"
                purchase_logs = pd.read_sql_query(query, self.conn, params=(customer_id,))
                has_purchased = not purchase_logs.empty
                
                X.append(list(features.values()))
                y.append(1 if has_purchased else 0)
        
        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)
        
        # Train model if we have data
        if len(X) > 0 and len(np.unique(y)) > 1:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Save model
            self.purchase_model = model
            joblib.dump(model, f"{self.model_path}/purchase_prediction_model.joblib")
            
            # Return accuracy
            accuracy = model.score(X_test, y_test)
            return accuracy
        else:
            return None
    
    def predict_purchase_likelihood(self, customer_id):
        """Predict the likelihood of a customer making a purchase"""
        # Load model if not loaded
        if self.purchase_model is None:
            try:
                self.purchase_model = joblib.load(f"{self.model_path}/purchase_prediction_model.joblib")
            except:
                return {"error": "Model not trained yet. Please train the model first."}
        
        # Get customer features
        features = self._prepare_customer_features(customer_id)
        if not features:
            return {"error": "Could not extract features for this customer"}
        
        # Make prediction
        features_array = np.array(list(features.values())).reshape(1, -1)
        probability = self.purchase_model.predict_proba(features_array)[0][1]
        
        return {
            "customer_id": customer_id,
            "purchase_likelihood": round(probability * 100, 2),
            "recommendation": "High priority lead" if probability > 0.7 else 
                              "Medium priority lead" if probability > 0.4 else 
                              "Low priority lead"
        }
    
    def predict_service_needs(self, vehicle_id):
        """Predict when a vehicle will need service next"""
        # Get vehicle's service history
        query = """
        SELECT * FROM logs 
        WHERE vehicle_id = ? AND category = 'SERVICE'
        ORDER BY timestamp ASC
        """
        service_logs = pd.read_sql_query(query, self.conn, params=(vehicle_id,))
        
        if service_logs.empty:
            return {"error": "No service history found for this vehicle"}
        
        # Get latest service
        latest_service = service_logs.iloc[-1]
        last_service_date = pd.to_datetime(latest_service['timestamp'])
        
        # Simple prediction based on average service interval
        if len(service_logs) > 1:
            service_dates = pd.to_datetime(service_logs['timestamp'])
            intervals = service_dates.diff().dropna()
            avg_interval_days = intervals.mean().days
            
            # If we have meaningful interval data
            if avg_interval_days > 0:
                next_predicted_date = last_service_date + timedelta(days=avg_interval_days)
                days_until_next = (next_predicted_date - datetime.now()).days
                
                return {
                    "vehicle_id": vehicle_id,
                    "last_service_date": last_service_date.strftime("%Y-%m-%d"),
                    "predicted_next_service": next_predicted_date.strftime("%Y-%m-%d"),
                    "days_until_next_service": max(0, days_until_next),
                    "service_urgency": "High" if days_until_next < 7 else 
                                      "Medium" if days_until_next < 30 else 
                                      "Low"
                }
        
        # Default prediction (3 months) if not enough data
        next_predicted_date = last_service_date + timedelta(days=90)
        days_until_next = (next_predicted_date - datetime.now()).days
        
        return {
            "vehicle_id": vehicle_id,
            "last_service_date": last_service_date.strftime("%Y-%m-%d"),
            "predicted_next_service": next_predicted_date.strftime("%Y-%m-%d"),
            "days_until_next_service": max(0, days_until_next),
            "confidence": "Low (based on standard intervals)"
        }

    def identify_customer_segments(self, min_cluster_size=5):
        """Segment customers based on their interaction patterns"""
        from sklearn.cluster import KMeans
        
        # Get all customers
        query = "SELECT DISTINCT customer_id FROM logs WHERE customer_id IS NOT NULL"
        customer_ids = pd.read_sql_query(query, self.conn)['customer_id'].tolist()
        
        # Prepare feature matrix
        feature_data = []
        ids = []
        
        for customer_id in customer_ids:
            features = self._prepare_customer_features(customer_id)
            if features:
                feature_data.append(list(features.values()))
                ids.append(customer_id)
        
        # Convert to DataFrame
        if not feature_data:
            return {"error": "Not enough customer data for segmentation"}
            
        feature_array = np.array(feature_data)
        
        # Determine optimal number of clusters (simplified)
        k = min(5, max(2, len(feature_data) // min_cluster_size))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=k, random_state=42)
        clusters = kmeans.fit_predict(feature_array)
        
        # Analyze clusters
        segments = {}
        for i in range(k):
            cluster_indices = np.where(clusters == i)[0]
            cluster_customers = [ids[idx] for idx in cluster_indices]
            
            # Calculate segment characteristics
            segment_features = feature_array[cluster_indices].mean(axis=0)
            
            segments[f"Segment {i+1}"] = {
                "size": len(cluster_customers),
                "customers": cluster_customers,
                "avg_service_count": round(segment_features[5], 1),
                "avg_satisfaction": round(segment_features[6], 2),
                "avg_sales_funnel_stage": round(segment_features[4], 1),
                "segment_description": self._describe_segment(segment_features)
            }
        
        return segments
    
    def _describe_segment(self, features):
        """Generate a description for a customer segment based on their features"""
        # This is a simplified version - would be more sophisticated in production
        days_since_last = features[0]
        customer_count = features[1]
        sales_count = features[2]
        service_count = features[5]
        satisfaction = features[6]
        sales_stage = features[4]
        
        if sales_stage > 4 and service_count > 2:
            return "Loyal Customers"
        elif sales_stage > 3 and days_since_last < 30:
            return "Active Buyers"
        elif service_count > 3 and satisfaction > 4:
            return "Service Loyalists"
        elif sales_count > customer_count and sales_stage < 3:
            return "Prospective Customers"
        elif days_since_last > 180:
            return "Inactive Customers"
        else:
            return "General Customers"