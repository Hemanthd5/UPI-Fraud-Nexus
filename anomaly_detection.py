'''import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
import os
import sqlite3


def retrain_user_profiles():
    print("Retraining user profiles and anomaly models...")
    conn = sqlite3.connect('fraud_detection.db')
    
    # Load all transactions from the database
    all_transactions_df = pd.read_sql_query("SELECT * FROM transactions", conn)
    
    if all_transactions_df.empty:
        print("No transactions in the database to train on.")
        return

    # Build user profiles from the updated data
    user_profiles = all_transactions_df.groupby('sender_upi_id').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('fraud_prediction', 'count'),  # Using count as a proxy for frequency
        timing_norm=('timestamp', lambda x: pd.to_datetime(x).dt.hour.mean()),
        std_dev=('amount', 'std')
    ).reset_index()
    user_profiles.fillna(0, inplace=True)
    user_profiles.rename(columns={'sender_upi_id': 'Sender_UPI_ID'}, inplace=True)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    # Train anomaly models for users with enough data (e.g., > 3 transactions)
    user_models = {}
    user_counts = all_transactions_df['sender_upi_id'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 3].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = all_transactions_df[all_transactions_df['sender_upi_id'] == user_id].copy()
        
        features = ['amount', 'timestamp', 'fraud_prediction'] # Example features
        
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(user_data[features])
        user_models[user_id] = model
        
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
    
    print(f"Retrained profiles and models for {len(user_models)} users.")
    conn.close()

def build_user_profiles(df):
    """
    Builds a behavioral profile for each user based on their historical transactions.
    """
    print("Building user behavioral profiles...")
    
    # Group by sender and calculate key statistics
    user_profiles = df.groupby('Sender_UPI_ID').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('Transaction_Frequency', 'mean'),
        timing_norm=('hour', 'mean'),
        std_dev=('amount', 'std')
    ).reset_index()
    
    # Fill NaN values (for users with single transactions)
    user_profiles.fillna(0, inplace=True)
    
    # Create a column for anomaly threshold (e.g., based on std dev)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    # Save profiles for future use
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    print("User behavioral profiles built and saved.")
    return user_profiles

def train_anomaly_detectors(df):
    """
    Trains a separate Isolation Forest model for each user with sufficient data.
    """
    print("Training per-user anomaly detection models...")
    user_models = {}
    
    # Get users with enough data points to train a model
    user_counts = df['Sender_UPI_ID'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 1].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = df[df['Sender_UPI_ID'] == user_id].copy()
        
        # Features for anomaly detection
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        
        if not user_data[features].empty:
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(user_data[features])
            user_models[user_id] = model
    
    # Save the models
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
        
    print(f"Trained and saved {len(user_models)} per-user anomaly detection models.")
    return user_models

def check_anomaly(transaction, user_profiles, user_models):
    """
    Checks if a new transaction is anomalous for a given user.
    """
    sender_id = transaction['Sender_UPI_ID'].iloc[0]
    
    # Check if a specific model exists for the user
    if sender_id in user_models:
        model = user_models[sender_id]
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        anomaly_score = model.decision_function(transaction[features])
        is_anomalous = anomaly_score < model.threshold_
        print(f"Anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for user {sender_id}.")
        return is_anomalous.iloc[0], anomaly_score.iloc[0]
    
    # Fallback to a simple rule-based check if no model is trained for the user
    else:
        profile = user_profiles[user_profiles['Sender_UPI_ID'] == sender_id]
        if not profile.empty:
            avg_amount = profile['avg_txn_amount'].iloc[0]
            std_dev = profile['std_dev'].iloc[0]
            # Simple rule: if amount is > 3 * std dev from the mean, it's an anomaly
            is_anomalous = abs(transaction['amount'].iloc[0] - avg_amount) > (std_dev * 3)
            print(f"Rule-based anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for new user {sender_id}.")
            return is_anomalous, 0 # anomaly score 0 indicates no model
        else:
            # For new users, no anomaly can be detected
            return False, 0
    
if __name__ == '__main__':
    # Example usage
    from preprocess import preprocess_pipeline
    
    df = preprocess_pipeline()
    if df is not None:
        user_profiles = build_user_profiles(df)
        user_models = train_anomaly_detectors(df)
        
        # Example new transaction
        new_txn = pd.DataFrame([['c1e0deb4-7c97-4178-a838-38f4a2f0b57c', 'd4a5efcb-4eb6-4d3a-8132-07bb3e6e13a4', 1500, 10, 5, 20]],
                               columns=['Sender_UPI_ID', 'Receiver_UPI_ID', 'amount', 'Transaction_Frequency', 'Days_Since_Last_Transaction', 'hour'])
        
        is_anomalous, score = check_anomaly(new_txn, user_profiles, user_models)
        print(f"Is anomalous: {is_anomalous}, Score: {score}")'''
