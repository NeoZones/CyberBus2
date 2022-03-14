import requests

from dotenv import load_dotenv
load_dotenv()
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")


channel_id = 952474835538284614
message_id = 952510538552868884
emoji = "%F0%9F%8E%AE"








API_ENDPOINT = 'https://discord.com/api/v8'
headers = {
	'Content-Type': 'application/json',
	'Authorization': f'Bot {BOT_TOKEN}',
}
data = {
	# 'content': content,
}
response = requests.put(f'{API_ENDPOINT}/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me', json=data, headers=headers)
print(response.json())
