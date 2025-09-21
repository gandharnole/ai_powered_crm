# customer_module.py
from logging_system import log_customer_interaction

def register_new_customer(name, email, phone, address, preferences=None):
    # Business logic to register customer
    customer_id = "CUST-" + generate_id()
    
    # Log the event
    log_customer_interaction(
        customer_id=customer_id,
        action="registration",
        details={
            "name": name,
            "email": email,
            "preferences": preferences
        },
        user_id=current_user_id()
    )
    
    # Continue with customer registration
    return customer_id


# sales_module.py
from logging_system import log_sales_event

def record_test_drive(customer_id, vehicle_id, satisfaction_score):
    # Business logic for test drive
    
    # Log the event
    log_sales_event(
        event_type="TEST_DRIVE",
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        details={
            "satisfaction_score": satisfaction_score,
            "duration_minutes": 30,
            "salesperson": current_user_id()
        }
    )


# esg_module.py
from logging_system import log_esg_action

def implement_sustainability_initiative(initiative_id, initiative_name):
    # Business logic for implementing ESG initiative
    previous_score = get_current_esg_score()
    
    # Implement the initiative
    # ...
    
    # Calculate new score
    new_score = calculate_updated_esg_score()
    
    # Log the ESG action
    log_esg_action(
        action_type="INITIATIVE_IMPLEMENTED",
        metrics={
            "initiativeId": initiative_id,
            "initiativeName": initiative_name,
            "previousScore": previous_score,
            "newScore": new_score,
            "improvement": new_score - previous_score
        },
        recommendations=[
            {
                "id": "REC-123",
                "description": "Install solar panels on service center roof",
                "estimatedImpact": "+0.4 points"
            }
        ]
    )