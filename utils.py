"""
import datetime
import random
import uuid
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_current_time_date():

    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

def get_real_time_data():

    transaction_id = str(uuid.uuid4())
    date, time = get_current_time_date()
    ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    device_os = random.choice(['Windows', 'iOS', 'Android', 'MacOS'])
    
    return {
        'Transaction_ID': transaction_id,
        'Date': date,
        'Time': time,
        'IP_Address': ip_address,
        'Device_OS': device_os
    }

def calculate_risk_score(fraud_proba, is_anomaly, is_new_sender, is_new_receiver):

    score = fraud_proba * 100
    
    if is_anomaly:
        score += 10
    if is_new_sender or is_new_receiver:
        score += 5 # Medium risk for new users/receivers
        
    score = min(100, score)
    return score

def get_explanation(risk_score, is_anomaly, is_new_sender, is_new_receiver):

    if risk_score > 75:
        base_explanation = "This transaction is flagged as high-risk."
    elif risk_score > 50:
        base_explanation = "This transaction is flagged as medium-risk."
    else:
        base_explanation = "This transaction is likely legitimate."
        
    reasons = []
    if is_anomaly:
        reasons.append("It shows unusual behavior for this user.")
    if is_new_sender:
        reasons.append("The sender is a new user.")
    if is_new_receiver:
        reasons.append("The receiver is new or has no historical data.")
    
    if reasons:
        explanation = base_explanation + " Reasons: " + " ".join(reasons)
    else:
        explanation = base_explanation
        
    return explanation

def log_message(level, message):

    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)

def get_transaction_fields_from_db(sender_upi_id, receiver_upi_id):

    # Simulate a database lookup
    sender_data = {'Transaction_Frequency': 2, 'Days_Since_Last_Transaction': 5}
    receiver_data = {'Merchant_Category': 'Investment'}
    
    return sender_data, receiver_data
"""
import datetime
import random
import uuid
import logging
import pandas as pd
import os  # <-- ADD THIS IMPORT
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client  # <-- ADD THIS IMPORT

# --- REAL API Keys (read from environment variables) ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- (hash_password and check_password functions remain the same) ---
def hash_password(password):
    """Hashes a password for storing."""
    return generate_password_hash(password)


def check_password(hashed_password, password):
    """Checks a provided password against a stored hash."""
    return check_password_hash(hashed_password, password)


# --- UPDATED: send_sms_alert function ---
def send_sms_alert(phone_number, message):
    """
    Sends an SMS alert using Twilio.
    """

    # Ensure all credentials are set
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        log_message('error', "Twilio credentials are not set. Cannot send SMS.")
        return

    # IMPORTANT: Ensure the phone number has the country code (e.g., +91, +1)
    # This is a simple check; you might need a more robust one
    if not phone_number.startswith('+'):
        log_message('warning', f"Phone number {phone_number} missing country code. SMS may fail.")
        # Example for India:
        # if len(phone_number) == 10:
        #     phone_number = f"+91{phone_number}"

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        log_message('info', f"Successfully sent SMS alert. Message SID: {sms.sid}")
    except Exception as e:
        log_message('error', f"Failed to send SMS: {e}")


def get_current_time_date():
    """
    Returns the current time and date.
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


# --- (All other functions: get_real_time_data, calculate_risk_score, etc. remain the same) ---

def get_real_time_data():
    """
    Generates placeholder real-time data for a new transaction.
    NOTE: In a real-world application, this would capture actual device data.
    """
    transaction_id = str(uuid.uuid4())
    date, time = get_current_time_date()
    ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    device_os = random.choice(['Windows', 'iOS', 'Android', 'MacOS'])

    return {
        'Transaction_ID': transaction_id,
        'Date': date,
        'Time': time,
        'IP_Address': ip_address,
        'Device_OS': device_os
    }


def calculate_risk_score(fraud_proba, is_anomaly, is_new_sender, is_new_receiver):
    """
    Calculates a risk score based on prediction probability and other flags.
    """
    score = fraud_proba * 100

    if is_anomaly:
        score += 10
    if is_new_sender or is_new_receiver:
        score += 5  # Medium risk for new users/receivers

    score = min(100, score)
    return score


def get_explanation(risk_score, is_anomaly, is_new_sender, is_new_receiver):
    """
    Generates a textual explanation for the fraud prediction.
    """
    if risk_score > 75:
        base_explanation = "This transaction is flagged as high-risk."
    elif risk_score > 50:
        base_explanation = "This transaction is flagged as medium-risk."
    else:
        base_explanation = "This transaction is likely legitimate."

    reasons = []
    if is_anomaly:
        reasons.append("It shows unusual behavior for this user.")
    if is_new_sender:
        reasons.append("The sender is a new user.")
    if is_new_receiver:
        reasons.append("The receiver is new or has no historical data.")

    if reasons:
        explanation = base_explanation + " Reasons: " + " ".join(reasons)
    else:
        explanation = base_explanation

    return explanation


def log_message(level, message):
    """
    Logs a message with the specified level.
    """
    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)


def get_transaction_fields_from_db(sender_upi_id, receiver_upi_id):
    """
    Fetches required details from the database to complete a transaction record.
    NOTE: This is a placeholder function. In a real application, this would
    require a proper database lookup.
    """
    # Simulate a database lookup
    sender_data = {'Transaction_Frequency': 2, 'Days_Since_Last_Transaction': 5}
    receiver_data = {'Merchant_Category': 'Investment'}

    return sender_data, receiver_data