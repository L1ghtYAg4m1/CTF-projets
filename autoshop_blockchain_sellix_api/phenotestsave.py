#use local crypto testnet for the shop
import logging
import asyncio
import re
import httpx
import decimal
from web3 import Web3
import aiohttp
import nest_asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

nest_asyncio.apply()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE = 'bot_database.db'
TELEGRAM_BOT_TOKEN = '7660325653:AAE1fUV-8-xig67Ub8s_0DcTAwlCjz2IiYo'

# Global variable to store conversion rates
conversion_rates = {
    'SOL': 0.0,
    'ETH': 0.0,
    'LTC': 0.0
}

# Global task reference
monitor_task = None

def transaction_processed(tx_hash):
    """Check if the transaction has already been processed."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM processed_transactions WHERE tx_hash = ?', (tx_hash,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0
async def get_user_balance_in_euros(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if user exists
    c.execute('SELECT COUNT(*) FROM user_balances WHERE user_id = ?', (user_id,))
    exists = c.fetchone()[0]

    # If user does not exist, insert them with default balances
    if exists == 0:
        c.execute('''
            INSERT INTO user_balances (user_id, sol_balance, eth_balance, ltc_balance, euro_balance)
            VALUES (?, 0.0, 0.0, 0.0, 0.0)
        ''', (user_id,))
        conn.commit()
        logger.info(f"Inserted new user {user_id} with default balances.")

    # Fetch the user's balances
    c.execute('SELECT sol_balance, eth_balance, ltc_balance, euro_balance FROM user_balances WHERE user_id = ?', (user_id,))
    balance = c.fetchone()
    conn.close()

    sol_balance = balance[0] or 0.0
    eth_balance = balance[1] or 0.0
    ltc_balance = balance[2] or 0.0
    euro_balance = balance[3] or 0.0

    return {
        'SOL': sol_balance,
        'ETH': eth_balance,
        'LTC': ltc_balance,
        'total_eur': euro_balance
    }


async def handle_shop(update: Update, context: CallbackContext) -> None:
    shop_text = "🛒 Voici les articles disponibles dans notre shop:\n\n1. Article 1\n2. Article 2\n3. Article 3"

    keyboard = [
        [InlineKeyboardButton("🔙 Retour", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(shop_text, reply_markup=reply_markup)
def mark_transaction_as_processed(tx_hash):
    """Mark a transaction as processed to avoid duplicate deposits."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO processed_transactions (tx_hash) VALUES (?)', (tx_hash,))
    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def store_user_wallet(user_id, wallet_address, crypto_type):
    conn = get_db_connection()
    c = conn.cursor()

    try:
        if crypto_type == 'SOL':
            c.execute('''
                INSERT INTO user_wallets (user_id, sol_wallet_address)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                sol_wallet_address = excluded.sol_wallet_address
            ''', (user_id, wallet_address))
        elif crypto_type == 'ETH':
            c.execute('''
                INSERT INTO user_wallets (user_id, eth_wallet_address)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                eth_wallet_address = excluded.eth_wallet_address
            ''', (user_id, wallet_address))
        elif crypto_type == 'LTC':
            c.execute('''
                INSERT INTO user_wallets (user_id, ltc_wallet_address)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                ltc_wallet_address = excluded.ltc_wallet_address
            ''', (user_id, wallet_address))
        conn.commit()
        logger.info(f"Stored wallet address for user {user_id} and crypto {crypto_type}: {wallet_address}")
    except sqlite3.Error as e:
        logger.error(f"Database error while storing wallet address: {e}")
    finally:
        conn.close()

async def fetch_conversion_rates() -> None:
    global conversion_rates
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'solana,ethereum,litecoin',
        'vs_currencies': 'eur'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            data = response.json()
            conversion_rates['SOL'] = data.get('solana', {}).get('eur', 0.0)
            conversion_rates['ETH'] = data.get('ethereum', {}).get('eur', 0.0)
            conversion_rates['LTC'] = data.get('litecoin', {}).get('eur', 0.0)
            logger.info(f"Updated conversion rates: {conversion_rates}")
        except Exception as e:
            logger.error(f"Error fetching conversion rates: {e}")



