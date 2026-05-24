import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler

def build_generator(latent_dim, n_features):
    model = Sequential()
    model.add(Dense(128, input_dim=latent_dim, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(n_features, activation='linear')) # Output layer for features
    return model

def build_discriminator(n_features):
    model = Sequential()
    model.add(Dense(256, input_dim=n_features, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(1, activation='sigmoid')) # Output layer for real/fake classification
    return model

def generate_synthetic_data(df, n_samples=475):
    print("Starting synthetic data generation...")
    fraud_df = df[df['fraud'] == 1].copy()
    if fraud_df.empty:
        print("Warning: No fraudulent transactions found. Using SMOTE instead.")
        X = df.drop('fraud', axis=1)
        y = df['fraud']
        smote = SMOTE(random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        synthetic_data = X_resampled[y_resampled == 1].copy()
        synthetic_data['fraud'] = 1
        synthetic_data['is_synthetic'] = 1
        return synthetic_data
    real_sender_ids = fraud_df['Sender_UPI_ID'].unique()
    real_receiver_ids = fraud_df['Receiver_UPI_ID'].unique()
    X_fraud = fraud_df.drop(['Sender_UPI_ID', 'Receiver_UPI_ID', 'fraud'], axis=1)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_fraud)
    latent_dim = 100
    n_features = X_scaled.shape[1]
    generator = build_generator(latent_dim, n_features)
    discriminator = build_discriminator(n_features)
    discriminator.compile(loss='binary_crossentropy', optimizer='adam')
    discriminator.trainable = False
    gan = Sequential()
    gan.add(generator)
    gan.add(discriminator)
    gan.compile(loss='binary_crossentropy', optimizer='adam')
    epochs = 100
    batch_size = 32
    print(f"Training GAN for {epochs} epochs...")
    for epoch in range(epochs):
        noise = np.random.normal(0, 1, size=(batch_size, latent_dim))
        gen_data = generator.predict(noise)
        real_data = X_scaled[np.random.randint(0, X_scaled.shape[0], batch_size)]
        X_combined = np.concatenate([real_data, gen_data])
        y_discriminator = np.concatenate([np.ones((batch_size, 1)), np.zeros((batch_size, 1))])
        d_loss = discriminator.train_on_batch(X_combined, y_discriminator)
        noise = np.random.normal(0, 1, size=(batch_size, latent_dim))
        y_gan = np.ones((batch_size, 1))
        g_loss = gan.train_on_batch(noise, y_gan)
    print("GAN training complete.")
    noise = np.random.normal(0, 1, size=(n_samples, latent_dim))
    synthetic_features = generator.predict(noise)
    synthetic_features = scaler.inverse_transform(synthetic_features)
    synthetic_df = pd.DataFrame(synthetic_features, columns=X_fraud.columns)
    # Assign real IDs to synthetic data
    synthetic_df['Sender_UPI_ID'] = np.random.choice(real_sender_ids, n_samples)
    synthetic_df['Receiver_UPI_ID'] = np.random.choice(real_receiver_ids, n_samples)
    synthetic_df['is_synthetic'] = 1
    synthetic_df['fraud'] = 1
    print(f"Generated {n_samples} synthetic fraud samples.")
    return synthetic_df

if __name__ == '__main__':
    from preprocess import preprocess_pipeline
    
    # Note: For running this standalone, you'll need the original dataset and preprocessing
    df = preprocess_pipeline()
    if df is not None:
        synthetic_df = generate_synthetic_data(df)
        print("\nSynthetic Data Head:")
        print(synthetic_df.head())
        print("\nSynthetic Data Info:")
        synthetic_df.info()
        print(f"- All fraud labels: {synthetic_df['fraud'].all()}")
        print(f"- Feature count: {len(synthetic_df.columns)}")
        print(f"- Missing values: {synthetic_df.isnull().sum().sum()}")

        # Save synthetic data
        synthetic_df.to_csv("synthetic_fraud_data_1.csv", index=False)
        #logger.info("Synthetic fraud data saved to synthetic_fraud_data.csv")