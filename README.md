# UPI Fraud Detection System

A comprehensive machine learning-based fraud detection system for UPI (Unified Payments Interface) transactions with phishing detection capabilities and an interactive web dashboard.

## 🎯 Overview

This system combines multiple machine learning techniques to detect fraudulent UPI transactions and phishing attempts in real-time. It features:

- **Multi-model Fraud Detection**: XGBoost and Random Forest classifiers trained on imbalanced datasets with SMOTE
- **Anomaly Detection**: User behavior-based anomaly detection using Isolation Forest
- **Phishing Detection**: Gradient Boosting classifier to identify phishing attempts
- **Synthetic Data Generation**: GAN-based synthetic fraud data generation for model training
- **Real-time Risk Scoring**: Dynamic risk assessment based on transaction patterns
- **Interactive Dashboard**: Web-based UI for transaction monitoring and user management
- **Database Logging**: SQLite-based transaction and alert logging

## 📋 Features

### Core Capabilities
- User authentication and registration
- Transaction processing with real-time fraud prediction
- Phishing URL and email detection
- Behavioral anomaly detection per user
- Risk score calculation with explainability
- SMS alerts for suspicious transactions
- Transaction history and fraud alerts tracking
- User profile management

### Detection Methods
1. **Feature-based Detection**: 40+ features including transaction amount, frequency, timing patterns
2. **Anomaly Detection**: Statistical deviation from user's normal behavior
3. **Phishing Detection**: URL analysis and email pattern recognition
4. **Ensemble Models**: Multiple models voting for improved accuracy

## 🛠 Technology Stack

### Core
- **Python 3.x**: Main programming language
- **Flask**: Web framework for dashboard and API
- **SQLite**: Database for transactions and users
- **Gunicorn**: Production WSGI server

### Machine Learning
- **scikit-learn**: Random Forest, SMOTE, preprocessing
- **XGBoost**: Gradient boosted trees for fraud classification
- **TensorFlow**: Neural networks (optional)
- **CTGAN**: Synthetic data generation
- **SHAP**: Model explainability

### Data Processing
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **matplotlib, seaborn**: Data visualization

### Additional
- **beautifulsoup4**: HTML parsing for phishing detection
- **requests, python-whois**: Web data retrieval
- **python-dateutil**: Date/time utilities

## 📁 Project Structure

