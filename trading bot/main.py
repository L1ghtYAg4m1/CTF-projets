from multiprocessing import Process
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from stable_baselines3 import PPO
from train import CryptoTradingEnv

# Asset symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT']

# Load the model in a separate function/process
def load_model():
    global model
    try:
        model = PPO.load("crypto_trading_bot_rmt_martingale.zip")
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading the model: {e}")
        model = None

# Function to make predictions using the trained model
def make_prediction(update: Update, context: CallbackContext):
    if model is None:
        update.message.reply_text("Model not loaded. Unable to make predictions.")
        return

    try:
        env = CryptoTradingEnv(asset_symbols=symbols)
        obs = env.reset()
        action, _ = model.predict(obs)

        message = "Trading signals based on ML model with RMT and Martingale:\n"
        for i, symbol in enumerate(symbols):
            action_text = "HOLD" if action[i] == 0 else "BUY" if action[i] == 1 else "SELL"
            message += f"{symbol}: {action_text} (Trade Size: {env.current_trade_amount})\n"

        update.message.reply_text(message)
    except Exception as e:
        update.message.reply_text(f"An error occurred while making a prediction: {e}")

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Welcome to the Advanced Crypto Trading Bot with RMT and Martingale! Use /predict to get trading signals.'
    )

# Start the Telegram bot in a separate process
def run_bot():
    TOKEN = "7948445357:AAGoIbi1_x0EO_u9ysWc_gQw2wsNG15KZDY"  # Replace with your actual bot token
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers for commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('predict', make_prediction))

    # Start polling for updates from Telegram
    updater.start_polling()

    # Run the bot until Ctrl+C is pressed or the process is stopped
    updater.idle()

if __name__ == '__main__':
    # Process to load the model
    model_process = Process(target=load_model)

    # Process to run the Telegram bot
    bot_process = Process(target=run_bot)

    # Start both processes
    model_process.start()
    bot_process.start()

    # Join processes (wait for them to complete, or until you manually stop them)
    model_process.join()
    bot_process.join()
