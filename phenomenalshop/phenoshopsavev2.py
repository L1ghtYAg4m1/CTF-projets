import logging
import asyncio
import html 
import nest_asyncio
import aiohttp
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Apply the nest_asyncio patch
nest_asyncio.apply()
# Escape special characters for Markdown V2
def escape_markdown_v2(text):
    special_chars = [
        '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!', ':', '\\'
    ]
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text



# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your actual token
TELEGRAM_BOT_TOKEN = '7321304401:AAFV6SmQBr0eNuEQMUoIrM07v78YNPgqmqU'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Global variable to store conversion rates
conversion_rates = {
    'SOL': 0.0,
    'ETH': 0.0,
    'LTC': 0.0
}

# Define function to fetch crypto rates
async def fetch_crypto_rates():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'solana,ethereum,litecoin',
        'vs_currencies': 'eur'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, ssl=False) as response:
            rates = await response.json()
            return rates

# Define function to update rates periodically
async def update_rates_periodically():
    global conversion_rates
    while True:
        try:
            rates = await fetch_crypto_rates()
            conversion_rates['SOL'] = rates.get('solana', {}).get('eur', 0.0)
            conversion_rates['ETH'] = rates.get('ethereum', {}).get('eur', 0.0)
            conversion_rates['LTC'] = rates.get('litecoin', {}).get('eur', 0.0)
            logger.info(f"Updated rates: {conversion_rates}")
        except Exception as e:
            logger.error(f"Error updating rates: {e}")
        await asyncio.sleep(20)





# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    username = user.username if user.username else "utilisateur"

    user_balance = context.user_data.get('balance', {'SOL': 0.0, 'ETH': 0.0, 'LTC': 0.0})
    total_balance_eur = sum(user_balance[crypto] * conversion_rates[crypto] for crypto in user_balance)

    # Escape special characters in the username and message
    escaped_username = html.escape(username)
    escaped_message = (
        f"👋 Salut, @{escaped_username}\n\n"
        "Vous êtes actuellement sur le meilleur AUTOSHOP de numlist/maillist/plesk de Telegram avec la plus grande variété de pays. Nous vous invitons à découvrir nos différentes catégories disponibles !\n\n"
        "🗓 Dépôt doublé tout les dimanches à partir de minuit.\n\n"
        "🏦 NL IDF disponible en mp @rienagratter2phenomenal\n"
        "💲 10€ le k (pas de dépôt doublé)\n\n"
        "🏙 NL ciblé par ville/région/code postal...\n"
        "En mp @rienagratter2phenomenal 💲 5€ le k\n\n"
        "🤖 Bot pour Split votre NL : @rienagratter2phenomenal\n"
        "Pour y accéder : 100$ de dépôt minimum\n\n"
        "💳 Dépôt en PSF disponible avec 10% de frais.\n"
        "⚠️ NE PAS PRENDRE PCS !!!!\n\n"
        f"👛 Solde: {total_balance_eur:.2f}€\n"
        f"💵 Solde crypto actuel: {user_balance['SOL']} SOL, {user_balance['ETH']} ETH, {user_balance['LTC']} LTC"
    )

    # Debugging: Log the escaped message
    logger.info(f"Sending message: {escaped_message}")

    # Creating buttons (simplified labels)
    keyboard = [
        [InlineKeyboardButton("Profil", callback_data='profile'),  # Simplified button text
         InlineKeyboardButton("Shop", callback_data='shop')],      # Simplified button text
        [InlineKeyboardButton("Dépot Crypto", callback_data='deposit_crypto'),
         InlineKeyboardButton("Canal", url='https://t.me/chezphenomenal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message
    if update.message:
        await update.message.reply_text(escaped_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.reply_text(escaped_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)







# Handle the profile view
async def handle_profile(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_balance = context.user_data.get('balance', {'SOL': 0.0, 'ETH': 0.0, 'LTC': 0.0})
    total_balance_eur = sum(user_balance[crypto] * conversion_rates[crypto] for crypto in user_balance)

    profile_text = escape_markdown_v2(
        f"👤 Profil de l'utilisateur: @{user.username}\n"
        f"💼 Solde total en euros: {total_balance_eur:.2f}€\n"
        f"💵 Solde crypto: {user_balance['SOL']} SOL, {user_balance['ETH']} ETH, {user_balance['LTC']} LTC"
    )

    keyboard = [
        [InlineKeyboardButton("↩️ Retour", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(profile_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup)

# Handle the shop view
async def handle_shop(update: Update, context: CallbackContext) -> None:
    text = (
        "🛒 Bienvenue dans la boutique !\n"
        "Voici les articles disponibles...\n\n"
        "1. NumList - 10€/K\n"
        "2. MailList - 15€/K\n"
        "3. Plesk - 50€/server\n\n"
        "Contactez-nous pour acheter."
    )
    keyboard = [
        [InlineKeyboardButton("↩️ Retour", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)

# Handle deposit crypto action
async def handle_deposit_crypto(update: Update, context: CallbackContext) -> None:
    text = (
        "💰 Choisissez la crypto pour le dépôt :"
    )
    keyboard = [
        [InlineKeyboardButton("SOL", callback_data='deposit_SOL'),
         InlineKeyboardButton("ETH", callback_data='deposit_ETH')],
        [InlineKeyboardButton("LTC", callback_data='deposit_LTC')],
        [InlineKeyboardButton("↩️ Retour", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)

# Handle specific crypto deposit
async def handle_crypto_deposit(update: Update, context: CallbackContext, crypto_type: str) -> None:
    addresses = {
        'SOL': '3oWNV7hZHJXHVHE9jtgUha1cjDDN6tWeKFHJf1Q4DqAH',
        'ETH': '0x8338Ef87f251f556466b9f3B0F8687886e03F742',
        'LTC': 'LZm7WQ2ZYz4WnQKQfWQmKNM1eQ9KkD6nFf3qkLmCCKfQ'
    }
    address = addresses.get(crypto_type, 'Adresse non trouvée')

    text = (
        f"💰 Dépôt en {crypto_type} sélectionné.\n"
        f"Veuillez envoyer le montant souhaité à l'adresse suivante :\n"
        f"{address}"
    )
    keyboard = [
        [InlineKeyboardButton("↩️ Retour", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)

# Handle button clicks and their actions
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'profile':
        await handle_profile(update, context)
    elif data == 'shop':
                await handle_shop(update, context)
    elif data == 'deposit_crypto':
        await handle_deposit_crypto(update, context)
    elif data.startswith('deposit_'):
        crypto_type = data.split('_')[1]
        await handle_crypto_deposit(update, context, crypto_type)
    elif data == 'main_menu':
        await start(update, context)

# Main function to run the bot
async def main() -> None:
    # Create the Application object
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Start updating the rates in the background
    asyncio.create_task(update_rates_periodically())

    # Initialize and start polling
    await application.initialize()
    await application.run_polling()

# Run the bot
if __name__ == '__main__':
    asyncio.run(main())

       