def update_user_balance(user_id, crypto_type, amount):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the latest conversion rates (convert float to Decimal)
    sol_rate = decimal.Decimal(conversion_rates['SOL'])
    eth_rate = decimal.Decimal(conversion_rates['ETH'])
    ltc_rate = decimal.Decimal(conversion_rates['LTC'])
    
    try:
        # Convert user_id to string just to ensure compatibility with SQLite
        user_id_str = str(user_id)

        if crypto_type == 'SOL':
            euro_amount = decimal.Decimal(amount) * sol_rate
            c.execute('''
                INSERT INTO user_balances (user_id, sol_balance, euro_balance)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                sol_balance = sol_balance + excluded.sol_balance,
                euro_balance = euro_balance + ?
            ''', (user_id_str, float(amount), float(euro_amount), float(euro_amount)))
        elif crypto_type == 'ETH':
            euro_amount = decimal.Decimal(amount) * eth_rate
            c.execute('''
                INSERT INTO user_balances (user_id, eth_balance, euro_balance)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                eth_balance = eth_balance + excluded.eth_balance,
                euro_balance = euro_balance + ?
            ''', (user_id_str, float(amount), float(euro_amount), float(euro_amount)))
        elif crypto_type == 'LTC':
            euro_amount = decimal.Decimal(amount) * ltc_rate
            c.execute('''
                INSERT INTO user_balances (user_id, ltc_balance, euro_balance)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                ltc_balance = ltc_balance + excluded.ltc_balance,
                euro_balance = euro_balance + ?
            ''', (user_id_str, float(amount), float(euro_amount), float(euro_amount)))

        conn.commit()
        logger.info(f"Updated balance for user {user_id}, crypto {crypto_type}: amount {amount}, euro equivalent {euro_amount}")
    except sqlite3.Error as e:
        logger.error(f"Database error while updating balance: {e}")
    finally:
        conn.close()

def is_valid_eth_address(address):
    return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None

def is_valid_ltc_address(address):
    # Validate Legacy (L or M) or P2SH (3) addresses
    if re.match(r'^(L|M|3)[a-zA-Z0-9]{33}$', address):
        return True
    
    # Validate Bech32 (SegWit) addresses (ltc1... with a length between 42 and 62)
    if re.match(r'^ltc1[a-z0-9]{39,59}$', address):
        return True
    
    return False
def is_valid_sol_address(address):
    return re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address) is not None


async def check_eth_deposit(application: Application):
    # Connect to the local Ethereum testnet (Ganache)
    web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

    if web3.is_connected():
        logger.info("Connected to Ganache")
    else:
        logger.error("Failed to connect to Ganache")
        return

    # Connect to the database and fetch all user wallet addresses
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT user_id, eth_wallet_address FROM user_wallets')
    rows = c.fetchall()
    conn.close()

    # Loop through each user and check for transactions
    for row in rows:
        user_id, eth_address = row

        try:
            # Get the latest block and its transactions
            latest_block = web3.eth.get_block('latest', full_transactions=True)
            logger.info(f"Block Number: {latest_block.number}")
            
            for tx in latest_block.transactions:
                # Check if the 'to' address matches the shop's destination address
                if tx['to'].lower() == '0xEA4B7cEA6D574540436e4fDFF3B0447CF7952bCb'.lower():
                    logger.info(f"Transaction found: {tx}")

                    # Check if the 'from' address matches the user's wallet
                    if tx['from'].lower() == eth_address.lower():
                        # Convert value from Wei to Ether using the correct method on the `web3` instance
                        deposit_amount = web3.from_wei(tx['value'], 'ether')

                        # Check if the transaction has been processed already
                        tx_hash = tx['hash'].hex()
                        if not transaction_processed(tx_hash):
                            logger.info(f"Processing deposit: {deposit_amount} ETH from TX {tx_hash}")

                            # Update the user's balance
                            update_user_balance(user_id, 'ETH', deposit_amount)

                            # Notify the user of the deposit
                            await notify_user_of_deposit(application, user_id, 'ETH', deposit_amount)

                            # Mark the transaction as processed
                            mark_transaction_as_processed(tx_hash)

        except Exception as e:
            logger.error(f"Error checking ETH deposits for {eth_address}: {e}")





blockcypher_token = "c45425d0495647f7acd60d8999328e0a"



async def check_ltc_deposit(application: Application):
    async with aiohttp.ClientSession() as session:
        url = 'https://api.blockcypher.com/v1/ltc/main/addrs'
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT user_id, ltc_wallet_address FROM user_wallets')
        rows = c.fetchall()
        conn.close()
        for row in rows:
            user_id, ltc_address = row
            try:
                logger.info(f"Checking LTC deposits for address {ltc_address}")
                # Make a request to BlockCypher API for checking received transactions
                async with session.get(f"{url}/{ltc_address}/full?token={blockcypher_token}",ssl=False) as response:
                    result = await response.json()
                    logger.info(f"LTC deposit check result: {result}")
                    
                    if 'txs' in result:  # Transactions are returned under 'txs'
                        transactions = result['txs']
                        destination_address = 'ltc1qvrc2l7f455c0dgklf33sruy96v6atfn0njhmrk'  # Your destination address
                        
                        for tx in transactions:
                            if destination_address in tx['addresses']:
                                deposit_amount = sum([float(output['value']) / 1e8 for output in tx['outputs'] if output['addresses'] == [destination_address]])
                                tx_hash = tx['hash']
                                
                                # Check if this transaction has already been processed
                                if not transaction_processed(tx_hash):
                                    logger.info(f"Processing deposit: {deposit_amount} LTC from TX {tx_hash}")
                                    update_user_balance(user_id, 'LTC', deposit_amount)
                                    await notify_user_of_deposit(application, user_id, 'LTC', deposit_amount)
                                    mark_transaction_as_processed(tx_hash)  # Mark transaction as processed
            except Exception as e:
                logger.error(f"Error checking LTC deposits: {e}")


