from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from train import CryptoTradingEnv
from stable_baselines3 import PPO

symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT']
# Load the trained model with RMT and Martingale system
model = PPO.load("crypto_trading_bot_rmt_martingale.zip")

# Function to make predictions using the trained model
def make_prediction(update: Update, context: CallbackContext):
    env = CryptoTradingEnv(asset_symbols=symbols)
    obs = env.reset()
    action, _ = model.predict(obs)

    message = "Trading signals based on ML model with RMT and Martingale:\n"
    for i, symbol in enumerate(symbols):
        action_text = "HOLD" if action[i] == 0 else "BUY" if action[i] == 1 else "SELL"
        message += f"{symbol}: {action_text} (Trade Size: {env.current_trade_amount})\n"

    update.message.reply_text(message)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome to the Advanced Crypto Trading Bot with RMT and Martingale! Use /predict to get trading signals.')

def main():
    TOKEN = "7948445357:AAGoIbi1_x0EO_u9ysWc_gQw2wsNG15KZDY"
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('predict', make_prediction))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
