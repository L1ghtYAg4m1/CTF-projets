import gym
import numpy as np
import pandas as pd
import talib as ta
from gym import spaces
from scipy.linalg import eigh
import torch
from stable_baselines3 import PPO

# Check if CUDA (GPU) is available
if torch.cuda.is_available():
    print(f"CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available. Using CPU.")

# Define the asset symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT']
TRANSACTION_FEE_PERCENT = 0.001  # 0.1% transaction fee

class CryptoTradingEnv(gym.Env):
    def __init__(self, asset_symbols, initial_balance=10000, base_trade_amount=100, max_trade_amount=5000, is_inference=False):
        super(CryptoTradingEnv, self).__init__()

        self.asset_symbols = asset_symbols
        self.initial_balance = initial_balance
        self.base_trade_amount = base_trade_amount
        self.current_trade_amount = base_trade_amount
        self.max_trade_amount = max_trade_amount
        self.current_step = 0
        self.balance = initial_balance
        self.net_worth = initial_balance
        self.crypto_held = np.zeros(len(asset_symbols))
        self.asset_prices = np.zeros(len(asset_symbols))
        self.last_trade_result = None
        self.is_inference = is_inference  # Flag to determine if the environment is being used for inference

        # Load historical data
        self.df_assets = self._fetch_multiple_assets()
        self.df_returns = self.df_assets.pct_change().dropna()
        self.df_assets = self.df_assets.iloc[self.df_returns.index]

        # Apply random matrix theory filtering
        self.corr_matrix, self.filtered_corr_matrix = self._apply_random_matrix_theory(self.df_returns)

        # Pre-calculate indicators for each asset
        self.df_assets = self._apply_indicators(self.df_assets)

        # Define action and observation space
        num_features = len(self.df_assets.columns) + len(self.asset_symbols) + 2  # Columns from asset data, crypto_held, balance, net_worth
        self.action_space = spaces.MultiDiscrete([3] * len(asset_symbols))  # Actions: 0 = Hold, 1 = Buy, 2 = Sell for each asset
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(num_features,), dtype=np.float32)

    def _fetch_multiple_assets(self, timeframe='1h', limit=500):
        import ccxt
        exchange = ccxt.binance()
        asset_data = {}

        for symbol in self.asset_symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            asset_data[symbol] = df['close']

        return pd.DataFrame(asset_data)

    def _apply_random_matrix_theory(self, df_returns, q=None):
        correlation_matrix = np.corrcoef(df_returns, rowvar=False)
        eigenvalues, eigenvectors = eigh(correlation_matrix)
        if q is None:
            q = df_returns.shape[0] / df_returns.shape[1]
        lambda_max = (1 + np.sqrt(1 / q)) ** 2
        filtered_eigenvalues = np.where(eigenvalues > lambda_max, eigenvalues, 0)
        filtered_corr_matrix = (eigenvectors @ np.diag(filtered_eigenvalues) @ eigenvectors.T)
        return correlation_matrix, filtered_corr_matrix

    def _apply_indicators(self, df):
        for column in df.columns:
            df[f'{column}_MA'] = ta.SMA(df[column], timeperiod=20)
            df[f'{column}_EMA'] = ta.EMA(df[column], timeperiod=20)
            df[f'{column}_RSI'] = ta.RSI(df[column], timeperiod=14)
            df[f'{column}_std_dev'] = df[column].rolling(window=20).std()
        return df.fillna(0)

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.crypto_held = np.zeros(len(self.asset_symbols))
        self.current_trade_amount = self.base_trade_amount
        return self._next_observation()

    def _next_observation(self):
        # Get the latest market data (indicators, asset prices, etc.)
        asset_data = self.df_assets.iloc[self.current_step].values  # Market data features

        # Combine market data with additional features
        obs = np.concatenate([asset_data, self.crypto_held, [self.balance, self.net_worth]])

        return obs  # Return the observation

    def step(self, action):
        self.asset_prices = self.df_assets.iloc[self.current_step][self.asset_symbols].values

        previous_net_worth = self.net_worth

        # Execute actions only for inference
        for i in range(len(self.asset_symbols)):
            if action[i] == 1 and self.balance > self.current_trade_amount:
                fee = self.current_trade_amount * TRANSACTION_FEE_PERCENT
                self.crypto_held[i] += (self.current_trade_amount - fee) / self.asset_prices[i]
                self.balance -= self.current_trade_amount
                self.last_trade_result = 'buy'

            elif action[i] == 2 and self.crypto_held[i] > 0:
                sold_value = self.crypto_held[i] * self.asset_prices[i]
                fee = sold_value * TRANSACTION_FEE_PERCENT
                self.balance += (sold_value - fee)
                self.crypto_held[i] = 0
                self.last_trade_result = 'sell'

        self.net_worth = self.balance + np.sum(self.crypto_held * self.asset_prices)
        self.current_step += 1

        done = self.current_step >= len(self.df_assets) - 1  # Stop if the last step is reached
        reward = self.net_worth - previous_net_worth

        # Apply Martingale adjustment only if not in inference mode
        if not self.is_inference:
            self._martingale_adjustment(reward)

        return self._next_observation(), reward, done, {}

    def _martingale_adjustment(self, reward):
        if self.last_trade_result == 'sell' and self.net_worth < self.initial_balance:
            self.current_trade_amount = min(self.current_trade_amount * 2, self.max_trade_amount)
            print(f"[Martingale] Loss detected. Increasing trade size to: {self.current_trade_amount}")
        elif self.net_worth >= self.initial_balance:
            self.current_trade_amount = self.base_trade_amount
            print(f"[Martingale] Profit detected. Resetting trade size to: {self.base_trade_amount}")

    def render(self, mode='human'):
        print(f'Step: {self.current_step}, Balance: {self.balance}, Crypto Held: {self.crypto_held}, Net Worth: {self.net_worth}, Trade Amount: {self.current_trade_amount}')


# **TRAINING MODE**
""" 
# Initialize the environment with the asset symbols and ensure we specify whether we are training or inferring
env = CryptoTradingEnv(asset_symbols=symbols, is_inference=False)  # Set is_inference to False for training

# Train the PPO model using GPU
model = PPO('MlpPolicy', env, verbose=1, tensorboard_log="./crypto_trading_tensorboard/", device='cuda')

# Run training (only if we are not in inference mode)
model.learn(total_timesteps=100000)  # Adjust the timesteps based on your dataset
 
# Save the trained model
model.save("crypto_trading_bot_rmt_martingale")
"""

# **INFERENCE MODE**
# Uncomment this section to run inference after training
env = CryptoTradingEnv(asset_symbols=symbols, is_inference=True)
model = PPO.load("crypto_trading_bot_rmt_martingale.zip", env=env)
obs = env.reset()
action, _ = model.predict(obs)
print(f"Predicted actions: {action}")
