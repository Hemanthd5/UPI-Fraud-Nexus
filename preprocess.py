'''import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

def load_data(file_path='UPI_Dataset.csv'):
    """
    Loads the dataset from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        print("Dataset loaded successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None

def clean_data(df):
    """
    Cleans the dataframe by handling missing values.
    """
    # Fill missing string values with 'Unknown'
    df.fillna('Unknown', inplace=True)
    # Fill missing numerical values with the mean
    for col in df.select_dtypes(include=np.number).columns:
        df[col].fillna(df[col].mean(), inplace=True)
    print("Data cleaned.")
    return df

def feature_engineering(df):
    """
    Performs feature engineering to create new features.
    """
    # Convert 'Date' and 'Time' to datetime objects
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df['hour'] = df['Datetime'].dt.hour
    df['day_of_week'] = df['Datetime'].dt.dayofweek
    df.drop(['Date', 'Time', 'Datetime'], axis=1, inplace=True)
    print("Feature engineering complete.")
    return df

def encode_data(df):
    """
    Encodes categorical features.
    """
    # Identify categorical columns (exclude IDs and 'fraud')
    categorical_cols = [
        'Transaction_Type', 'Payment_Gateway', 'Transaction_City',
        'Transaction_State', 'Transaction_Status', 'Device_OS',
        'Merchant_Category', 'Transaction_Channel'
    ]
    
    # Label encode for initial handling (will use one-hot for model)
    le = LabelEncoder()
    for col in categorical_cols:
        df[col] = le.fit_transform(df[col])
    print("Categorical data encoded.")
    return df

def preprocess_pipeline(file_path='UPI_Dataset.csv'):
    """
    Runs the full preprocessing pipeline.
    """
    df = load_data(file_path)
    if df is None:
        return None
    
    # Rename columns for clarity as per user request
    df.rename(columns={
        'Customer_ID': 'Sender_UPI_ID',
        'Merchant_ID': 'Receiver_UPI_ID'
    }, inplace=True)
    
    df = clean_data(df)
    df = feature_engineering(df)
    df = encode_data(df)
    
    # Drop columns not needed for modeling
    df.drop(['Transaction_ID', 'Device_ID', 'IP_Address'], axis=1, inplace=True)
    
    return df

if __name__ == '__main__':
    # Example usage
    preprocessed_df = preprocess_pipeline()
    if preprocessed_df is not None:
        print("\nPreprocessed Data:")
        print(preprocessed_df.head())
        print("\nData Info:")
        preprocessed_df.info()'''


import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import pickle
import os

def load_data(file_path='UPI_Dataset.csv'):

    try:
        df = pd.read_csv(file_path)
        print("Dataset loaded successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None

def clean_data(df):


    for col in df.select_dtypes(include=['object']).columns:
        df[col].fillna('Unknown', inplace=True)
    
    # Fill missing numerical values with the mean
    for col in df.select_dtypes(include=np.number).columns:
        df[col].fillna(df[col].mean(), inplace=True)
        
    print("Data cleaned.")
    return df

def feature_engineering(df):

    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df['hour'] = df['Datetime'].dt.hour
    df['day_of_week'] = df['Datetime'].dt.dayofweek
    df.drop(['Date', 'Time', 'Datetime'], axis=1, inplace=True)
    print("Feature engineering complete.")
    return df

def encode_data(df):

    categorical_cols = [
        'Transaction_Type', 'Payment_Gateway', 'Transaction_City',
        'Transaction_State', 'Transaction_Status', 'Device_OS',
        'Merchant_Category', 'Transaction_Channel'
    ]
    encoders = {}
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = df[col].astype(str)
            all_values = list(df[col].unique())
            if 'Unknown' not in all_values:
                all_values.append('Unknown')
            le.fit(all_values)
            df[col] = le.transform(df[col])
            encoders[col] = le

    if not os.path.exists('models'):
        os.makedirs('models')
    with open('models/label_encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)
    print("Categorical data encoded and encoders saved.")
    return df, encoders

def preprocess_pipeline(file_path='UPI_Dataset.csv'):

    df = load_data(file_path)
    if df is None:
        return None, None
    df.rename(columns={
        'Customer_ID': 'Sender_UPI_ID',
        'Merchant_ID': 'Receiver_UPI_ID'
    }, inplace=True)
    df = clean_data(df)
    df = feature_engineering(df)
    df, encoders = encode_data(df)
    df.drop(['Transaction_ID', 'Device_ID', 'IP_Address'], axis=1, inplace=True, errors='ignore')
    return df, encoders

if __name__ == '__main__':
    # Update main block to capture both values
    preprocessed_df, label_encoders = preprocess_pipeline()
    
    if preprocessed_df is not None:
        print("\nPreprocessed Data:")
        print(preprocessed_df.head())
        print("\nData Info:")
        preprocessed_df.info()
        print("\nSaved Encoders:")
        print(label_encoders.keys())