'''

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
import os
import sqlite3

def retrain_user_profiles():
    print("Retraining user profiles and anomaly models...")
    conn = sqlite3.connect('fraud_detection.db')
    
    # Load all transactions from the database
    all_transactions_df = pd.read_sql_query("SELECT * FROM transactions", conn)
    
    if all_transactions_df.empty:
        print("No transactions in the database to train on.")
        return

    # Build user profiles from the updated data
    user_profiles = all_transactions_df.groupby('sender_upi_id').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('fraud_prediction', 'count'),  # Using count as a proxy for frequency
        timing_norm=('timestamp', lambda x: pd.to_datetime(x).dt.hour.mean()),
        std_dev=('amount', 'std')
    ).reset_index()
    user_profiles.fillna(0, inplace=True)
    user_profiles.rename(columns={'sender_upi_id': 'Sender_UPI_ID'}, inplace=True)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    # Train anomaly models for users with enough data (e.g., > 3 transactions)
    user_models = {}
    user_counts = all_transactions_df['sender_upi_id'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 3].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = all_transactions_df[all_transactions_df['sender_upi_id'] == user_id].copy()
        
        features = ['amount', 'timestamp', 'fraud_prediction'] # Example features
        
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(user_data[features])
        
        # Manually calculate the threshold from the training data
        threshold = np.quantile(model.score_samples(user_data[features]), q=0.05)
        
        # Store the model and its calculated threshold
        user_models[user_id] = {'model': model, 'threshold': threshold}
        
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
    
    print(f"Retrained profiles and models for {len(user_models)} users.")
    conn.close()

def build_user_profiles(df):
    """
    Builds a behavioral profile for each user based on their historical transactions.
    """
    print("Building user behavioral profiles...")
    
    # Group by sender and calculate key statistics
    user_profiles = df.groupby('Sender_UPI_ID').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('Transaction_Frequency', 'mean'),
        timing_norm=('hour', 'mean'),
        std_dev=('amount', 'std')
    ).reset_index()
    
    # Fill NaN values (for users with single transactions)
    user_profiles.fillna(0, inplace=True)
    
    # Create a column for anomaly threshold (e.g., based on std dev)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    # Save profiles for future use
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    print("User behavioral profiles built and saved.")
    return user_profiles

def train_anomaly_detectors(df):
    """
    Trains a separate Isolation Forest model for each user with sufficient data.
    """
    print("Training per-user anomaly detection models...")
    user_models = {}
    
    # Get users with enough data points to train a model
    user_counts = df['Sender_UPI_ID'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 1].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = df[df['Sender_UPI_ID'] == user_id].copy()
        
        # Features for anomaly detection
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        
        if not user_data[features].empty:
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(user_data[features])
            
            # Manually calculate and save the threshold
            threshold = np.quantile(model.score_samples(user_data[features]), q=0.05)
            user_models[user_id] = {'model': model, 'threshold': threshold}
    
    # Save the models
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
        
    print(f"Trained and saved {len(user_models)} per-user anomaly detection models.")
    return user_models

def check_anomaly(transaction, user_profiles, user_models):
    """
    Checks if a new transaction is anomalous for a given user.
    """
    sender_id = transaction['Sender_UPI_ID'].iloc[0]
    
    # Check if a specific model exists for the user
    if sender_id in user_models:
        model_data = user_models[sender_id]
        model = model_data['model']
        threshold = model_data['threshold']
        
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        anomaly_score = model.decision_function(transaction[features])
        
        # The fix is here: using the manually calculated threshold
        is_anomalous = anomaly_score < threshold
        print(f"Anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for user {sender_id}.")
        return is_anomalous.iloc[0], anomaly_score.iloc[0]
    
    # Fallback to a simple rule-based check if no model is trained for the user
    else:
        profile = user_profiles[user_profiles['Sender_UPI_ID'] == sender_id]
        if not profile.empty:
            avg_amount = profile['avg_txn_amount'].iloc[0]
            std_dev = profile['std_dev'].iloc[0]
            # Simple rule: if amount is > 3 * std dev from the mean, it's an anomaly
            is_anomalous = abs(transaction['amount'].iloc[0] - avg_amount) > (std_dev * 3)
            print(f"Rule-based anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for new user {sender_id}.")
            return is_anomalous, 0 # anomaly score 0 indicates no model
        else:
            # For new users, no anomaly can be detected
            return False, 0
    
if __name__ == '__main__':
    # Example usage
    from preprocess import preprocess_pipeline
    
    df = preprocess_pipeline()
    if df is not None:
        user_profiles = build_user_profiles(df)
        user_models = train_anomaly_detectors(df)
        
        # Example new transaction
        new_txn = pd.DataFrame([['c1e0deb4-7c97-4178-a838-38f4a2f0b57c', 'd4a5efcb-4eb6-4d3a-8132-07bb3e6e13a4', 1500, 10, 5, 20]],
                               columns=['Sender_UPI_ID', 'Receiver_UPI_ID', 'amount', 'Transaction_Frequency', 'Days_Since_Last_Transaction', 'hour'])
        
        is_anomalous, score = check_anomaly(new_txn, user_profiles, user_models)
        print(f"Is anomalous: {is_anomalous}, Score: {score}")'''