async def check_sol_deposit(application: Application):
    connector = aiohttp.TCPConnector(use_dns_cache=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        url = 'https://api.mainnet-beta.solana.com'  # Replace with Solana's official mainnet or testnet RPC
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT user_id, sol_wallet_address FROM user_wallets')
        rows = c.fetchall()
        conn.close()

        for row in rows:
            user_id, sol_address = row
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getConfirmedSignaturesForAddress2",
                "params": [sol_address, {"limit": 10}]
            }
            try:
                logger.info(f"Checking SOL deposits for address {sol_address}")
                async with session.post(url, json=payload, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"SOL deposit check result: {result}")
                        if 'result' in result:
                            transactions = result['result']
                            destination_address = '3vwRyzNv9HGsp4wQekTUCDQsHFZkmHfXig2nuSmXrjGu'  # Replace with actual destination address
                            for tx in transactions:
                                if tx['memo'] == destination_address:  # Assuming 'memo' contains destination info
                                    deposit_amount = float(tx['amount']) / 1e9  # Adjust conversion
                                    tx_hash = tx['signature']

                                    if not transaction_processed(tx_hash):
                                        logger.info(f"Processing deposit: {deposit_amount} SOL from TX {tx_hash}")
                                        update_user_balance(user_id, 'SOL', deposit_amount)
                                        await notify_user_of_deposit(application, user_id, 'SOL', deposit_amount)
                                        mark_transaction_as_processed(tx_hash)
                    else:
                        logger.error(f"Error fetching SOL transactions: {response.status}")
            except Exception as e:
                logger.error(f"Error checking SOL deposits: {e}")




async def monitor_deposits_periodically(application: Application):
    logger.info("Started monitoring deposits")
    while True:
        try:
            await fetch_conversion_rates()  # Fetch the latest conversion rates before checking deposits
            await check_eth_deposit(application)
            await check_ltc_deposit(application)
            await check_sol_deposit(application)
        except Exception as e:
            logger.error(f"Error during periodic deposit monitoring: {e}")
        await asyncio.sleep(10)  # Wait for 20 seconds before running the next check


