import tkinter as tk
import numpy as np
import pandas as pd
import ccxt
from stable_baselines3 import PPO
import torch
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from train import CryptoTradingEnv

# Load the model path and trading symbol
model_path = "optimized_trading_bot"
symbols = ['ETH/USDT']
timeframe = '1m'

# Initialize exchange
exchange = ccxt.binance()

# Function to fetch real-time data
def fetch_market_data(symbol, limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].apply(mdates.date2num)  # Convert to format for candlestick_ohlc
    return df

# Create the candlestick chart
def update_chart(i):
    global ax1
    df = fetch_market_data(symbols[0])
    ax1.clear()

    # Plotting candlestick
    candlestick_ohlc(ax1, df[['timestamp', 'open', 'high', 'low', 'close']].values, width=0.0005, colorup='g', colordown='r')
    ax1.set_title(f'{symbols[0]} Real-Time Candlestick Chart')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')

# Prediction function
def make_prediction():
    obs = env.reset()
    action, _ = model.predict(obs, deterministic=True)  # Get the action from the model
    
    # Ensure action is treated as a scalar value if needed
    action_val = action.item() if action.size == 1 else action[0]

    # Update the Tkinter labels with the prediction and action label
    prediction_text.set(f"Action predicted: {action_val}")

    # Define the action labels (0=HOLD, 1=BUY, 2=SELL)
    action_label = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
    prediction_label.set(f"Action: {action_label.get(action_val, 'UNKNOWN')}")

    # Schedule the next prediction in 60 seconds (real-time scalping)
    window.after(60000, make_prediction)

# Initialize the GUI window for the prediction interface
window = tk.Tk()
window.title("Real-Time Scalping Prediction")

# Initialize the prediction text labels
prediction_text = tk.StringVar()
prediction_label = tk.StringVar()

# Set up the label widgets in the window
tk.Label(window, textvariable=prediction_text).pack()
tk.Label(window, textvariable=prediction_label).pack()

# Initialize real-time trading environment for inference
try:
    env = CryptoTradingEnv(asset_symbols=symbols, is_inference=True)  # Set inference mode
    model = PPO.load(model_path, env=env, device='cuda')  # Load the trained model (use GPU if available)
    print("Model loaded successfully for inference!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Set up Matplotlib for real-time chart display
fig, ax1 = plt.subplots(figsize=(10, 6))
ani = FuncAnimation(fig, update_chart, interval=60000, cache_frame_data=False)  # Update the chart every minute

# Start real-time predictions
make_prediction()

# Create a separate window to display the candlestick chart
def show_chart():
    plt.show()

# Start the chart window in a separate thread
window.after(100, show_chart)

# Start the Tkinter GUI loop
window.mainloop()
