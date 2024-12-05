import requests

TELEGRAM_BOT_TOKEN = '7321304401:AAFV6SmQBr0eNuEQMUoIrM07v78YNPgqmqU'
NGROK_URL = 'https://d4a4-89-36-76-132.ngrok-free.app'  # Replace with your ngrok URL

webhook_url = f"{NGROK_URL}/webhook"
response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook", data={'url': webhook_url})

print(response.json())
