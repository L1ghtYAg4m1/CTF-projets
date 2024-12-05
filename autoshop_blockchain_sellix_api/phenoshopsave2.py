import logging
import asyncio
import nest_asyncio
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Apply the nest_asyncio patch
nest_asyncio.apply()

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

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    username = user.username if user.username else "utilisateur"

    user_balance = context.user_data.get('balance', {'SOL': 0.0, 'ETH': 0.0, 'LTC': 0.0})
    total_balance_eur = sum(user_balance[crypto] * conversion_rates[crypto] for crypto in user_balance)

    welcome_message = (
        f"👋 Salut, @{username}\n\n"
        f"👛 Solde: {total_balance_eur:.2f}€\n"
        f"💵 Solde crypto actuel: {user_balance['SOL']} SOL, {user_balance['ETH']} ETH, {user_balance['LTC']} LTC"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧑‍💼 Mon profil", callback_data='profile'),
         InlineKeyboardButton("🛒 Shop", callback_data='shop')],
        [InlineKeyboardButton("💰 Dépôt Crypto", callback_data='deposit_crypto'),
         InlineKeyboardButton("🔗 Canal", url='url')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def main() -> None:
    # Create application and add handlers
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    # Add other handlers...

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    # Use existing event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Error occurred: {e}")
