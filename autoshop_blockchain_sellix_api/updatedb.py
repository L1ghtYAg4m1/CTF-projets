import sqlite3
import aiohttp
import asyncio
import ssl
import certifi
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create or connect to an SQLite database and set up a table
def initialize_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL,
            rate_eur REAL NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to fetch cryptocurrency rates from the CoinGecko API
async def fetch_crypto_rates():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'solana,ethereum,litecoin',
        'vs_currencies': 'eur'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, params=params, ssl=ssl_context) as response:
            rates = await response.json()
            return rates

# Function to update rates in the database
def update_database(rates):
    conn = sqlite3.connect('crypto_rates.db')
    cursor = conn.cursor()

    # Update rates for each currency
    for currency, data in rates.items():
        rate_eur = data.get('eur', 0.0)
        
        # Insert or replace the currency's rate
        cursor.execute('''
            INSERT INTO crypto_rates (currency, rate_eur)
            VALUES (?, ?)
        ''', (currency, rate_eur))

    conn.commit()
    conn.close()

# Periodically fetch and update rates in the database
async def update_rates_periodically():
    while True:
        try:
            rates = await fetch_crypto_rates()
            logger.info(f"Fetched rates: {rates}")
            update_database(rates)
            logger.info("Database updated successfully!")
        except Exception as e:
            logger.error(f"Error updating rates: {e}")
        
        # Wait 20 seconds before the next update
        await asyncio.sleep(20)

# Main entry point
async def main():
    initialize_db()  # Ensure database and table are created
    await update_rates_periodically()  # Start the periodic update process

if __name__ == "__main__":
    asyncio.run(main())
