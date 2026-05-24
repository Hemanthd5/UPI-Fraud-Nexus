"""
import os
import pickle
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from preprocess import preprocess_pipeline
from gan_generator import generate_synthetic_data
from anomaly_detection import build_user_profiles, train_anomaly_detectors, check_anomaly, retrain_user_profiles
from model_training import train_models, predict_fraud
import uuid
import numpy as np
from dotenv import load_dotenv
load_dotenv()
import secrets  # For generating secure tokens

from database import (
    setup_database, insert_user, get_user_data,
    get_user_data_by_phone,  # NEW
    get_receiver_data, log_all_data,
    get_user_transactions, insert_transaction, insert_fraud_alert,DB_PATH, insert_confirmation, get_confirmation, delete_confirmation
)

try:
    from phishing_feature import FeatureExtraction
except ImportError:
    print("WARNING: 'phishing_feature.py' not found. Phishing detector will be disabled.")
    FeatureExtraction = None

# --- MODIFIED: Import new Utils functions ---
from utils import (
    get_real_time_data, calculate_risk_score, get_explanation,
    log_message, get_transaction_fields_from_db,
    hash_password, check_password, send_sms_alert  # NEW
)
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['BASE_URL'] = 'http://Your IP Address:5000' # Change to your ip address


def initialize_system():
    global xgb_model, user_profiles, user_anomaly_models, preprocessed_df, combined_df, label_encoders, phishing_gbc_model

    log_message('info', "Initializing system...")
    setup_database()

    # --- LOAD PHISHING MODEL ---
    try:
        with open('models/phishing_model.pkl', 'rb') as f:
            phishing_gbc_model = pickle.load(f)
        log_message('info', "Phishing detection model loaded successfully.")
    except FileNotFoundError:
        log_message('error',
                    "Phishing model ('models/phishing_model.pkl') not found. Phishing detector will be disabled.")
    except Exception as e:
        log_message('error', f"Error loading phishing model: {e}")
    # --- END LOADING PHISHING MODEL ---

    if not os.path.exists('models/xgb_model.pkl'):
        log_message('info', "First-time run detected. Building the pipeline...")
        preprocessed_df, label_encoders = preprocess_pipeline()
        if preprocessed_df is not None:
            log_all_data(preprocessed_df)
            synthetic_df = generate_synthetic_data(preprocessed_df)
            combined_df = pd.concat([preprocessed_df, synthetic_df], ignore_index=True)

            user_profiles = build_user_profiles(preprocessed_df)
            user_anomaly_models = train_anomaly_detectors(preprocessed_df)

            _, xgb_model = train_models(combined_df)

            with open('models/label_encoders.pkl', 'wb') as f:
                pickle.dump(label_encoders, f)

            log_message('info', "Pipeline setup complete. Models and profiles saved.")
        else:
            log_message('error', "Failed to load or preprocess data. System initialization incomplete.")
            return
    else:
        log_message('info', "Loading pre-trained models and profiles...")
        with open('models/xgb_model.pkl', 'rb') as f:
            xgb_model = pickle.load(f)
        with open('models/user_anomaly_models.pkl', 'rb') as f:
            user_anomaly_models = pickle.load(f)
        with open('models/label_encoders.pkl', 'rb') as f:
            label_encoders = pickle.load(f)

        user_profiles = pd.read_csv('user_profiles.csv')
        preprocessed_df, _ = preprocess_pipeline()
        log_message('info', "Models and profiles loaded successfully.")


@app.route('/')
def index():

    return render_template('index.html')


# --- MODIFIED: LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')

        # Check if user exists
        user_data = get_user_data_by_phone(phone_number)

        # user_data is now a dictionary-like object
        if user_data and check_password(user_data['password_hash'], password):
            # Store the UUID (upi_id) and name in the session
            session['sender_id'] = user_data['upi_id']
            session['sender_name'] = user_data['name']

            log_message('info', f"User {user_data['name']} ({user_data['upi_id']}) logged in.")

            return redirect(url_for('dashboard'))
        else:
            flash("Invalid phone number or password.", "error")
            return render_template('login.html', error="Invalid phone number or password.")

    return render_template('login.html')


# --- NEW: LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.pop('sender_id', None)
    session.pop('sender_name', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


# --- MODIFIED: REGISTER ROUTE ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sender_name = request.form.get('sender_name')
        phone_number = request.form.get('phone_number')
        device_os = request.form.get('device_os')
        bank_name = request.form.get('bank_name')
        password = request.form.get('password')

        # Check if phone number already exists
        if get_user_data_by_phone(phone_number):
            flash("Phone number already registered. Please login.", "error")
            return render_template('register.html', error="Phone number already registered.")

        # Hash password and generate UUID
        hashed_password = hash_password(password)
        generated_uuid = str(uuid.uuid4())

        # Insert new user
        insert_user(
            upi_id=generated_uuid,
            name=sender_name,
            device_os=device_os,
            phone_number=phone_number,
            bank_name=bank_name,
            password_hash=hashed_password
        )

        log_message('info', f"New user '{sender_name}' ({generated_uuid}) registered.")

        flash(f"Account created successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# --- MODIFIED: Dashboard and other routes to use session ---
@app.route('/dashboard')
def dashboard():
    if 'sender_id' not in session:
        return redirect(url_for('login'))

    sender_id = session['sender_id']
    sender_name = session['sender_name']

    all_transactions = get_user_transactions(sender_id)
    recent_transactions = all_transactions[:5]

    return render_template('dashboard.html',
                           sender_id=sender_id,
                           sender_name=sender_name,
                           recent_transactions=recent_transactions)


@app.route('/transaction')
def transaction():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']
    return render_template('transaction.html', sender_id=sender_id, sender_name=sender_name)


@app.route('/history')
def history():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']
    transactions = get_user_transactions(sender_id)
    return render_template('transaction_history.html', sender_id=sender_id, sender_name=sender_name,
                           transactions=transactions)


@app.route('/profile')
def profile():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']

    user_data = get_user_data(sender_id)  # Fetches by UUID

    if not user_data:
        flash("Error loading profile.", "error")
        return redirect(url_for('dashboard'))

    return render_template('user_profile.html',
                           user_data=user_data,  # Pass the whole dict-like object
                           sender_id=sender_id,
                           sender_name=sender_name)


@app.route('/retrain', methods=['POST'])
def retrain():
    # This route should be admin-protected in a real app
    retrain_user_profiles()
    return "Models and profiles are being retrained in the background.", 200


@app.route('/phishing_detector', methods=["GET", "POST"])
def phishing_detector():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']
    url_to_check = request.form.get("url", "")

    if request.method == "POST":
        url = request.form["url"]

        # ... (rest of your phishing logic is unchanged) ...
        if phishing_gbc_model is None or FeatureExtraction is None:
            log_message('error', "Phishing model or feature extractor is not loaded.")
            flash("Phishing Detector is currently unavailable.", "error")
            return render_template('phishing_detector.html', xx=-1, sender_id=sender_id, sender_name=sender_name)

        try:
            obj = FeatureExtraction(url)
            x = np.array(obj.getFeaturesList()).reshape(1, 30)
            y_pro_non_phishing = phishing_gbc_model.predict_proba(x)[0, 1]
            return render_template('phishing_detector.html', xx=round(y_pro_non_phishing, 2), url=url,
                                   sender_id=sender_id, sender_name=sender_name)
        except Exception as e:
            log_message('error', f"Error during phishing prediction: {e}")
            flash("An error occurred. Please ensure the URL is valid and starts with http:// or https://", "error")
            return render_template('phishing_detector.html', xx=-1, url=url, sender_id=sender_id,
                                   sender_name=sender_name)

    return render_template("phishing_detector.html", xx=-1, sender_id=sender_id, sender_name=sender_name)


@app.route('/confirm/<token>')
def confirm_payment(token):
    data = get_confirmation(token)
    if data:
        # data = (token, sender_id, receiver_id, amount, timestamp)
        sender_id, receiver_id, amount = data[1], data[2], data[3]

        # Valid token found! Delete it (one-time use) and proceed
        delete_confirmation(token)

        # Log user in temporarily or ensure session exists
        session['sender_id'] = sender_id

        flash("Transaction verified via SMS link!", "success")
        return redirect(url_for('pay', sender_id=sender_id, receiver_id=receiver_id, amount=amount))
    else:
        return "<h1>Invalid or Expired Link</h1><p>Please initiate the transaction again.</p>"

@app.route('/predict', methods=['POST'])
def predict():
    global xgb_model, user_profiles, user_anomaly_models, preprocessed_df, label_encoders

    # Get user data from session
    if 'sender_id' not in session:
        return redirect(url_for('login'))

    # This sender_upi_id is the UUID, which is correct for the models
    sender_upi_id = session['sender_id']
    sender_name = session['sender_name']

    receiver_upi_id = request.form.get('receiver_upi_id')
    amount = float(request.form.get('amount'))
    transaction_type = request.form.get('transaction_type')
    transaction_city = request.form.get('transaction_city')

    # Get user's full data (including device_os and phone_number)
    sender_data = get_user_data(sender_upi_id)  # Fetches by UUID
    if not sender_data:
        flash("Session error, please login again.", "error")
        return redirect(url_for('login'))

    device_os = sender_data['device_os']
    phone_number = sender_data['phone_number']

    # ... (rest of the prediction logic is mostly the same) ...

    is_new_receiver = get_receiver_data(receiver_upi_id) is None
    real_time_data = get_real_time_data()
    sender_fields, receiver_fields = get_transaction_fields_from_db(sender_upi_id, receiver_upi_id)

    new_txn = pd.DataFrame([{
        'Transaction_ID': real_time_data['Transaction_ID'],
        'Sender_UPI_ID': sender_upi_id,  # This is the UUID
        'Receiver_UPI_ID': receiver_upi_id,
        'Transaction_Type': transaction_type,
        'Payment_Gateway': 'Unknown',
        'Transaction_City': transaction_city,
        'Transaction_State': 'Unknown',
        'IP_Address': real_time_data['IP_Address'],
        'Transaction_Status': 'Completed',
        'Device_OS': device_os,  # Use the user's real device_os
        'Transaction_Frequency': sender_fields['Transaction_Frequency'],
        'Merchant_Category': receiver_fields['Merchant_Category'],
        'Transaction_Channel': 'In-store',
        'Transaction_Amount_Deviation': 0,
        'Days_Since_Last_Transaction': sender_fields['Days_Since_Last_Transaction'],
        'amount': amount,
        'fraud': 0,
        'hour': pd.to_datetime(real_time_data['Time']).hour,
        'day_of_week': pd.to_datetime(real_time_data['Date']).dayofweek
    }])

    processed_txn = new_txn.drop(columns=['Transaction_ID', 'IP_Address', 'fraud'])

    categorical_cols = ['Transaction_Type', 'Payment_Gateway', 'Transaction_City', 'Transaction_State',
                        'Transaction_Status', 'Device_OS', 'Merchant_Category', 'Transaction_Channel']

    for col in categorical_cols:
        if col in processed_txn.columns and col in label_encoders:
            le = label_encoders[col]
            processed_txn[col] = processed_txn[col].apply(lambda x: str(x) if str(x) in le.classes_ else 'Unknown')
            try:
                processed_txn[col] = le.transform(processed_txn[col])
            except ValueError:
                processed_txn[col] = -1
        elif col in processed_txn.columns:
            processed_txn[col] = -1

    is_new_sender = sender_fields['Transaction_Frequency'] == 0

    is_anomaly, anomaly_score = check_anomaly(processed_txn, user_profiles, user_anomaly_models)

    PREDICTION_THRESHOLD = 0.7
    model_cols = xgb_model.feature_names_in_
    prediction_features = processed_txn.drop(columns=['Sender_UPI_ID', 'Receiver_UPI_ID'])
    prediction_features = prediction_features.reindex(columns=model_cols).fillna(-1)

    prediction, probability = predict_fraud(xgb_model, prediction_features, threshold=PREDICTION_THRESHOLD)

    risk_score = calculate_risk_score(probability, is_anomaly, is_new_sender, is_new_receiver)
    explanation = get_explanation(risk_score, is_anomaly, is_new_sender, is_new_receiver)

    insert_transaction(
        real_time_data['Transaction_ID'],
        sender_upi_id,  # The UUID
        receiver_upi_id,
        amount,
        f"{real_time_data['Date']} {real_time_data['Time']}",
        'Completed',
        prediction
    )
    insert_fraud_alert(real_time_data['Transaction_ID'], risk_score, explanation)

    result = "Fraudulent Transaction" if prediction == 1 else "Legitimate Transaction"

    if prediction == 0:
        # Legitimate transaction
        return redirect(url_for('pay',
                                receiver_id=receiver_upi_id,
                                amount=amount))
    else:

        # 1. Generate secure token
        token = secrets.token_urlsafe(16)
        insert_confirmation(token, sender_upi_id, receiver_upi_id, amount)
        # 3. Build Link
        base_url = app.config.get('BASE_URL', 'http://localhost:5000')
        link = f"{base_url}//confirm/{token}"

        # 4. Send SMS
        alert_msg = f"ALERT: High risk transaction of Rs.{amount} detected. To AUTHORIZE anyway, click:\n {link}"
        send_sms_alert(phone_number, alert_msg)

        return render_template('transaction.html',
                               sender_id=sender_upi_id,
                               sender_name=sender_name,
                               receiver_id=receiver_upi_id,
                               amount=amount,
                               result=result,
                               risk_score=round(risk_score, 2),
                               explanation=explanation + " We sent a verification link to your phone.")


# --- MODIFIED: Payment flow to use session ---
@app.route('/pay', methods=['GET'])
def pay():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    if 'sender_name' in session:
        sender_name = session['sender_name']
    else:
        user_data = get_user_data(sender_id)
        sender_name = user_data['name']
        session['sender_name'] = sender_name
    #sender_name = session['sender_name']

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    return render_template('payment_options.html',
                           sender_id=sender_id,
                           receiver_id=receiver_id,
                           amount=amount,
                           sender_name=sender_name)


@app.route('/details', methods=['GET'])
def details():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    option = request.args.get('option')
    return render_template('payment_details.html',
                           sender_id=sender_id,
                           receiver_id=receiver_id,
                           amount=amount,
                           option=option,
                           sender_name=sender_name)


@app.route('/complete', methods=['GET'])
def complete():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session['sender_name']

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    return render_template('payment_success.html',
                           sender_id=sender_id,
                           sender_name=sender_name,
                           receiver_id=receiver_id,
                           amount=amount)


if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        print(f"Database file found at {DB_PATH}. Checking schema...")
        conn_check = sqlite3.connect(DB_PATH)
        c_check = conn_check.cursor()
        try:
            c_check.execute("SELECT phone_number FROM users LIMIT 1")
            print("Database schema appears correct (phone_number found).")
        except sqlite3.OperationalError:
            print("SCHEMA MISMATCH! Old database detected.")
            print("!!! DELETE 'fraud_detection.db' manually before running!!!")

    initialize_system()
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
import os
import pickle
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from preprocess import preprocess_pipeline
from gan_generator import generate_synthetic_data
from anomaly_detection import build_user_profiles, train_anomaly_detectors, check_anomaly, retrain_user_profiles
from model_training import train_models, predict_fraud
import uuid
import numpy as np
from dotenv import load_dotenv
import secrets  # For secure tokens

load_dotenv()

# --- MODIFIED: Import new DB and Utils functions ---
from database import (
    setup_database, insert_user, get_user_data,
    get_user_data_by_phone,
    get_receiver_data, log_all_data,
    get_user_transactions, insert_transaction, insert_fraud_alert,
    DB_PATH,
    insert_confirmation, get_confirmation, delete_confirmation, update_transaction_fraud_status  # NEW
)

try:
    from phishing_feature import FeatureExtraction
except ImportError:
    print("WARNING: 'phishing_feature.py' not found. Phishing detector will be disabled.")
    FeatureExtraction = None

# --- MODIFIED: Import new Utils functions ---
from utils import (
    get_real_time_data, calculate_risk_score, get_explanation,
    log_message, get_transaction_fields_from_db,
    hash_password, check_password, send_sms_alert
)
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIG: BASE URL FOR SMS LINKS ---
# Replace this with your ngrok URL if using ngrok (e.g., 'https://xyz.ngrok-free.app')
# Or use your local IP if testing on same WiFi (e.g., 'http://192.168.1.5:5000')
app.config['BASE_URL'] = 'http://192.168.0.106:5000'

# Global variables
xgb_model = None
user_profiles = None
user_anomaly_models = None
preprocessed_df = None
combined_df = None
label_encoders = None
phishing_gbc_model = None


def initialize_system():
    global xgb_model, user_profiles, user_anomaly_models, preprocessed_df, combined_df, label_encoders, phishing_gbc_model

    log_message('info', "Initializing system...")
    setup_database()

    # --- LOAD PHISHING MODEL ---
    try:
        with open('models/phishing_model.pkl', 'rb') as f:
            phishing_gbc_model = pickle.load(f)
        log_message('info', "Phishing detection model loaded successfully.")
    except FileNotFoundError:
        log_message('error',
                    "Phishing model ('models/phishing_model.pkl') not found. Phishing detector will be disabled.")
    except Exception as e:
        log_message('error', f"Error loading phishing model: {e}")

    if not os.path.exists('models/xgb_model.pkl'):
        log_message('info', "First-time run detected. Building the pipeline...")
        preprocessed_df, label_encoders = preprocess_pipeline()
        if preprocessed_df is not None:
            log_all_data(preprocessed_df)
            synthetic_df = generate_synthetic_data(preprocessed_df)
            combined_df = pd.concat([preprocessed_df, synthetic_df], ignore_index=True)

            user_profiles = build_user_profiles(preprocessed_df)
            user_anomaly_models = train_anomaly_detectors(preprocessed_df)

            _, xgb_model = train_models(combined_df)

            with open('models/label_encoders.pkl', 'wb') as f:
                pickle.dump(label_encoders, f)

            log_message('info', "Pipeline setup complete. Models and profiles saved.")
        else:
            log_message('error', "Failed to load or preprocess data. System initialization incomplete.")
            return
    else:
        log_message('info', "Loading pre-trained models and profiles...")
        with open('models/xgb_model.pkl', 'rb') as f:
            xgb_model = pickle.load(f)
        with open('models/user_anomaly_models.pkl', 'rb') as f:
            user_anomaly_models = pickle.load(f)
        with open('models/label_encoders.pkl', 'rb') as f:
            label_encoders = pickle.load(f)

        user_profiles = pd.read_csv('user_profiles.csv')
        preprocessed_df, _ = preprocess_pipeline()
        log_message('info', "Models and profiles loaded successfully.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')

        user_data = get_user_data_by_phone(phone_number)

        if user_data and check_password(user_data['password_hash'], password):
            session['sender_id'] = user_data['upi_id']
            session['sender_name'] = user_data['name']
            log_message('info', f"User {user_data['name']} ({user_data['upi_id']}) logged in.")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid phone number or password.", "error")
            return render_template('login.html', error="Invalid phone number or password.")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('sender_id', None)
    session.pop('sender_name', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sender_name = request.form.get('sender_name')
        phone_number = request.form.get('phone_number')
        device_os = request.form.get('device_os')
        bank_name = request.form.get('bank_name')
        password = request.form.get('password')

        if get_user_data_by_phone(phone_number):
            flash("Phone number already registered. Please login.", "error")
            return render_template('register.html', error="Phone number already registered.")

        hashed_password = hash_password(password)
        generated_uuid = str(uuid.uuid4())

        insert_user(
            upi_id=generated_uuid,
            name=sender_name,
            device_os=device_os,
            phone_number=phone_number,
            bank_name=bank_name,
            password_hash=hashed_password
        )

        log_message('info', f"New user '{sender_name}' ({generated_uuid}) registered.")
        flash(f"Account created successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'sender_id' not in session:
        return redirect(url_for('login'))

    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    all_transactions = get_user_transactions(sender_id)
    recent_transactions = all_transactions[:5]

    return render_template('dashboard.html',
                           sender_id=sender_id,
                           sender_name=sender_name,
                           recent_transactions=recent_transactions)


@app.route('/transaction')
def transaction():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')
    return render_template('transaction.html', sender_id=sender_id, sender_name=sender_name)


@app.route('/history')
def history():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')
    transactions = get_user_transactions(sender_id)
    return render_template('transaction_history.html', sender_id=sender_id, sender_name=sender_name,
                           transactions=transactions)


@app.route('/profile')
def profile():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    user_data = get_user_data(sender_id)

    if not user_data:
        flash("Error loading profile.", "error")
        return redirect(url_for('dashboard'))

    return render_template('user_profile.html',
                           user_data=user_data,
                           sender_id=sender_id,
                           sender_name=sender_name)


@app.route('/retrain', methods=['POST'])
def retrain():
    retrain_user_profiles()
    return "Models and profiles are being retrained in the background.", 200


@app.route('/phishing_detector', methods=["GET", "POST"])
def phishing_detector():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    if request.method == "POST":
        url = request.form["url"]

        if phishing_gbc_model is None or FeatureExtraction is None:
            log_message('error', "Phishing model or feature extractor is not loaded.")
            flash("Phishing Detector is currently unavailable.", "error")
            return render_template('phishing_detector.html', xx=-1, sender_id=sender_id, sender_name=sender_name)

        try:
            obj = FeatureExtraction(url)
            x = np.array(obj.getFeaturesList()).reshape(1, 30)
            y_pro_non_phishing = phishing_gbc_model.predict_proba(x)[0, 1]
            return render_template('phishing_detector.html', xx=round(y_pro_non_phishing, 2), url=url,
                                   sender_id=sender_id, sender_name=sender_name)
        except Exception as e:
            log_message('error', f"Error during phishing prediction: {e}")
            flash("An error occurred. Please ensure the URL is valid.", "error")
            return render_template('phishing_detector.html', xx=-1, url=url, sender_id=sender_id,
                                   sender_name=sender_name)

    return render_template("phishing_detector.html", xx=-1, sender_id=sender_id, sender_name=sender_name)


# --- MODIFIED CONFIRM ROUTE ---
@app.route('/confirm/<token>')
def confirm_payment(token):
    data = get_confirmation(token)
    if data:
        # data structure: (token, transaction_id, sender_id, receiver_id, amount, timestamp)
        # NOTE: We added transaction_id at index 1
        transaction_id = data[1]
        sender_id = data[2]
        receiver_id = data[3]
        amount = data[4]

        # 1. Valid token found! Delete it so it cannot be reused
        delete_confirmation(token)

        # 2. CRITICAL: Update transaction to be LEGITIMATE (is_fraud = 0)
        update_transaction_fraud_status(transaction_id, 0)

        # 3. Log user in temporarily/refresh session if needed
        session['sender_id'] = sender_id
        user_data = get_user_data(sender_id)
        if user_data:
            session['sender_name'] = user_data['name']
        else:
            session['sender_name'] = 'User'

        flash("Identity verified. Please select your payment method.", "success")
        return redirect(url_for('pay',
                                receiver_id=receiver_id,
                                amount=amount))
    else:
        return "<h1>Invalid or Expired Link</h1><p>This link is invalid or has already been used. Please initiate the transaction again from your dashboard.</p>"


@app.route('/predict', methods=['POST'])
def predict():
    global xgb_model, user_profiles, user_anomaly_models, preprocessed_df, label_encoders

    if 'sender_id' not in session:
        return redirect(url_for('login'))

    sender_upi_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    receiver_upi_id = request.form.get('receiver_upi_id')
    amount = float(request.form.get('amount'))
    transaction_type = request.form.get('transaction_type')
    transaction_city = request.form.get('transaction_city')

    sender_data = get_user_data(sender_upi_id)
    if not sender_data:
        flash("Session error, please login again.", "error")
        return redirect(url_for('login'))

    device_os = sender_data['device_os']
    phone_number = sender_data['phone_number']

    is_new_receiver = get_receiver_data(receiver_upi_id) is None
    real_time_data = get_real_time_data()

    # Store this ID to pass to confirmation logic
    current_transaction_id = real_time_data['Transaction_ID']

    sender_fields, receiver_fields = get_transaction_fields_from_db(sender_upi_id, receiver_upi_id)

    new_txn = pd.DataFrame([{
        'Transaction_ID': current_transaction_id,
        'Sender_UPI_ID': sender_upi_id,
        'Receiver_UPI_ID': receiver_upi_id,
        'Transaction_Type': transaction_type,
        'Payment_Gateway': 'Unknown',
        'Transaction_City': transaction_city,
        'Transaction_State': 'Unknown',
        'IP_Address': real_time_data['IP_Address'],
        'Transaction_Status': 'Completed',
        'Device_OS': device_os,
        'Transaction_Frequency': sender_fields['Transaction_Frequency'],
        'Merchant_Category': receiver_fields['Merchant_Category'],
        'Transaction_Channel': 'In-store',
        'Transaction_Amount_Deviation': 0,
        'Days_Since_Last_Transaction': sender_fields['Days_Since_Last_Transaction'],
        'amount': amount,
        'fraud': 0,
        'hour': pd.to_datetime(real_time_data['Time']).hour,
        'day_of_week': pd.to_datetime(real_time_data['Date']).dayofweek
    }])

    processed_txn = new_txn.drop(columns=['Transaction_ID', 'IP_Address', 'fraud'])

    categorical_cols = ['Transaction_Type', 'Payment_Gateway', 'Transaction_City', 'Transaction_State',
                        'Transaction_Status', 'Device_OS', 'Merchant_Category', 'Transaction_Channel']

    for col in categorical_cols:
        if col in processed_txn.columns and col in label_encoders:
            le = label_encoders[col]
            processed_txn[col] = processed_txn[col].apply(lambda x: str(x) if str(x) in le.classes_ else 'Unknown')
            try:
                processed_txn[col] = le.transform(processed_txn[col])
            except ValueError:
                processed_txn[col] = -1
        elif col in processed_txn.columns:
            processed_txn[col] = -1

    is_new_sender = sender_fields['Transaction_Frequency'] == 0

    is_anomaly, anomaly_score = check_anomaly(processed_txn, user_profiles, user_anomaly_models)

    PREDICTION_THRESHOLD = 0.7
    model_cols = xgb_model.feature_names_in_
    prediction_features = processed_txn.drop(columns=['Sender_UPI_ID', 'Receiver_UPI_ID'])
    prediction_features = prediction_features.reindex(columns=model_cols).fillna(-1)

    prediction, probability = predict_fraud(xgb_model, prediction_features, threshold=PREDICTION_THRESHOLD)

    risk_score = calculate_risk_score(probability, is_anomaly, is_new_sender, is_new_receiver)
    explanation = get_explanation(risk_score, is_anomaly, is_new_sender, is_new_receiver)

    insert_transaction(
        current_transaction_id,
        sender_upi_id,
        receiver_upi_id,
        amount,
        f"{real_time_data['Date']} {real_time_data['Time']}",
        'Completed',
        prediction
    )
    insert_fraud_alert(current_transaction_id, risk_score, explanation)

    result = "Fraudulent Transaction" if prediction == 1 else "Legitimate Transaction"

    if prediction == 0:
        return redirect(url_for('pay',
                                sender_id=sender_upi_id,
                                receiver_id=receiver_upi_id,
                                amount=amount,
                                sender_name=sender_name))
    else:
        # --- FRAUD DETECTED: SEND SMS WITH LINK ---

        # 1. Generate secure token
        token = secrets.token_urlsafe(16)

        # 2. Store in DB (Now passing current_transaction_id)
        insert_confirmation(token, current_transaction_id, sender_upi_id, receiver_upi_id, amount)

        # 3. Build Link
        base_url = app.config.get('BASE_URL', 'http://localhost:5000')
        link = f"{base_url}/confirm/{token}"

        # 4. Send SMS
        #alert_msg = f"ALERT: High risk transaction of Rs.{amount} detected.\n\nTo AUTHORIZE this payment, click here:\n{link}"
        alert_msg = (
            f"UPI-NEXUS SECURITY ALERT\n\n"
            f"Transaction of Rs.{amount} to {receiver_upi_id} was declined due to SECURITY RISK.\n\n"
            f"If you initiated this, click to AUTHORIZE:\n{link}\n\n"
            f"Not you? Contact your Bank immediately."
        )
        send_sms_alert(phone_number, alert_msg)

        return render_template('transaction.html',
                               sender_id=sender_upi_id,
                               sender_name=sender_name,
                               receiver_id=receiver_upi_id,
                               amount=amount,
                               result=result,
                               risk_score=round(risk_score, 2),
                               explanation=explanation + " We sent a verification link to your phone.")


@app.route('/pay', methods=['GET'])
def pay():
    if 'sender_id' not in session:
        return redirect(url_for('login'))

    sender_id = session['sender_id']

    # SAFEGUARD: Try to get name from session, else fetch from DB
    if 'sender_name' in session:
        sender_name = session['sender_name']
    else:
        user_data = get_user_data(sender_id)
        if user_data:
            sender_name = user_data['name']
            session['sender_name'] = sender_name
        else:
            sender_name = "User"

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    return render_template('payment_options.html',
                           sender_id=sender_id,
                           receiver_id=receiver_id,
                           amount=amount,
                           sender_name=sender_name)


@app.route('/details', methods=['GET'])
def details():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    option = request.args.get('option')
    return render_template('payment_details.html',
                           sender_id=sender_id,
                           receiver_id=receiver_id,
                           amount=amount,
                           option=option,
                           sender_name=sender_name)


@app.route('/complete', methods=['GET'])
def complete():
    if 'sender_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['sender_id']
    sender_name = session.get('sender_name', 'User')

    receiver_id = request.args.get('receiver_id')
    amount = request.args.get('amount')
    return render_template('payment_success.html',
                           sender_id=sender_id,
                           sender_name=sender_name,
                           receiver_id=receiver_id,
                           amount=amount)


if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        print(f"Database file found at {DB_PATH}. Checking schema...")
        conn_check = sqlite3.connect(DB_PATH)
        c_check = conn_check.cursor()
        try:
            # We check for the new column 'transaction_id' in 'payment_confirmations'
            c_check.execute("SELECT transaction_id FROM payment_confirmations LIMIT 1")
            print("Database schema appears correct.")
        except sqlite3.OperationalError:
            print("SCHEMA MISMATCH! Old database detected.")
            # os.remove(DB_PATH)
            print("!!! DELETE 'fraud_detection.db' manually before running!!!")

    initialize_system()

    # Run on 0.0.0.0 so other devices on network can access it
    app.run(host='0.0.0.0', port=5000, debug=True)