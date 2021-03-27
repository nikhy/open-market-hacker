# importing all required libraries 
import requests
# get your api_id, api_hash, token 
# from telegram as described above 
from config import config
telegramParams = config(filename ='telegram.ini',section='telegram')

bot_token = telegramParams['bot_token']
chat_id = telegramParams['chat_id'] 
def telegram_bot_sendtext(bot_message):
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()

if __name__ == '__main__':
    telegram_bot_sendtext('Hi Nik')