async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    username = user.username if user.username else "utilisateur"

    user_id = user.id
    user_balance = await get_user_balance_in_euros(user_id)

    sol_balance = user_balance.get('SOL', 0.0)
    eth_balance = user_balance.get('ETH', 0.0)
    ltc_balance = user_balance.get('LTC', 0.0)
    total_eur = user_balance.get('total_eur', 0.0)

    # Format the welcome message with the dynamic balance
    text = f"""
    👋 Salut, @{username}
    👛 Solde: {total_eur:.2f}€
    💵 Solde crypto actuel: {sol_balance:.2f} SOL, {eth_balance:.2f} ETH, {ltc_balance:.2f} LTC.
    """

    keyboard = [
        [InlineKeyboardButton("🧑‍💼 Mon profil", callback_data='profile'),
         InlineKeyboardButton("🛒 Shop", callback_data='shop')],
        [InlineKeyboardButton("💰 Dépôt Crypto", callback_data='deposit_crypto'),
         InlineKeyboardButton("🔗 Canal", url='url')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def handle_profile(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    user_id = user.id  # Get the user's Telegram ID

    # Fetch the user's balance from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT sol_balance, eth_balance, ltc_balance FROM user_balances WHERE user_id = ?', (user_id,))
    balance_row = c.fetchone()
    conn.close()

    if balance_row:
        sol_balance = balance_row['sol_balance'] or 0.0
        eth_balance = balance_row['eth_balance'] or 0.0
        ltc_balance = balance_row['ltc_balance'] or 0.0
    else:
        sol_balance = 0.0
        eth_balance = 0.0
        ltc_balance = 0.0

    # Calculate total balance in euros (assuming you have conversion rates)
    total_balance_eur = (
        sol_balance * conversion_rates['SOL'] +
        eth_balance * conversion_rates['ETH'] +
        ltc_balance * conversion_rates['LTC']
    )

    profile_text = (
        f"👤 Profil de {user.first_name}\n\n"
        f"🔹 Solde total: {total_balance_eur:.2f}€\n"
        f"🔹 SOL: {sol_balance:.2f}\n"
        f"🔹 ETH: {eth_balance:.2f}\n"
        f"🔹 LTC: {ltc_balance:.2f}\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Retour", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def notify_user_of_deposit(application: Application, user_id: int, crypto_type: str, amount: float) -> None:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM user_wallets WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()

    if user_data:
        try:
            message = f"✅ Dépôt reçu de {amount} {crypto_type} dans votre portefeuille."
            await application.bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error notifying user of deposit: {e}")

async def handle_register_wallet(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    crypto_type = query.data
    context.user_data['crypto_type'] = crypto_type

    text = f"Merci d'avoir choisi {crypto_type}. Veuillez entrer votre adresse {crypto_type}."
    await query.edit_message_text(text=text, parse_mode=ParseMode.HTML)

async def handle_deposit_crypto(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("1. SOL", callback_data='SOL')],
        [InlineKeyboardButton("2. ETH", callback_data='ETH')],
        [InlineKeyboardButton("3. LTC", callback_data='LTC')],
        [InlineKeyboardButton("🔙 Retour", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "💰 Dépôt Crypto\nVeuillez sélectionner la crypto-monnaie pour le dépôt:\n\n"
        "1. SOL\n2. ETH\n3. LTC", reply_markup=reply_markup
    )


async def handle_crypto_deposit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    crypto_type = query.data

    if crypto_type not in ['SOL', 'ETH', 'LTC']:
        await query.answer(text="Option invalide.")
        return

    context.user_data['crypto_type'] = crypto_type

    if crypto_type == 'ETH':
        prompt_text = "🔐 Veuillez entrer votre adresse Ethereum :"
    elif crypto_type == 'LTC':
        prompt_text = "🔐 Veuillez entrer votre adresse Litecoin :"
    elif crypto_type == 'SOL':
        prompt_text = "🔐 Veuillez entrer votre adresse Solana :"

    await query.message.reply_text(prompt_text)


async def capture_wallet_address(update: Update, context: CallbackContext) -> None:
    wallet_address = update.message.text
    crypto_type = context.user_data.get('crypto_type')
    user_id = update.effective_user.id

    if crypto_type == 'ETH' and is_valid_eth_address(wallet_address):
        store_user_wallet(user_id, wallet_address, 'ETH')
        destination_address = '0xb5E1E26A33eedeEF83601DD61Bb00e3587caf046'  # Replace with actual address
        await update.message.reply_text(
            f"Votre adresse ETH a été enregistrée: {wallet_address}\n\n"
            f"📝 Veuillez envoyer votre dépôt à l'adresse suivante: {destination_address}"
        )
    elif crypto_type == 'LTC' and is_valid_ltc_address(wallet_address):
        store_user_wallet(user_id, wallet_address, 'LTC')
        destination_address = 'ltc1qabcdef1234567890abcdef1234567890abcde'  # Replace with actual address
        await update.message.reply_text(
            f"Votre adresse LTC a été enregistrée: {wallet_address}\n\n"
            f"📝 Veuillez envoyer votre dépôt à l'adresse suivante: {destination_address}"
        )
    elif crypto_type == 'SOL' and is_valid_sol_address(wallet_address):
        store_user_wallet(user_id, wallet_address, 'SOL')
        destination_address = 'FhG5ZKqF9F5oz7knF7h5EbctYJwU8Lna5vGJ5s5ABqXt'  # Replace with actual address
        await update.message.reply_text(
            f"Votre adresse SOL a été enregistrée: {wallet_address}\n\n"
            f"📝 Veuillez envoyer votre dépôt à l'adresse suivante: {destination_address}"
        )
    else:
        await update.message.reply_text(f"L'adresse {crypto_type} que vous avez fournie est invalide. Veuillez réessayer.")





async def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add bot handlers
    application.add_handler(CommandHandler('start', start))
     # Add bot handlers
    application.add_handler(CallbackQueryHandler(handle_profile, pattern='profile'))
    application.add_handler(CallbackQueryHandler(start, pattern='start'))
    application.add_handler(CallbackQueryHandler(handle_shop, pattern='shop'))
    application.add_handler(CallbackQueryHandler(handle_deposit_crypto, pattern='deposit_crypto'))
    application.add_handler(CallbackQueryHandler(handle_register_wallet, pattern='SOL|ETH|LTC'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_wallet_address))
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_crypto_choice))

    # Start monitoring deposits asynchronously
    global monitor_task
    monitor_task = asyncio.create_task(monitor_deposits_periodically(application))

    # Run the bot with polling inside the asyncio event loop
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
