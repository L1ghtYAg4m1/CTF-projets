from stable_baselines3 import PPO
from train import CryptoTradingEnv
import torch

# Asset symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'SOL/USDT']

# Path to the trained model file
model_path = "crypto_trading_bot_scalping.zip"

# Load the pre-trained policy for inference only
try:
    # Initialize a dummy environment for inference (with is_inference=True)
    env = CryptoTradingEnv(asset_symbols=symbols, is_inference=True)  # Ensure we are in inference mode

    # Load the entire model from the saved file (no new model initialization)
    model = PPO.load(model_path, env=env, device='cuda')  # Load pre-trained model

    print("Model loaded successfully for inference!")
except Exception as e:
    print(f"Error loading the model for inference: {e}")
    model = None

# Function to generate predictions and write them to a text file
def generate_signals():
    if model is None:
        print("Error: Model is not loaded.")
        return

    try:
        obs = env.reset()  # Reset the environment for inference

        print("Environment reset successfully. Running inference...")

        # Make predictions using the loaded policy (inference mode)
        action, _ = model.predict(obs, deterministic=True)  # Use deterministic=True for inference
        print(f"Actions predicted: {action}")

        # Prepare the signals message
        message = "Trading signals based on ML model with RMT and Martingale (Inference mode):\n"
        for i, symbol in enumerate(symbols):
            action_text = "HOLD" if action[i] == 0 else "BUY" if action[i] == 1 else "SELL"
            message += f"{symbol}: {action_text} (Trade Size: {env.current_trade_amount})\n"

        # Write the predictions to a text file
        with open('trading_signals.txt', 'w') as f:
            f.write(message)

        print("Signals written to trading_signals.txt")
    except Exception as e:
        print(f"An error occurred while generating signals: {e}")

if __name__ == '__main__':
    # Call the generate_signals function just for predictions (inference only)
    generate_signals()
