import torch
from telegram import Update
from telegram.ext import Application, CommandHandler
from train import CryptoTradingEnv
from stable_baselines3 import PPO

# Asset symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT']

# Path to the policy file
policy_path = "policy.pth"

# Load the pre-trained policy for inference only
try:
    # Initialize a dummy environment for inference
    dummy_env = CryptoTradingEnv(asset_symbols=symbols, is_inference=True)  # Inference mode
    model = PPO('MlpPolicy', dummy_env)  # Create a dummy model to load the policy into

    # Load the saved policy network's weights (inference only)
    model.policy.load_state_dict(torch.load(policy_path, map_location=torch.device('cpu')))
    model.policy.eval()  # Set the policy to evaluation mode (no training)

    print("Policy loaded successfully for inference!")
except Exception as e:
    print(f"Error loading the policy for inference: {e}")
    model = None

# Function to handle /start command
async def start(update: Update, context):
    await update.message.reply_text(
        'Welcome to the Advanced Crypto Trading Bot with RMT and Martingale! Use /predict to get trading signals.'
    )

# Function to generate predictions for the /predict command
async def make_prediction(update: Update, context):
    if model is None:
        await update.message.reply_text("Error: Model is not loaded.")
        return

    try:
        # Create the environment for inference (with is_inference=True)
        env = CryptoTradingEnv(asset_symbols=symbols, is_inference=True)
        obs = env.reset()

        print("Environment reset successfully. Running inference...")

        # Make predictions using the loaded policy (inference mode)
        action, _ = model.predict(obs)

        # Prepare the signals message
        message = "Trading signals based on ML model with RMT and Martingale (Inference mode):\n"
        for i, symbol in enumerate(symbols):
            action_text = "HOLD" if action[i] == 0 else "BUY" if action[i] == 1 else "SELL"
            message += f"{symbol}: {action_text} (Trade Size: {env.current_trade_amount})\n"

        # Send the response back to the user on Telegram
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"Error generating predictions: {e}")

# Function to run the Telegram bot
def run_bot():
    TOKEN = "7948445357:AAGoIbi1_x0EO_u9ysWc_gQw2wsNG15KZDY"  # Use your actual bot token
    application = Application.builder().token(TOKEN).build()

    # Handlers for commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('predict', make_prediction))

    # Start polling for updates from Telegram
    application.run_polling()

if __name__ == "__main__":
    run_bot()
