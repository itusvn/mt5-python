# models/ml/trend_classifier.py

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import logging

logger = logging.getLogger(__name__)

class TrendClassifier:
    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 20,
        n_classes: int = 3,  # Up, Down, Sideways
        trend_threshold: float = 0.001  # 0.1% change threshold
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.n_classes = n_classes
        self.trend_threshold = trend_threshold
        self.model = None
        self.feature_scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

    def build_model(self) -> None:
        """Build CNN-LSTM hybrid model"""
        try:
            model = tf.keras.Sequential([
                # CNN layers
                tf.keras.layers.Conv1D(
                    filters=64,
                    kernel_size=3,
                    activation='relu',
                    input_shape=(self.sequence_length, self.n_features)
                ),
                tf.keras.layers.MaxPooling1D(pool_size=2),
                tf.keras.layers.Dropout(0.2),
                
                tf.keras.layers.Conv1D(
                    filters=128,
                    kernel_size=3,
                    activation='relu'
                ),
                tf.keras.layers.MaxPooling1D(pool_size=2),
                tf.keras.layers.Dropout(0.2),
                
                # LSTM layers
                tf.keras.layers.LSTM(100, return_sequences=True),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.LSTM(50),
                tf.keras.layers.Dropout(0.2),
                
                # Dense layers
                tf.keras.layers.Dense(50, activation='relu'),
                tf.keras.layers.Dense(self.n_classes, activation='softmax')
            ])

            # Compile model
            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            self.model = model
            logger.info("Model built successfully")

        except Exception as e:
            logger.error(f"Error building model: {str(e)}")
            raise

    def create_labels(self, prices: np.ndarray) -> np.ndarray:
        """Create trend labels from price data"""
        try:
            returns = np.diff(prices) / prices[:-1]
            labels = np.zeros(len(returns))
            
            # Create labels based on returns
            labels[returns > self.trend_threshold] = 1  # Uptrend
            labels[returns < -self.trend_threshold] = 2  # Downtrend
            # 0 remains for sideways
            
            # Pad first element
            labels = np.pad(labels, (1, 0), 'constant', constant_values=0)
            
            return labels

        except Exception as e:
            logger.error(f"Error creating labels: {str(e)}")
            raise

    def prepare_data(
        self,
        df: pd.DataFrame,
        price_column: str = 'close'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences and labels for training"""
        try:
            # Scale features
            feature_data = df.drop(columns=[price_column]).values
            scaled_features = self.feature_scaler.fit_transform(feature_data)
            
            # Create labels
            labels = self.create_labels(df[price_column].values)
            encoded_labels = self.label_encoder.fit_transform(labels)
            
            # Create sequences
            X, y = [], []
            for i in range(len(df) - self.sequence_length):
                X.append(scaled_features[i:(i + self.sequence_length)])
                y.append(encoded_labels[i + self.sequence_length])
                
            # Convert to categorical
            y = tf.keras.utils.to_categorical(y, num_classes=self.n_classes)
            
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
        class_weights: Optional[Dict] = None
    ) -> tf.keras.callbacks.History:
        """Train the model"""
        try:
            if self.model is None:
                self.build_model()

            # Callbacks
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001
                )
            ]

            # Train model
            history = self.model.fit(
                X_train, y_train,
                validation_split=validation_split,
                epochs=epochs,
                batch_size=batch_size,
                class_weight=class_weights,
                callbacks=callbacks,
                verbose=1
            )

            logger.info("Model training completed")
            return history

        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict(
        self,
        X: np.ndarray,
        return_probabilities: bool = False
    ) -> np.ndarray:
        """Make predictions"""
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")

            predictions = self.model.predict(X)
            
            if return_probabilities:
                return predictions
                
            # Convert to class labels
            class_predictions = np.argmax(predictions, axis=1)
            return self.label_encoder.inverse_transform(class_predictions)

        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """Evaluate model performance"""
        try:
            # Get predictions
            y_pred = self.predict(X_test)
            y_true = np.argmax(y_test, axis=1)
            y_true = self.label_encoder.inverse_transform(y_true)
            
            # Calculate metrics
            report = classification_report(
                y_true,
                y_pred,
                target_names=['Sideways', 'Up', 'Down'],
                output_dict=True
            )
            
            conf_matrix = confusion_matrix(y_true, y_pred)
            
            # Calculate additional metrics
            accuracy = (y_true == y_pred).mean()
            
            trend_accuracy = np.mean(
                (y_true != 0) & (y_pred != 0) & (y_true == y_pred)
            )
            
            return {
                'classification_report': report,
                'confusion_matrix': conf_matrix,
                'accuracy': accuracy,
                'trend_accuracy': trend_accuracy
            }

        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def get_trend_signals(
        self,
        probabilities: np.ndarray,
        threshold: float = 0.7
    ) -> list:
        """Get trading signals from predictions"""
        signals = []
        
        for prob in probabilities:
            if prob[1] > threshold:  # Strong uptrend
                signals.append('BUY')
            elif prob[2] > threshold:  # Strong downtrend
                signals.append('SELL')
            else:
                signals.append('HOLD')
                
        return signals

    def save_model(self, path: str) -> None:
        """Save model to file"""
        try:
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