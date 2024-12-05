import logging
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = 'bot_database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/webhook', methods=['POST'])
def webhook():
    # Log the incoming request data
    logger.info(f"Received webhook payload: {request.get_data(as_text=True)}")
    
    # Get the JSON payload from the webhook
    data = request.json
    event_type = data.get('event')
    event_data = data.get('data')

    if event_type == 'order:paid':
        user_id = int(event_data.get('user_id'))
        amount = float(event_data.get('amount'))
        product = event_data.get('product')
        
        # Update user balance in the database
        update_user_balance(user_id, amount, product)
        
        # Log the processing
        logger.info(f"Processed order for User ID: {user_id}")
        logger.info(f"Amount: {amount}")
        logger.info(f"Product: {product}")

    return jsonify({'status': 'ok'})

def update_user_balance(user_id, amount, product):
    """Update the user's balance in the database based on the product"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Determine the field to update based on the product
        if product == "SOL Product":  # Example product name
            cur.execute('''
                INSERT INTO users (user_id, balance_ltc)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET balance_ltc = balance_ltc + ?
            ''', (user_id, amount, amount))
        elif product == "ETH Product":  # Example product name
            cur.execute('''
                INSERT INTO users (user_id, balance_eth)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET balance_eth = balance_eth + ?
            ''', (user_id, amount, amount))
        elif product == "BTC Product":  # Example product name
            cur.execute('''
                INSERT INTO users (user_id, balance_btc)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET balance_btc = balance_btc + ?
            ''', (user_id, amount, amount))
        
        conn.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
