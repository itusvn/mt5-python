# models/services/ai_model_service.py

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from ..ml.price_predictor import PricePredictor
from ..ml.trend_classifier import TrendClassifier
from ..rl.agent import TradingRL
from ..ml.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.price_predictor = PricePredictor()
        self.trend_classifier = TrendClassifier()
        self.trading_rl = None
        
        # Model states
        self.models_loaded = {
            'price_predictor': False,
            'trend_classifier': False,
            'trading_rl': False
        }

    def load_models(self, model_paths: Dict[str, str]) -> None:
        """Load all models from saved files"""
        try:
            if 'price_predictor' in model_paths:
                self.price_predictor.load_model(model_paths['price_predictor'])
                self.models_loaded['price_predictor'] = True
                
            if 'trend_classifier' in model_paths:
                self.trend_classifier.load_model(model_paths['trend_classifier'])
                self.models_loaded['trend_classifier'] = True
                
            if 'trading_rl' in model_paths:
                # Initialize RL agent with dummy data first
                dummy_data = np.zeros((100, self.feature_engineer.n_features))
                self.trading_rl = TradingRL(dummy_data)
                self.trading_rl.agent.load(model_paths['trading_rl'])
                self.models_loaded['trading_rl'] = True
                
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise

    def prepare_prediction_data(
        self,
        data: pd.DataFrame,
        sequence_length: int = 60
    ) -> np.ndarray:
        """Prepare data for predictions"""
        try:
            # Engineer features
            featured_data = self.feature_engineer.create_features(data)
            
            # Create sequence
            if len(featured_data) < sequence_length:
                raise ValueError(f"Not enough data points. Need at least {sequence_length}")
                
            sequence = featured_data.iloc[-sequence_length:].values
            
            return sequence
            
        except Exception as e:
            logger.error(f"Error preparing prediction data: {str(e)}")
            raise

    def get_predictions(
        self,
        data: pd.DataFrame,
        prediction_type: str = 'all'
    ) -> Dict[str, Any]:
        """Get predictions from all or specific models"""
        try:
            sequence = self.prepare_prediction_data(data)
            predictions = {}
            
            if prediction_type in ['all', 'price'] and self.models_loaded['price_predictor']:
                price_preds = self.price_predictor.predict_next_n_prices(
                    sequence,
                    n_steps=5
                )
                predictions['price_predictions'] = price_preds
                
            if prediction_type in ['all', 'trend'] and self.models_loaded['trend_classifier']:
                trend_probs = self.trend_classifier.predict(
                    sequence.reshape(1, -1),
                    return_probabilities=True
                )
                predictions['trend_probabilities'] = trend_probs[0]
                predictions['trend_signals'] = self.trend_classifier.get_trend_signals(trend_probs)
                
            if prediction_type in ['all', 'rl'] and self.models_loaded['trading_rl']:
                rl_action = self.trading_rl.agent.act(
                    sequence[-1],
                    eval_mode=True
                )
                predictions['rl_action'] = ['HOLD', 'BUY', 'SELL'][rl_action]
                
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions: {str(e)}")
            raise

    def aggregate_signals(
        self,
        predictions: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Aggregate signals from different models"""
        try:
            if weights is None:
                weights = {
                    'trend': 0.4,
                    'price': 0.3,
                    'rl': 0.3
                }
                
            signal_scores = {
                'BUY': 0.0,
                'SELL': 0.0,
                'HOLD': 0.0
            }
            
            # Process trend signals
            if 'trend_probabilities' in predictions:
                trend_probs = predictions['trend_probabilities']
                signal_scores['HOLD'] += weights['trend'] * trend_probs[0]
                signal_scores['BUY'] += weights['trend'] * trend_probs[1]
                signal_scores['SELL'] += weights['trend'] * trend_probs[2]
                
            # Process price predictions
            if 'price_predictions' in predictions:
                price_preds = predictions['price_predictions']
                current_price = predictions.get('current_price', price_preds[0])
                price_change = (price_preds[-1] - current_price) / current_price
                
                if abs(price_change) > 0.001:  # 0.1% threshold
                    if price_change > 0:
                        signal_scores['BUY'] += weights['price']
                    else:
                        signal_scores['SELL'] += weights['price']
                else:
                    signal_scores['HOLD'] += weights['price']
                    
            # Process RL signals
            if 'rl_action' in predictions:
                rl_action = predictions['rl_action']
                signal_scores[rl_action] += weights['rl']
                
            # Get final signal
            final_signal = max(signal_scores.items(), key=lambda x: x[1])
            confidence = final_signal[1] / sum(weights.values())
            
            return {
                'signal': final_signal[0],
                'confidence': confidence,
                'scores': signal_scores,
                'individual_signals': {
                    'trend': predictions.get('trend_signals', [None])[0],
                    'price': 'BUY' if price_change > 0.001 else 'SELL' if price_change < -0.001 else 'HOLD',
                    'rl': predictions.get('rl_action')
                }
            }
            
        except Exception as e:
            logger.error(f"Error aggregating signals: {str(e)}")
            raise

    def validate_signal(
        self,
        signal: Dict[str, Any],
        min_confidence: float = 0.6
    ) -> bool:
        """Validate trading signal"""
        try:
            # Check confidence threshold
            if signal['confidence'] < min_confidence:
                return False
                
            # Check signal agreement
            signals = signal['individual_signals'].values()
            if len(set(signals)) == len(signals):  # All signals different
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            raise

    def get_position_sizing(
        self,
        signal: Dict[str, Any],
        account_balance: float,
        risk_per_trade: float = 0.02
    ) -> float:
        """Calculate position size based on signal confidence"""
        try:
            base_position = account_balance * risk_per_trade
            confidence_factor = signal['confidence']
            
            # Adjust position size based on confidence
            position_size = base_position * confidence_factor
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            raise

    def update_models(
        self,
        model_paths: Dict[str, str]
    ) -> None:
        """Update models with new versions"""
        try:
            self.load_models(model_paths)
            logger.info("Models updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating models: {str(e)}")
            raise