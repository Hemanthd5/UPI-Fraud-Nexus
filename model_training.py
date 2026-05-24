"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from imblearn.over_sampling import SMOTE
import pickle
import shap
import matplotlib.pyplot as plt
import os

def train_models(df):

    print("Starting model training...")
    
    # Separate features and target
    X = df.drop(['Sender_UPI_ID', 'Receiver_UPI_ID', 'fraud'], axis=1)
    y = df['fraud']
    
    # Apply SMOTE to balance the dataset
    print("Applying SMOTE to balance the dataset...")
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    print("Dataset balanced. Original shape:", X.shape, "Resampled shape:", X_resampled.shape)

    # Split resampled data
    X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled)
    
    # Train Random Forest
    print("Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Evaluate models Random forest
    print("\nModel Evaluation:")
    y_pred_rf = rf_model.predict(X_test)
    y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
    
    print("Random Forest Metrics:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred_rf):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred_rf):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba_rf):.4f}")
    
    # Train XGBoost
    print("Training XGBoost Classifier...")
    xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    
    # Evaluate models
    print("\nModel Evaluation:")
    y_pred_xgb = xgb_model.predict(X_test)
    y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
    
    print("XGBoost Metrics:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred_xgb):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred_xgb):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba_xgb):.4f}")

    # Save the models
    if not os.path.exists('models'):
        os.makedirs('models')
    with open('models/rf_model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    with open('models/xgb_model.pkl', 'wb') as f:
        pickle.dump(xgb_model, f)

    # Explainability with SHAP for Random Forest
    print("\nGenerating SHAP explanation plot...")
    explainer = shap.TreeExplainer(rf_model)
    shap_values = explainer.shap_values(X_test)
    
    shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig('shap_summary_plot1.png')
    print("SHAP plot saved as shap_summary_plot1.png.")

    print("Model training and evaluation complete.")
    return rf_model
        
    # Explainability with SHAP for XGBoost
    print("\nGenerating SHAP explanation plot...")
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_test)
    
    shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig('shap_summary_plot2.png')
    print("SHAP plot saved as shap_summary_plot2.png.")

    print("Model training and evaluation complete.")
    return xgb_model


def predict_fraud(model, transaction, threshold=0.5):

    proba = model.predict_proba(transaction)[0][1]
    prediction = 1 if proba >= threshold else 0
    return prediction, proba

if __name__ == '__main__':
    from preprocess import preprocess_pipeline
    
    df = preprocess_pipeline()
    if df is not None:
        xgb = train_models(df)
        print("\nModels trained and saved.")
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
import pickle
import os
import time
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from imblearn.over_sampling import SMOTE


def train_models(df):
    print("Starting model training...")
    X = df.drop(['Sender_UPI_ID', 'Receiver_UPI_ID', 'fraud'], axis=1)
    y = df['fraud']
    print("Applying SMOTE to balance the dataset...")
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    print("Dataset balanced. Original shape:", X.shape, "Resampled shape:", X_resampled.shape)
    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled
    )
    #  RANDOM FOREST
    print("\n🔹 Training Random Forest Classifier...")
    start_time = time.time()
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_train_time = time.time() - start_time
    print(f"Random Forest Training Time: {rf_train_time:.2f} seconds")
    y_pred_rf = rf_model.predict(X_test)
    y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
    print("\nRandom Forest Metrics:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred_rf):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred_rf):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred_rf):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba_rf):.4f}")
    print("Plotting Random Forest Accuracy Curve...")
    n_trees = [10, 30, 50, 70, 100, 150, 200]
    acc_values = []
    for n in n_trees:
        rf_temp = RandomForestClassifier(n_estimators=n, random_state=42)
        rf_temp.fit(X_train, y_train)
        y_pred_temp = rf_temp.predict(X_test)
        acc_values.append(accuracy_score(y_test, y_pred_temp))
    plt.figure(figsize=(7, 5))
    plt.plot(n_trees, acc_values, marker='o')
    plt.title("Random Forest Accuracy vs Number of Trees")
    plt.xlabel("Number of Trees")
    plt.ylabel("Accuracy")
    plt.grid(True)
    plt.savefig('rf_accuracy_curve.png')
    print("Random Forest accuracy curve saved as rf_accuracy_curve.png.")
    # XGBOOST
    print("\n🔹 Training XGBoost Classifier with evaluation...")
    start_time = time.time()
    xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    eval_set = [(X_train, y_train), (X_test, y_test)]
    xgb_model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
    xgb_train_time = time.time() - start_time
    print(f"XGBoost Training Time: {xgb_train_time:.2f} seconds")
    y_pred_xgb = xgb_model.predict(X_test)
    y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
    print("\nXGBoost Metrics:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred_xgb):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred_xgb):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred_xgb):.4f}")
    print(f"AUC: {roc_auc_score(y_test, y_proba_xgb):.4f}")
    results = xgb_model.evals_result()
    epochs = len(results['validation_0']['logloss'])
    x_axis = range(0, epochs)
    plt.figure(figsize=(7, 5))
    plt.plot(x_axis, results['validation_0']['logloss'], label='Train')
    plt.plot(x_axis, results['validation_1']['logloss'], label='Test')
    plt.title("XGBoost Log Loss Over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("Log Loss")
    plt.legend()
    plt.grid(True)
    plt.savefig('xgb_loss_curve.png')
    print("XGBoost loss curve saved as xgb_loss_curve.png.")
    if not os.path.exists('models'):
        os.makedirs('models')
    with open('models/rf_model_1.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    with open('models/xgb_model_1.pkl', 'wb') as f:
        pickle.dump(xgb_model, f)
    #  SHAP Explainability
    print("\nGenerating SHAP explanation plot...")
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_test)
    shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig('shap_summary_plot.png')
    print("SHAP plot saved as shap_summary_plot.png.")
    print("\n✅ Model training, evaluation, and visualization complete.")
    return rf_model, xgb_model
# HYPERPARAMETER TUNING
def tune_models(X, y):
    print("\nStarting hyperparameter tuning...")
    start_time = time.time()
    rf_param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    rf_grid = GridSearchCV(
        RandomForestClassifier(random_state=42),
        rf_param_grid,
        cv=3,
        scoring='f1',
        n_jobs=-1,
        verbose=1
    )
    rf_grid.fit(X, y)
    print("\nBest Random Forest Params:", rf_grid.best_params_)

    # XGBoost Grid
    xgb_param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    xgb_grid = GridSearchCV(
        XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
        xgb_param_grid,
        cv=3,
        scoring='f1',
        n_jobs=-1,
        verbose=1
    )
    xgb_grid.fit(X, y)
    print("\nBest XGBoost Params:", xgb_grid.best_params_)

    total_time = time.time() - start_time
    print(f"\nTotal Hyperparameter Tuning Time: {total_time/60:.2f} minutes")

    return rf_grid.best_estimator_, xgb_grid.best_estimator_


# ---------------- PREDICT FUNCTION ---------------- #
def predict_fraud(model, transaction, threshold=0.5):
    #Predicts fraud for a single transaction based on a given threshold.
    proba = model.predict_proba(transaction)[0][1]
    prediction = 1 if proba >= threshold else 0
    return prediction, proba


# ---------------- MAIN EXECUTION ---------------- #
if __name__ == '__main__':
    from preprocess import preprocess_pipeline

    df, encoders = preprocess_pipeline()
    if df is not None:
        rf, xgb = train_models(df)

        # Tune models (optional, time-consuming)
        X = df.drop(['Sender_UPI_ID', 'Receiver_UPI_ID', 'fraud'], axis=1)
        y = df['fraud']
        tune_models(X, y)
