import requests

TELEGRAM_BOT_TOKEN = '7321304401:AAFV6SmQBr0eNuEQMUoIrM07v78YNPgqmqU'
WEBHOOK_URL = 'https://5cdb-188-125-171-203.ngrok-free.app/webhook'  # Replace with your actual URL

response = requests.post(
    f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook',
    data={'url': WEBHOOK_URL}
)
print(response.json())
