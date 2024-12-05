import requests
TELEGRAM_BOT_TOKEN = '7321304401:AAFV6SmQBr0eNuEQMUoIrM07v78YNPgqmqU'
response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo")
print(response.json())
