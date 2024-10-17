import gym
import ccxt
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import talib as ta
from gym import spaces
import torch

# Check if CUDA (GPU) is available
if torch.cuda.is_available():
    print(f"CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available. Using CPU.")

# Define the asset symbols (focusing only on ETH/USDT for faster training)
symbols = ['ETH/USDT']
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
        self.is_inference = is_inference

        # Load historical data and indicators
        self.df_assets = self._fetch_multiple_assets()
        self.df_assets = self._apply_indicators(self.df_assets)

        # Define action and observation space
        num_features = 9  # Close price (1), RSI (1), SMA (1), MACD (1), BOLL_UPPER and LOWER (2), Crypto held (1), Balance (1), Net worth (1)
        self.action_space = spaces.Discrete(3)  # Discrete (0 = hold, 1 = buy, 2 = sell)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(num_features,), dtype=np.float32)

    def _fetch_multiple_assets(self, timeframe='1m', limit=500):
        exchange = ccxt.binance()
        asset_data = {}
        for symbol in self.asset_symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                asset_data[symbol] = df
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                asset_data[symbol] = pd.DataFrame()
        return asset_data

    def _apply_indicators(self, asset_data):
        # Precompute indicators once and store them in the DataFrame
        for symbol, df in asset_data.items():
            if not df.empty:
                df['VWAP'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
                df['RSI'] = ta.RSI(df['close'], timeperiod=14)
                df['SMA'] = ta.SMA(df['close'], timeperiod=20)  # Simple moving average
                df['BOLL_UPPER'], df['BOLL_MIDDLE'], df['BOLL_LOWER'] = ta.BBANDS(df['close'], timeperiod=20)
                df['MACD'], df['MACD_signal'], _ = ta.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)

                # Fill NaN values with the most recent valid data (forward fill)
                df.fillna(method='ffill', inplace=True)
                # Backfill any remaining NaN values after forward filling
                df.fillna(method='bfill', inplace=True)

        return asset_data

    def _next_observation(self):
        # Get the latest market data (indicators, asset prices, etc.)
        asset_data = {symbol: self.df_assets[symbol].iloc[self.current_step] for symbol in self.asset_symbols}
        close_prices = np.array([asset_data[symbol]['close'] for symbol in self.asset_symbols])
        rsi = np.array([asset_data[symbol]['RSI'] for symbol in self.asset_symbols])
        sma = np.array([asset_data[symbol]['SMA'] for symbol in self.asset_symbols])
        macd = np.array([asset_data[symbol]['MACD'] for symbol in self.asset_symbols])
        boll_upper = np.array([asset_data[symbol]['BOLL_UPPER'] for symbol in self.asset_symbols])
        boll_lower = np.array([asset_data[symbol]['BOLL_LOWER'] for symbol in self.asset_symbols])

        # Concatenate all features
        obs = np.concatenate([close_prices, rsi, sma, macd, boll_upper, boll_lower, self.crypto_held, [self.balance, self.net_worth]])

        # Debug: Check for NaN or inf values in the observation
        if not np.all(np.isfinite(obs)):
            print("Invalid observation:", obs)
            obs = np.nan_to_num(obs)  # Replace NaN/inf with 0

        return obs

    def step(self, action):
        self.asset_prices = np.array([self.df_assets[symbol].iloc[self.current_step]['close'] for symbol in self.asset_symbols])
        previous_net_worth = self.net_worth

        # Execute actions
        if action == 1 and self.balance > self.current_trade_amount:  # Buy action
            fee = self.current_trade_amount * TRANSACTION_FEE_PERCENT
            self.crypto_held[0] += (self.current_trade_amount - fee) / self.asset_prices[0]
            self.balance -= self.current_trade_amount
            self.last_trade_result = 'buy'
        elif action == 2 and self.crypto_held[0] > 0:  # Sell action
            sold_value = self.crypto_held[0] * self.asset_prices[0]
            fee = sold_value * TRANSACTION_FEE_PERCENT
            self.balance += (sold_value - fee)
            self.crypto_held[0] = 0
            self.last_trade_result = 'sell'

        self.net_worth = self.balance + np.sum(self.crypto_held * self.asset_prices)
        self.current_step += 1
        reward = self.net_worth - previous_net_worth
        done = self.current_step >= len(self.df_assets[self.asset_symbols[0]]) - 1

        # Encourage buying/selling over holding by adding a small negative reward for holding
        if action == 0:
            reward -= 0.01

        return self._next_observation(), reward, done, {}

    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.crypto_held = np.zeros(len(self.asset_symbols))
        return self._next_observation()

    def render(self, mode='human'):
        print(f'Step: {self.current_step}, Balance: {self.balance}, Crypto Held: {self.crypto_held}, Net Worth: {self.net_worth}, Trade Amount: {self.current_trade_amount}')


# **TRAINING MODE**
if __name__ == '__main__':
    # Initialize environment directly without wrapping
    env = CryptoTradingEnv(asset_symbols=symbols)

    # Check the action space after environment initialization
    print(f"Action space after environment initialization: {env.action_space}")

    # Train the PPO model using GPU without wrapping the environment
    model = PPO('MlpPolicy', env, verbose=1, batch_size=1024, n_steps=2048, device='cuda')

    # Run training
    model.learn(total_timesteps=1000000)

    # Save the trained model
    model.save("optimized_trading_bot")
