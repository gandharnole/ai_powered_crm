import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import json
from datetime import datetime, timedelta
import altair as alt
from log_analyzer import LogAnalyzer
from pathlib import Path
from logging_system import DatabaseLogHandler
import logging
import pickle
import numpy as np
from flask import Flask, request, render_template
import matplotlib.pyplot as plt
import joblib
import calplot
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tensorflow.keras.models import load_model  # Add this import
import pandas as pd
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
# Page configuration
st.set_page_config(
    page_title="Automotive CRM Logging Dashboard",
    page_icon="🚗",
    layout="wide"
)

# Initialize analyzer
analyzer = LogAnalyzer()

# Initialize database and logging system
@st.cache_resource
def initialize_db():
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create and initialize the database
    conn = sqlite3.connect("logs/crm.db")
    
    # Add database handler to logging system
    db_handler = DatabaseLogHandler(conn)
    logging.getLogger().addHandler(db_handler)
    
    return conn

# Initialize on app startup
conn = initialize_db()

# Load .env file for credentials
load_dotenv()
EMAIL_ADDRESS = os.getenv("GMAIL_USER")
EMAIL_PASSWORD = os.getenv("GMAIL_PASS")

def send_email(to_email, subject, message_body):
    msg = MIMEText(message_body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False

# Dummy Gmail credentials
EMAIL_ADDRESS = os.getenv("GMAIL_USER")  # Replace with your Gmail address
APP_PASSWORD = os.getenv("GMAIL_PASS")  # Replace with the app password you generated

# Email sending function
def send_email(to_email, subject, body):
    try:
        # Set up the server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Use TLS to secure the connection
        server.login(EMAIL_ADDRESS, APP_PASSWORD)

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send the email
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.close()

        st.success(f"✅ Email sent successfully to {to_email}")

    except Exception as e:
        st.error(f"Error while sending email: {str(e)}")

# Load the saved sentiment analysis model
model = load_model('sentiment_model.keras')

# Load or define your tokenizer (recreate or load from a file if saved separately)
tokenizer = Tokenizer(num_words=5000)

# Function to predict sentiment
def predict_sentiment(text):
    # Tokenize the text using the fitted tokenizer
    tw = tokenizer.texts_to_sequences([text])
    tw = pad_sequences(tw, maxlen=200)  # Adjust the maxlen as per your training
    prediction = int(model.predict(tw).round().item())
    return 'Positive' if prediction == 1 else 'Negative'



# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview", 
        "Customer Logs", 
        "ESG Integration", 
        "Service Tracking", 
        "ESG Integration",
        "Social Media Analytics",
        "Inventory Management",
        "Sales Forecast"
    ]
)

# Time filter for all pages
time_options = {
    "Last 24 hours": 24,
    "Last 7 days": 24*7,
    "Last 30 days": 24*30,
    "All time": None
}
selected_time = st.sidebar.selectbox("Time Period", list(time_options.keys()))
time_hours = time_options[selected_time]

