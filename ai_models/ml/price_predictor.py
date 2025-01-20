# models/ml/price_predictor.py

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class PricePredictor:
    def __init__(
        self, 
        sequence_length: int = 60,
        n_features: int = 20,
        n_lstm_layers: int = 2,
        n_lstm_nodes: int = 50,
        dropout_rate: float = 0.2
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.n_lstm_layers = n_lstm_layers
        self.n_lstm_nodes = n_lstm_nodes
        self.dropout_rate = dropout_rate

    def build_model(self) -> None:
        """Build LSTM model architecture"""
        try:
            model = tf.keras.Sequential()
            
            # First LSTM layer
            model.add(tf.keras.layers.LSTM(
                units=self.n_lstm_nodes,
                return_sequences=True if self.n_lstm_layers > 1 else False,
                input_shape=(self.sequence_length, self.n_features)
            ))
            model.add(tf.keras.layers.Dropout(self.dropout_rate))
            
            # Additional LSTM layers
            for i in range(self.n_lstm_layers - 1):
                model.add(tf.keras.layers.LSTM(
                    units=self.n_lstm_nodes,
                    return_sequences=True if i < self.n_lstm_layers - 2 else False
                ))
                model.add(tf.keras.layers.Dropout(self.dropout_rate))
            
            # Dense layers
            model.add(tf.keras.layers.Dense(25, activation='relu'))
            model.add(tf.keras.layers.Dense(1))
            
            # Compile model
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            self.model = model
            logger.info("Model built successfully")
            
        except Exception as e:
            logger.error(f"Error building model: {str(e)}")
            raise

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str = 'close'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training"""
        try:
            # Scale target
            target_data = df[target_column].values.reshape(-1, 1)
            scaled_target = self.price_scaler.fit_transform(target_data)
            
            # Scale features
            feature_data = df.drop(columns=[target_column]).values
            scaled_features = self.feature_scaler.fit_transform(feature_data)
            
            # Create sequences
            X, y = [], []
            for i in range(len(df) - self.sequence_length):
                X.append(scaled_features[i:(i + self.sequence_length)])
                y.append(scaled_target[i + self.sequence_length])
                
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32,
        early_stopping_patience: int = 10,
        verbose: int = 1
    ) -> tf.keras.callbacks.History:
        """Train the model"""
        try:
            if self.model is None:
                self.build_model()
                
            # Early stopping callback
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=early_stopping_patience,
                restore_best_weights=True
            )
            
            # Model checkpoint callback
            checkpoint = tf.keras.callbacks.ModelCheckpoint(
                'best_model.h5',
                monitor='val_loss',
                save_best_only=True,
                save_weights_only=True
            )
            
            # Train model
            history = self.model.fit(
                X_train, y_train,
                validation_split=validation_split,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[early_stopping, checkpoint],
                verbose=verbose
            )
            
            logger.info("Model training completed")
            return history
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict(
        self, 
        X: np.ndarray,
        return_scaled: bool = False
    ) -> np.ndarray:
        """Make predictions"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
                
            predictions = self.model.predict(X)
            
            if return_scaled:
                return predictions
            
            return self.price_scaler.inverse_transform(predictions)
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise

    def predict_next_n_prices(
        self,
        current_sequence: np.ndarray,
        n_steps: int = 5
    ) -> List[float]:
        """Predict next n price values"""
        try:
            predictions = []
            curr_seq = current_sequence.copy()
            
            for _ in range(n_steps):
                # Get prediction for next step
                next_pred = self.predict(
                    curr_seq.reshape(1, self.sequence_length, self.n_features),
                    return_scaled=True
                )
                predictions.append(float(next_pred[0, 0]))
                
                # Update sequence
                curr_seq = np.roll(curr_seq, -1, axis=0)
                curr_seq[-1, 0] = next_pred[0, 0]  # Update last row
                
            # Inverse transform all predictions at once
            predictions = np.array(predictions).reshape(-1, 1)
            return self.price_scaler.inverse_transform(predictions).flatten().tolist()
            
        except Exception as e:
            logger.error(f"Error predicting future prices: {str(e)}")
            raise

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> dict:
        """Evaluate model performance"""
        try:
            # Get predictions
            y_pred = self.predict(X_test)
            y_true = self.price_scaler.inverse_transform(y_test)
            
            # Calculate metrics
            mse = np.mean((y_true - y_pred) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_true - y_pred))
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            
            return {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def save_model(self, path: str) -> None:
        """Save model to file"""
        try:
            if self.model is None:
                raise ValueError("No model to save")
                
            self.model.save(path)
            logger.info(f"Model saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self, path: str) -> None:
        """Load model from file"""
        try:
            self.model = tf.keras.models.load_model(path)
            logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise