# Trading Bot v8 : 
#detects downward trends with moving average (MVA50 MVA200) and ADX (average directional index)
#Skips "buy" trades when a strong downward trend is detected.
#added bearish or bullish engulfing candlestick pattern strategy

import tkinter as tk
from tkinter import scrolledtext
import threading
import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
import time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

current_trade = None  # Tracks the current trade type: "buy" or "sell". None means no active trade.

# Initialize parameters
symbols = ['BTC/USDT']
timeframe = '1m'
exchange = ccxt.binance()
capital = 1000  # Starting capital
cumulative_winnings = 0
price_data = []
max_daily_loss = 0.1 * capital
daily_loss = 0
running = True
trades_executed_today = 0
max_trades_per_day = 10
sl_multiplier = 0.5
tp_multiplier = 0.5
martingale_steps = [15.62, 31.25, 62.5, 125.0, 250.0, 500.0]  # Fully utilize $1,000
current_step = 0
entry_price = None
stop_loss = None
take_profit = None
max_martingale_steps = 3  # Max Martingale steps allowed

# Update winnings in GUI
def update_winnings_box(winnings_box):
    try:
        if winnings_box:
            winnings_box.config(state=tk.NORMAL)
            winnings_box.delete(1.0, tk.END)
            winnings_box.insert(tk.END, f"${cumulative_winnings:.2f}")
            winnings_box.config(state=tk.DISABLED)
    except Exception as e:
        logger.error(f"Error updating winnings box: {e}")

# Log trade results
def log_result(result, log_box=None):
    try:
        with open("trade_resultsv7.txt", "a") as file:  # Append logs
            file.write(result + "\n")
        if log_box:
            log_box.config(state=tk.NORMAL)
            log_box.insert(tk.END, f"{result}\n")
            log_box.see(tk.END)
            log_box.config(state=tk.DISABLED)
    except Exception as e:
        logger.error(f"Error logging result: {e}")

def update_win_rate_gui(win_rate):
    try:
        win_rate.config(text=f"Win Rate: {win_rate:.2f}%")
    except Exception as e:
        logger.error(f"Error updating win rate in GUI: {e}")

def update_result_file(win_rate, cumulative_winnings, result_file="trade_resultsv7.txt"):
    try:
        with open(result_file, "r+") as file:
            lines = file.readlines()
            # New first line with win rate and cumulative winnings
            new_first_line = f"Win Rate: {win_rate:.2f}%, Cumulative Winnings: ${cumulative_winnings:.2f}\n"
            # Write the new first line and append the rest of the file content
            file.seek(0)
            file.write(new_first_line + ''.join(lines))
    except Exception as e:
        logger.error(f"Error updating result file: {e}")



# Define update_step_panel function
def update_step_panel(step_box):
    """
    Updates the Martingale Steps panel to show the current progression and steps.
    """
    try:
        if step_box:
            step_box.config(state=tk.NORMAL)
            step_box.delete(1.0, tk.END)
            step_box.insert(tk.END, "Martingale Steps:\n")
            for i, step in enumerate(martingale_steps):
                indicator = " (Current Step)" if i == current_step else ""
                step_box.insert(tk.END, f"Step {i + 1}: ${step:.2f}{indicator}\n")
            step_box.config(state=tk.DISABLED)
    except Exception as e:
        logger.error(f"Error updating step panel: {e}")

# Check candlestick patterns
def find_engulfing_pattern(candles):
    current_open = candles['open']
    current_close = candles['close']
    previous_open = candles['previous_open']
    previous_close = candles['previous_close']

    # Bullish Engulfing
    if (current_close > current_open and previous_close < previous_open and
        current_open < previous_close and current_close > previous_open):
        return 'bullish'

    # Bearish Engulfing
    elif (current_close < current_open and previous_close > previous_open and
          current_open > previous_close and current_close < previous_open):
        return 'bearish'

    return None

# Fetch market data
def fetch_market_data(symbol, limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return pd.DataFrame()

# Calculate indicators
def calculate_indicators(df):
    try:
        df['TR'] = df[['high', 'low', 'close']].apply(
            lambda row: max(row['high'] - row['low'], abs(row['high'] - row['close']), abs(row['low'] - row['close'])),
            axis=1
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
        df['RSI'] = calculate_rsi(df['close'])
        df['MVA50'] = df['close'].rolling(window=50).mean()  # 50-period moving average
        df['MVA200'] = df['close'].rolling(window=200).mean()  # 200-period moving average
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df

# RSI Calculation
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Adjust SL/TP
def adjust_sl_tp(entry_price, atr, trend="trending"):
    if trend == "sideways":
        sl_multiplier = 1.0
        tp_multiplier = 1.5
    stop_loss = entry_price - (atr * sl_multiplier)
    take_profit = entry_price + (atr * tp_multiplier)
    return stop_loss, take_profit

# Execute trading logic
def execute_trade(log_box, ax, canvas, winnings_box, step_box):
    global capital, cumulative_winnings, current_step, daily_loss, running, trades_executed_today, current_trade, entry_price, stop_loss, take_profit

    while running:
        if trades_executed_today >= max_trades_per_day or daily_loss >= max_daily_loss or current_step >= max_martingale_steps:
            log_result("Daily limit reached or max Martingale steps hit. Stopping trades.", log_box)
            break

        df = fetch_market_data(symbols[0], limit=50)
        if df.empty:
            time.sleep(5)
            continue

        df = calculate_indicators(df)
        if 'ATR' not in df.columns or 'RSI' not in df.columns:
            continue

        atr = df['ATR'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        mva50 = df['MVA50'].iloc[-1]
        mva200 = df['MVA200'].iloc[-1]

        trend = "downward" if mva50 < mva200 else "sideways"
        log_result(f"RSI: {current_rsi:.2f}, ATR: {atr:.2f}, Trend: {trend}", log_box)

        if not current_trade:
            if trend == "downward":
                log_result("Downward trend detected. Skipping buy trades.", log_box)
                continue

            if current_rsi < 40:
                current_trade = "buy"
                entry_price = df['close'].iloc[-1]
                stop_loss, take_profit = adjust_sl_tp(entry_price, atr, trend)
                log_result(f"Buy Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}", log_box)
            elif current_rsi > 60:
                current_trade = "sell"
                entry_price = df['close'].iloc[-1]
                stop_loss, take_profit = adjust_sl_tp(entry_price, atr, trend)
                log_result(f"Sell Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}", log_box)

        # Monitor active trade
        while current_trade and running:
            df = fetch_market_data(symbols[0], limit=1)
            current_price = df['close'].iloc[-1]
            price_data.append(current_price)
            ax.clear()
            ax.plot(price_data, label="Price Evolution")
            ax.axhline(entry_price, color='blue', linestyle='--', label="Entry Price")
            ax.axhline(stop_loss, color='red', linestyle='--', label="Stop Loss")
            ax.axhline(take_profit, color='green', linestyle='--', label="Take Profit")
            ax.legend()
            canvas.draw_idle()

            if current_price >= take_profit:
                profit = martingale_steps[current_step] * 0.005
                capital += profit
                cumulative_winnings += profit
                current_trade = None
                current_step = 0
                log_result(f"WIN: Profit {profit:.2f}", log_box)
                break
            elif current_price <= stop_loss:
                loss = -martingale_steps[current_step] * 0.005
                capital += loss
                cumulative_winnings += loss
                current_trade = None
                current_step = min(current_step + 1, len(martingale_steps) - 1)
                log_result(f"LOSS: Loss {loss:.2f}", log_box)
                break

        update_winnings_box(winnings_box)
        update_step_panel(step_box)
        time.sleep(5)

# GUI setup
def create_ui():
    root = tk.Tk()
    root.title("Trading Bot v8: Trend detection MVA ADX ")

    log_box = scrolledtext.ScrolledText(root, width=60, height=10)
    log_box.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    tk.Label(root, text="Cumulative Winnings", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, pady=5)

    winnings_box = tk.Text(root, height=1, width=20, state=tk.DISABLED)
    winnings_box.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
    win_rate_label = tk.Label(root, text="Win Rate: 0.00%", font=("Helvetica", 16))
    win_rate_label.grid()

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    step_panel = tk.Frame(root, relief=tk.RAISED, borderwidth=2)
    step_panel.grid(row=0, column=2, rowspan=6, padx=10, pady=10, sticky="nsew")
    tk.Label(step_panel, text="Martingale Steps", font=("Arial", 12, "bold")).pack(pady=5)
    step_box = tk.Text(step_panel, height=12, width=25, state=tk.DISABLED)
    step_box.pack(pady=10)
    update_step_panel(step_box)

    quit_button = tk.Button(root, text="Quit", command=root.destroy)
    quit_button.grid(row=6, column=0, columnspan=2, pady=10)

    threading.Thread(target=execute_trade, args=(log_box, ax, canvas, winnings_box, step_box)).start()
    root.mainloop()

if __name__ == "__main__":
    create_ui()