# Main content based on selected page
if page == "Overview":
    st.title("Automotive CRM Logging Dashboard")
    
    # Stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    # If time_hours is None, use a large value to get all logs
    hours_filter = time_hours if time_hours else 24*365*10
    
    logs_df = analyzer.get_logs_by_timeframe(hours=hours_filter)
    
    with col1:
        customer_count = len(logs_df[logs_df['category'] == 'CUSTOMER']['customer_id'].unique())
        st.metric("Unique Customers", customer_count)
    
    with col2:
        sales_events = len(logs_df[logs_df['category'] == 'SALES'])
        st.metric("Sales Events", sales_events)
    
    with col3:
        service_events = len(logs_df[logs_df['category'] == 'SERVICE'])
        st.metric("Service Events", service_events)
    
    with col4:
        esg_actions = len(logs_df[logs_df['category'] == 'ESG'])
        st.metric("ESG Actions", esg_actions)
    
    # Log volume chart
    st.subheader("Log Volume by Category")
    volume_data = analyzer.get_log_volume_by_day(days=30 if time_hours is None else time_hours//24)
    
    if not volume_data.empty:
        chart = alt.Chart(volume_data).mark_area().encode(
            x='day:T',
            y='count:Q',
            color='category:N',
            tooltip=['day', 'category', 'count']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No log data available for the selected time period.")
    
    # Recent logs table
    st.subheader("Recent Log Events")
    recent_logs = logs_df.head(10)
    if not recent_logs.empty:
        st.dataframe(recent_logs[['timestamp', 'category', 'message', 'customer_id', 'vehicle_id']])
    else:
        st.info("No recent logs found.")

elif page == "Customer Logs":
    st.title("Customer Interaction Logs")
    
    # Customer search
    customer_id = st.text_input("Enter Customer ID")
    
    if customer_id:
        customer_logs = analyzer.get_logs_by_customer(customer_id)
        
        if not customer_logs.empty:
            st.subheader(f"Journey for Customer {customer_id}")
            
            # Timeline visualization
            timeline_data = customer_logs[['timestamp', 'category', 'message']]
            fig = px.timeline(
                timeline_data, 
                x_start="timestamp", 
                y="category",
                color="category",
                hover_data=["message"]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed log table
            st.subheader("Detailed Customer Logs")
            st.dataframe(customer_logs)
        else:
            st.info(f"No logs found for customer {customer_id}")
    else:
        st.info("Enter a customer ID to view their journey.")

elif page == "ESG Integration":
    from esg_dashboard import show_esg_dashboard
    show_esg_dashboard()






# Main code for service tracking
elif page == "Service Tracking":
    import calplot
    import matplotlib.pyplot as plt
    st.title("After-Sales Service Tracking")

    # Load the dataset safely
    csv_path = "D:\Major project\service_records.csv"
    if os.path.exists(csv_path):
        service_df = pd.read_csv(csv_path, parse_dates=["last_service_date", "next_service_due"])
    else:
        service_df = pd.DataFrame(columns=[
            'customer_name', 'contact', 'car_model', 'registration_number',
            'last_service_date', 'service_type', 'next_service_due', 'status'
        ])

    # Add the 'eligible_for_discount' column if not present
    if 'eligible_for_discount' not in service_df.columns:
        service_df["eligible_for_discount"] = service_df.apply(
            lambda row: "✅ Yes" if pd.to_datetime(row["last_service_date"]) < pd.to_datetime(row["next_service_due"]) - pd.Timedelta(days=7) else "❌ No",
            axis=1
        )

    # Show all records
    st.subheader("📋 All Service Records")
    st.dataframe(service_df)

    # Filter/search by registration number
    search_reg = st.text_input("🔍 Search by Registration Number")
    if search_reg:
        filtered = service_df[service_df['registration_number'].str.contains(search_reg, case=False)]
        st.dataframe(filtered)

    # Email reminder functionality
    def generate_email(row):
        discount_deadline = pd.to_datetime(row["next_service_due"]) - pd.Timedelta(days=7)
        eligible = "Yes" if row["eligible_for_discount"] == "✅ Yes" else "No"
        email = f"""
Subject: 🚗 Reminder: Upcoming Vehicle Service Due for Your {row['car_model']}

Dear {row['customer_name']},

We hope you are enjoying a smooth ride in your {row['car_model']}.

This is a friendly reminder that your vehicle with registration number {row['registration_number']} is due for its scheduled {row['service_type']} on {row['next_service_due'].date()}.

To ensure optimal performance and safety, we recommend getting your car serviced on or before this date.

🎁 Good News! You’re eligible for an Early Bird Discount if the service is completed before {discount_deadline.date()}. Don’t miss this opportunity to save!

---
Service Details:
- Car Model: {row['car_model']}
- Service Type: {row['service_type']}
- Last Serviced On: {row['last_service_date']}
- Next Due On: {row['next_service_due'].date()}
- Discount Eligible: {eligible}

---
To book your service appointment or to get more details, please contact our service center.

Thank you for choosing us.

Warm regards,  
Suzuki CRM Team  
Email: support@marutisuzuki.com  
Phone: +91-99760-54678
"""
        return email

    # Generate and send email reminders for services due soon
    st.subheader("📧 Mock Email Reminders for Customers")
    if st.button("📤 Generate and Send Email Reminders"):
        soon_due = service_df[(service_df["next_service_due"] >= pd.to_datetime("today")) & 
                              (service_df["next_service_due"] <= pd.to_datetime("today") + pd.Timedelta(days=15))]

        if not soon_due.empty:
            for _, row in soon_due.iterrows():
                # Prepare the email content
                email_body = generate_email(row)

                # Send the email to the customer
                send_email(row["contact"], "Upcoming Service Due Reminder", email_body)
        else:
            st.warning("✅ No services due in the next 15 days.")



elif page == "ESG Integration":
    st.title("ESG Actions & Metrics")
    
    esg_data = analyzer.get_esg_actions()
    
    if not esg_data.empty:
        st.subheader("ESG Score Improvement History")
        
        # Extract metrics from details column
        esg_metrics = []
        for _, row in esg_data.iterrows():
            try:
                details = json.loads(row['details'])
                if 'metrics' in details and details['metrics']:
                    metrics = details['metrics']
                    if isinstance(metrics, dict) and 'previousScore' in metrics and 'newScore' in metrics:
                        esg_metrics.append({
                            'timestamp': row['timestamp'],
                            'action': row['message'],
                            'previousScore': metrics['previousScore'],
                            'newScore': metrics['newScore'],
                            'improvement': metrics['newScore'] - metrics['previousScore']
                        })
            except:
                continue
        
        if esg_metrics:
            metrics_df = pd.DataFrame(esg_metrics)
            
            # ESG score chart
            chart = alt.Chart(metrics_df).mark_line(point=True).encode(
                x='timestamp:T',
                y='newScore:Q',
                tooltip=['timestamp', 'action', 'previousScore', 'newScore', 'improvement']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
            
            # ESG actions table
            st.subheader("Recent ESG Actions")
            st.dataframe(metrics_df)
        else:
            st.info("No ESG score metrics found in the logs.")
    else:
        st.info("No ESG data available.")

elif page == "Social Media Analytics":
    st.title("Social Media Sentiment Analysis")

    # Sidebar input for the user to enter comments
    st.sidebar.header("Input Your Comments")
    comment = st.sidebar.text_area("Enter the comment:", height=150)

    # Analyzing sentiment
    if st.sidebar.button("Analyze Sentiment"):
        if comment:
            sentiment = predict_sentiment(comment)
            st.write(f"Sentiment of the comment: **{sentiment}**")
        else:
            st.write("Please enter a comment to analyze.")

    # Optionally, show some example positive and negative comments for reference
    st.subheader("Sample Sentiment Analysis")
    sample_comments = [
        ("The experience is amazing.", "Positive"),
        ("I love the service provided by the staff!", "Positive"),
        ("Food quality is not good.", "Negative"),
        ("This is the worst flight experience of my life!", "Negative")
    ]
    for comment, sentiment in sample_comments:
        st.write(f"**Comment**: {comment} - **Sentiment**: {sentiment}")

elif page == "Inventory Management":
    st.title("Inventory Management Dashboard")

    inventory_df = pd.read_csv("D:\Major project\inventory.csv")

    # Display current inventory
    st.subheader("🔍 Current Stock Levels")
    st.dataframe(inventory_df)

    # Show low stock warnings
    low_stock = inventory_df[inventory_df['stock_level'] < inventory_df['reorder_threshold']]
    if not low_stock.empty:
        st.warning("⚠️ The following items are below reorder threshold:")
        st.table(low_stock)

    # Update stock form
    st.subheader("📝 Update Stock")
    selected_car = st.selectbox("Select car model to update", inventory_df['car_model'])
    new_stock = st.number_input("Enter new stock level", min_value=0, value=0, step=1)

    if st.button("Update Stock"):
        inventory_df.loc[inventory_df['car_model'] == selected_car, 'stock_level'] = new_stock
        inventory_df.to_csv("inventory.csv", index=False)
        st.success(f"✅ Stock for {selected_car} updated to {new_stock}")


elif page == "Sales Forecast":
    st.title("📈 Sales Forecast Dashboard (ARIMA)")
    
    model_dir = "sales_models"
    car_models = ['Ertiga', 'WagonR', 'Brezza', 'Grand Vitara']
    selected_car = st.selectbox("Choose a car model to forecast", car_models)

    # Load historical data
    df = pd.read_csv("D:\Major project\maruti_monthly_sales.csv")
    df['month'] = pd.to_datetime(df['month'])
    car_df = df[df['car_model'] == selected_car].copy().set_index('month')
    ts = car_df['units_sold'].asfreq('MS')

    # Load model
    model_path = f"{model_dir}/{selected_car.lower().replace(' ', '_')}_arima_model.pkl"
    model = joblib.load(model_path)

    # Forecast next 6 months
    forecast = model.get_forecast(steps=6)
    forecast_index = pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), periods=6, freq='MS')
    forecast_df = pd.DataFrame({
        'month': forecast_index,
        'forecasted_units': forecast.predicted_mean.astype(int)
    }).set_index('month')

    # Combine actual + forecast
    combined = pd.concat([ts, forecast_df['forecasted_units']], axis=0)
    
    # Plotting
    st.subheader(f"{selected_car} Sales Forecast (Next 6 Months)")
    fig, ax = plt.subplots(figsize=(10, 4))
    ts.plot(ax=ax, label="Actual Sales", marker='o')
    forecast_df['forecasted_units'].plot(ax=ax, label="Forecasted Sales", linestyle='--', color='orange', marker='o')
    ax.set_ylabel("Units Sold")
    ax.set_xlabel("Month")
    ax.legend()
    st.pyplot(fig)

    # Show forecast table
    st.dataframe(forecast_df.reset_index().rename(columns={"month": "Month", "forecasted_units": "Forecasted Sales"}))