import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle
import os
import sqlite3

def retrain_user_profiles():
    print("Retraining user profiles and anomaly models...")
    conn = sqlite3.connect('fraud_detection.db')
    
    # Load all transactions from the database
    all_transactions_df = pd.read_sql_query("SELECT * FROM transactions", conn)
    
    if all_transactions_df.empty:
        print("No transactions in the database to train on.")
        return

    # Build user profiles from the updated data
    user_profiles = all_transactions_df.groupby('sender_upi_id').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('fraud_prediction', 'count'),  # Using count as a proxy for frequency
        timing_norm=('timestamp', lambda x: pd.to_datetime(x).dt.hour.mean()),
        std_dev=('amount', 'std')
    ).reset_index()
    user_profiles.fillna(0, inplace=True)
    user_profiles.rename(columns={'sender_upi_id': 'Sender_UPI_ID'}, inplace=True)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    # Train anomaly models for users with enough data (e.g., > 3 transactions)
    user_models = {}
    user_counts = all_transactions_df['sender_upi_id'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 3].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = all_transactions_df[all_transactions_df['sender_upi_id'] == user_id].copy()
        
        features = ['amount', 'timestamp', 'fraud_prediction'] # Example features
        
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(user_data[features])
        
        # Manually calculate the threshold from the training data
        threshold = np.quantile(model.score_samples(user_data[features]), q=0.05)
        
        # Store the model and its calculated threshold
        user_models[user_id] = {'model': model, 'threshold': threshold}
        
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
    
    print(f"Retrained profiles and models for {len(user_models)} users.")
    conn.close()

