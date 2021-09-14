import telegram
import json

class Telegrambot:
    tbot_config = json.loads(open('./config/tbotuser.json','r').read().rstrip())

    def send_message(self,message):
        bot = telegram.Bot(token=self.tbot_config['token'])
        bot.sendMessage(chat_id=self.tbot_config['chat_id'], text=message)