```
upi_fraud_detection/
├── app.py                      # Main Flask application
├── database.py                 # SQLite database setup and operations
├── model_training.py           # Model training and evaluation
├── preprocess.py              # Data preprocessing pipeline
├── anomaly_detection.py        # User behavior anomaly detection
├── gan_generator.py           # Synthetic data generation with GAN
├── phishing_feature.py        # Phishing detection features
├── PhishingDetection.py       # Phishing model training
├── utils.py                   # Utility functions
├── requirements.txt           # Python dependencies
│
├── models/                    # Pre-trained models (pkl files)
│   ├── xgb_model.pkl
│   ├── rf_model.pkl
│   ├── phishing_model.pkl
│   ├── user_anomaly_models.pkl
│   └── label_encoders.pkl
│
├── templates/                 # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transaction.html
│   ├── transaction_history.html
│   ├── phishing_detector.html
│   ├── payment_options.html
│   ├── payment_details.html
│   ├── payment_success.html
│   └── user_profile.html
│
├── static/                    # Static assets
│   ├── CSS/
│   │   └── style.css
│   └── images/
│
├── logs/                      # Application logs
│
├── data/
│   ├── UPI_Dataset.csv       # Original UPI transaction data
│   ├── phishing.csv          # Phishing dataset
│   ├── user_profiles.csv     # Learned user profiles
│   └── synthetic_fraud_data_*.csv  # Generated synthetic data
│
└── fraud_detection.db         # SQLite database (created at runtime)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd upi_fraud_detection
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

#### First Run (Model Training)
```bash
python app.py
```

On the first run, the system will:
- Load and preprocess the UPI dataset
- Generate synthetic fraud data using GAN
- Train XGBoost and Random Forest models
- Build user anomaly detection models
- Create the SQLite database

This may take 5-10 minutes depending on your hardware.

#### Subsequent Runs
```bash
python app.py
```

Subsequent runs will load pre-trained models and start the Flask server immediately.

#### For Production
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## 📊 Database Schema

### users table
```sql
- upi_id (TEXT, PRIMARY KEY)
- name (TEXT)
- last_active (TEXT)
- device_os (TEXT)
- phone_number (TEXT, UNIQUE)
- bank_name (TEXT)
- password_hash (TEXT)
```

### transactions table
```sql
- transaction_id (TEXT, PRIMARY KEY)
- sender_upi_id (TEXT)
- receiver_upi_id (TEXT)
- amount (REAL)
- timestamp (TEXT)
- fraud_prediction (INTEGER)
- confidence_score (REAL)
- risk_score (REAL)
```

### fraud_alerts table
```sql
- alert_id (TEXT, PRIMARY KEY)
- transaction_id (TEXT)
- alert_type (TEXT)
- severity (TEXT)
- timestamp (TEXT)
```

## 🤖 Machine Learning Models

### XGBoost Classifier
- **Purpose**: Primary fraud classification
- **Features**: 40+ engineered features
- **Performance**: High accuracy with balanced precision-recall
- **Training**: Uses SMOTE for handling class imbalance

### Random Forest Classifier
- **Purpose**: Ensemble voting and robustness
- **Estimators**: 100 trees
- **Performance**: Provides second opinion on fraud detection

### Isolation Forest (Anomaly Detection)
- **Purpose**: Detects unusual user behavior
- **Method**: Per-user anomaly models trained on historical transactions
- **Features**: Amount, frequency, timing patterns

### Phishing Detector (Gradient Boosting)
- **Purpose**: Identifies phishing URLs and emails
- **Features**: URL structure, domain age, SSL certificates
- **Dataset**: Phishing.csv with 11,055 samples

## ⚙️ Configuration

### app.py Settings
```python
app.config['BASE_URL'] = 'http://Your IP Address:5000'  # Change to your IP
app.secret_key = os.urandom(24)  # Secure session key
```

### Environment Variables (.env)
```
FLASK_ENV=development
FLASK_DEBUG=False
DATABASE_URL=sqlite:///fraud_detection.db
LOG_LEVEL=INFO
```

## 📈 Feature Engineering

The system uses 40+ engineered features including:

- **Transaction Features**: Amount, type, time of day
- **User Behavior**: Average transaction amount, frequency, standard deviation
- **Temporal**: Time since last transaction, hour of day, day of week
- **Geographic**: IP location consistency
- **Device**: OS type, device fingerprint
- **Velocity**: Transactions per hour/day
- **Network**: Receiver reputation, new receiver flag

## 🔍 Model Explainability

The system uses SHAP (SHapley Additive exPlanations) to provide:
- Feature importance scores
- Individual prediction explanations
- Impact visualization for each feature
- Model decision path transparency

## 📝 Usage Examples

### Making a Transaction
1. Login with UPI ID
2. Enter receiver UPI ID and amount
3. System analyzes for fraud in real-time
4. Transaction confirmed or flagged as suspicious

### Phishing Detection
1. Navigate to Phishing Detector
2. Enter URL or email content
3. System analyzes and provides verdict
4. Displays risk indicators

### Monitoring Dashboard
- View recent transactions
- Check fraud alerts
- Monitor user profiles
- Generate reports

## 🔐 Security Features

- Password hashing with secure algorithms
- Session management with secure tokens
- SQLite database with transaction logging
- SMS alerts for suspicious transactions
- Rate limiting and velocity checks
- Device fingerprinting

## 🐛 Troubleshooting

### Models Not Loading
```
ERROR: 'models/xgb_model.pkl' not found
```
**Solution**: Run `python app.py` once to train models. This is a one-time setup.

### Database Locked
```
ERROR: database is locked
```
**Solution**: Ensure only one instance of the app is running. Delete `fraud_detection.db` to reset.

### Import Errors
```
ModuleNotFoundError: No module named 'xgboost'
```
**Solution**: Run `pip install -r requirements.txt` to install all dependencies.

### Phishing Model Missing
```
WARNING: 'phishing_feature.py' not found. Phishing detector will be disabled.
```
**Solution**: Phishing detection is optional. Train it separately with `PhishingDetection.py`.

## 📊 Model Performance

### XGBoost Metrics (typical)
- Accuracy: ~95%
- Precision: ~93%
- Recall: ~92%
- F1-Score: ~92%
- AUC-ROC: ~0.98

(Actual performance depends on dataset and training parameters)

## 🔄 Retraining Models

To retrain models with new data:

```python
# In Python shell
from model_training import train_models
from preprocess import preprocess_pipeline

df, encoders = preprocess_pipeline()
rf_model, xgb_model = train_models(df)

# Save models
import pickle
with open('models/xgb_model.pkl', 'wb') as f:
    pickle.dump(xgb_model, f)
```

## 📚 API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /logout` - User logout

### Transactions
- `POST /transaction` - Create new transaction
- `GET /transaction_history` - View user's transactions
- `GET /dashboard` - View fraud dashboard

### Phishing Detection
- `POST /phishing_detector` - Check URL/email for phishing
- `GET /phishing` - Phishing detection page

### User Management
- `GET /user_profile` - View user profile
- `POST /user_profile` - Update user profile

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## 📄 License

MIT License

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Contact: ashetty8904@gmail.com



## 🎓 References

- [SMOTE: Synthetic Minority Oversampling Technique](https://arxiv.org/abs/1106.1813)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/papers/icdm08.pdf)
- [SHAP Explainability](https://github.com/slundberg/shap)



## 📝 Changelog

### v1.0.0
- Initial release
- XGBoost and Random Forest models
- Phishing detection
- Web dashboard
- User management system
- Real-time fraud detection

---