def build_user_profiles(df):
    """
    Builds a behavioral profile for each user based on their historical transactions.
    """
    print("Building user behavioral profiles...")
    
    # Group by sender and calculate key statistics
    user_profiles = df.groupby('Sender_UPI_ID').agg(
        avg_txn_amount=('amount', 'mean'),
        txn_frequency=('Transaction_Frequency', 'mean'),
        timing_norm=('hour', 'mean'),
        std_dev=('amount', 'std')
    ).reset_index()
    
    # Fill NaN values (for users with single transactions)
    user_profiles.fillna(0, inplace=True)
    
    # Create a column for anomaly threshold (e.g., based on std dev)
    user_profiles['anomaly_threshold'] = user_profiles['std_dev'] * 2
    
    # Save profiles for future use
    user_profiles.to_csv('user_profiles.csv', index=False)
    
    print("User behavioral profiles built and saved.")
    return user_profiles

def train_anomaly_detectors(df):
    """
    Trains a separate Isolation Forest model for each user with sufficient data.
    """
    print("Training per-user anomaly detection models...")
    user_models = {}
    
    # Get users with enough data points to train a model
    user_counts = df['Sender_UPI_ID'].value_counts()
    users_with_enough_data = user_counts[user_counts >= 10].index.tolist()
    
    for user_id in users_with_enough_data:
        user_data = df[df['Sender_UPI_ID'] == user_id].copy()
        
        # Features for anomaly detection
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        
        if not user_data[features].empty:
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(user_data[features])
            
            # Manually calculate and save the threshold
            threshold = np.quantile(model.score_samples(user_data[features]), q=0.05)
            user_models[user_id] = {'model': model, 'threshold': threshold}
    
    # Save the models
    with open('models/user_anomaly_models.pkl', 'wb') as f:
        pickle.dump(user_models, f)
        
    print(f"Trained and saved {len(user_models)} per-user anomaly detection models.")
    return user_models

def check_anomaly(transaction, user_profiles, user_models):
    """
    Checks if a new transaction is anomalous for a given user.
    """
    sender_id = transaction['Sender_UPI_ID'].iloc[0]
    
    # Check if a specific model exists for the user
    if sender_id in user_models:
        model_data = user_models[sender_id]
        model = model_data['model']
        threshold = model_data['threshold']
        
        features = ['amount', 'hour', 'Days_Since_Last_Transaction']
        anomaly_score = model.decision_function(transaction[features])
        
        # The fix is here: using the manually calculated threshold
        is_anomalous = anomaly_score < threshold
        print(f"Anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for user {sender_id}.")
        
        # Corrected line: Access the elements of the NumPy arrays using brackets
        return is_anomalous[0], anomaly_score[0]
    
    # Fallback to a simple rule-based check if no model is trained for the user
    else:
        profile = user_profiles[user_profiles['Sender_UPI_ID'] == sender_id]
        if not profile.empty:
            avg_amount = profile['avg_txn_amount'].iloc[0]
            std_dev = profile['std_dev'].iloc[0]
            # Simple rule: if amount is > 3 * std dev from the mean, it's an anomaly
            is_anomalous = abs(transaction['amount'].iloc[0] - avg_amount) > (std_dev * 3)
            print(f"Rule-based anomaly check: {'Anomalous' if is_anomalous else 'Normal'} transaction for new user {sender_id}.")
            return is_anomalous, 0 # anomaly score 0 indicates no model
        else:
            # For new users, no anomaly can be detected
            return False, 0
    
if __name__ == '__main__':
    # Example usage
    from preprocess import preprocess_pipeline
    
    df = preprocess_pipeline()
    if df is not None:
        user_profiles = build_user_profiles(df)
        user_models = train_anomaly_detectors(df)
        
        # Example new transaction
        new_txn = pd.DataFrame([['c1e0deb4-7c97-4178-a838-38f4a2f0b57c', 'd4a5efcb-4eb6-4d3a-8132-07bb3e6e13a4', 1500, 10, 5, 20]],
                               columns=['Sender_UPI_ID', 'Receiver_UPI_ID', 'amount', 'Transaction_Frequency', 'Days_Since_Last_Transaction', 'hour'])
        
        is_anomalous, score = check_anomaly(new_txn, user_profiles, user_models)
        print(f"Is anomalous: {is_anomalous}, Score: {score}")