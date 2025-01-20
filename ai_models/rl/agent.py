# models/rl/agent.py

import numpy as np
import tensorflow as tf
from collections import deque
import random
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

class TradingEnvironment:
    def __init__(
        self,
        data: np.ndarray,
        initial_balance: float = 10000,
        transaction_fee: float = 0.001
    ):
        self.data = data
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.reset()
        
    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.trades = []
        self.returns = []
        return self._get_state()
        
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """Take action and move to next step"""
        # Get current price info
        current_price = self.data[self.current_step]
        
        # Calculate reward based on action
        reward = self._calculate_reward(action, current_price)
        
        # Execute trade
        self._execute_trade(action, current_price)
        
        # Move to next step
        done = self.current_step >= len(self.data) - 1
        if not done:
            self.current_step += 1
            
        # Get new state
        next_state = self._get_state()
        
        # Get additional info
        info = {
            'balance': self.balance,
            'position': self.position,
            'trades': len(self.trades)
        }
        
        return next_state, reward, done, info
        
    def _get_state(self) -> np.ndarray:
        """Get current state of environment"""
        # Get price/indicator features
        price_features = self.data[self.current_step]
        
        # Add position and balance info
        state = np.append(price_features, [
            self.position,
            self.balance / self.initial_balance
        ])
        
        return state
        
    def _calculate_reward(self, action: int, current_price: float) -> float:
        """Calculate reward for action"""
        reward = 0
        
        if action == 0:  # HOLD
            if self.position != 0:  # If in position
                price_change = current_price - self.trades[-1]['price']
                reward = price_change if self.position == 1 else -price_change
                
        elif action == 1:  # BUY
            if self.position == -1:  # Close short
                price_change = self.trades[-1]['price'] - current_price
                reward = price_change * (1 - self.transaction_fee)
                
        elif action == 2:  # SELL
            if self.position == 1:  # Close long
                price_change = current_price - self.trades[-1]['price']
                reward = price_change * (1 - self.transaction_fee)
                
        return reward
        
    def _execute_trade(self, action: int, current_price: float) -> None:
        """Execute trading action"""
        if action == 1:  # BUY
            if self.position <= 0:
                self.trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'step': self.current_step
                })
                self.position = 1
                
        elif action == 2:  # SELL
            if self.position >= 0:
                self.trades.append({
                    'type': 'SELL',
                    'price': current_price,
                    'step': self.current_step
                })
                self.position = -1

class DQNAgent:
    def __init__(
        self,
        state_size: int,
        action_size: int = 3,  # HOLD, BUY, SELL
        memory_size: int = 10000,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        learning_rate: float = 0.001,
        batch_size: int = 32
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=memory_size)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        
        # Create main and target networks
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
    def _build_model(self) -> tf.keras.Model:
        """Build neural network model"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, input_dim=self.state_size, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        
        model.compile(
            loss='mse',
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
        )
        
        return model
        
    def update_target_model(self) -> None:
        """Update target model weights"""
        self.target_model.set_weights(self.model.get_weights())
        
    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ) -> None:
        """Store experience in memory"""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state: np.ndarray, eval_mode: bool = False) -> int:
        """Choose action based on epsilon-greedy policy"""
        if not eval_mode and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
            
        act_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(act_values[0])
        
    def replay(self) -> float:
        """Train on experiences in memory"""
        if len(self.memory) < self.batch_size:
            return 0
            
        # Sample random batch from memory
        minibatch = random.sample(self.memory, self.batch_size)
        
        states = np.zeros((self.batch_size, self.state_size))
        next_states = np.zeros((self.batch_size, self.state_size))
        
        # Fill state arrays
        for i, (state, _, _, next_state, _) in enumerate(minibatch):
            states[i] = state
            next_states[i] = next_state
            
        # Predict Q-values
        target_next = self.target_model.predict(next_states, verbose=0)
        target_curr = self.model.predict(states, verbose=0)
        
        # Update target Q-values
        for i, (state, action, reward, _, done) in enumerate(minibatch):
            if done:
                target = reward
            else:
                target = reward + self.gamma * np.amax(target_next[i])
            target_curr[i][action] = target
            
        # Train model
        history = self.model.fit(
            states,
            target_curr,
            batch_size=self.batch_size,
            epochs=1,
            verbose=0
        )
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        return history.history['loss'][0]
        
    def save(self, path: str) -> None:
        """Save model weights"""
        self.model.save_weights(path)
        
    def load(self, path: str) -> None:
        """Load model weights"""
        self.model.load_weights(path)

class TradingRL:
    def __init__(
        self,
        data: np.ndarray,
        initial_balance: float = 10000,
        transaction_fee: float = 0.001
    ):
        self.data = data
        self.state_size = data.shape[1] + 2  # +2 for position and balance
        self.env = TradingEnvironment(
            data=data,
            initial_balance=initial_balance,
            transaction_fee=transaction_fee
        )
        self.agent = DQNAgent(state_size=self.state_size)
        
    def train(
        self,
        episodes: int = 100,
        batch_size: int = 32
    ) -> List[dict]:
        """Train the agent"""
        scores = []
        
        for episode in range(episodes):
            state = self.env.reset()
            total_reward = 0
            done = False
            
            while not done:
                # Choose action
                action = self.agent.act(state)
                
                # Take action
                next_state, reward, done, info = self.env.step(action)
                
                # Store experience
                self.agent.remember(state, action, reward, next_state, done)
                
                # Train on past experiences
                loss = self.agent.replay()
                
                # Update state and reward
                state = next_state
                total_reward += reward
                
            # Update target model periodically
            if episode % 10 == 0:
                self.agent.update_target_model()
                
            scores.append({
                'episode': episode + 1,
                'reward': total_reward,
                'epsilon': self.agent.epsilon,
                'trades': info['trades']
            })
            
            logger.info(
                f"Episode: {episode + 1}, Reward: {total_reward:.2f}, "
                f"Epsilon: {self.agent.epsilon:.2f}, Trades: {info['trades']}"
            )
            
        return scores
        
    def evaluate(self, data: np.ndarray) -> List[dict]:
        """Evaluate the trained agent"""
        self.env.data = data
        state = self.env.reset()
        trades = []
        done = False
        
        while not done:
            action = self.agent.act(state, eval_mode=True)
            next_state, reward, done, info = self.env.step(action)
            
            if action != 0:  # If trade was made
                trades.append({
                    'step': self.env.current_step,
                    'action': 'BUY' if action == 1 else 'SELL',
                    'price': data[self.env.current_step][0],
                    'reward': reward
                })
                
            state = next_state
            
        return {
            'final_balance': self.env.balance,
            'total_trades': len(trades),
            'trades': trades,
            'returns': (self.env.balance - self.env.initial_balance) 
                      / self.env.initial_balance
        }