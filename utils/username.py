import requests

from dotenv import load_dotenv
load_dotenv()
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_ENDPOINT = 'https://discord.com/api/v8'
headers = {
	'Content-Type': 'application/json',
	'Authorization': f'Bot {BOT_TOKEN}',
}
data = {
	'username': 'Ricky',
}
response = requests.patch('%s/users/@me' % API_ENDPOINT, json=data, headers=headers)
print(response.json())
