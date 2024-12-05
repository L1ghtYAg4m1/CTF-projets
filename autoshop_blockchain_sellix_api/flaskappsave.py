from flask import Flask, request, jsonify
import logging
import requests
from telegram import Bot

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Telegram bot token
TELEGRAM_BOT_TOKEN = '7321304401:AAFV6SmQBr0eNuEQMUoIrM07v78YNPgqmqU'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

@app.route('/webhook', methods=['POST'])
def sellix_webhook():
    # Log the incoming request data
    logger.info(f"Received webhook payload: {request.get_data(as_text=True)}")
    
    # Get the JSON payload from the webhook
    data = request.json
    event_type = data.get('event')
    event_data = data.get('data')

    # Process the event
    if event_type == 'order:paid':
        order_id = event_data.get('id')
        # Fetch order details from Sellix API
        order_details = fetch_order_details(order_id)
        # Process order details (e.g., send confirmation message to user)
        send_confirmation_message(order_details)

    return jsonify({'status': 'ok'})

def fetch_order_details(order_id):
    """Fetch order details from Sellix API"""
    response = requests.get(f'https://dev.sellix.io/v1/orders/{order_id}', headers={
        'Authorization': 'Bearer YOUR_SELLIX_API_KEY'
    })
    return response.json()

def send_confirmation_message(order_details):
    """Send confirmation message to the user"""
    chat_id = order_details.get('user_id')  # Ensure this is the correct field for chat ID
    message = (
        f"🎉 Votre paiement pour la commande #{order_details.get('id')} a été confirmé !\n"
        f"🛒 Détails de la commande :\n"
        f"Montant : {order_details.get('amount')}\n"
        f"Produit : {order_details.get('product')}\n"
    )
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Sent message to chat ID {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Error sending message to chat ID {chat_id}: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
