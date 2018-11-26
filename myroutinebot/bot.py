import json
import requests
import urllib
import os


class Bot():
    def __init__(self):        
        self.TOKEN = "597151993:AAFYtCYeSONpV_8Fj16EmAF16XQjG0grvVo"
        self.URL = 'https://api.telegram.org/bot{}/'.format(self.TOKEN)
        self.HELP = (
            '/new NOME\n'
            '/todo ID\n'
            '/doing ID\n'
            '/done ID\n'
            '/delete ID\n'
            '/rename ID NOME\n'
            '/dependson ID ID...\n'
            '/duplicate ID\n'
            '/priority ID PRIORITY{low, medium, high}\n'
            '/duedate ID DATE{dd/mm/aaaa}\n'
            '/list\n'
            '/help\n'
        )

    def get_url(self, url):
        '''
        Retorna a url desejada
        '''
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        '''
        Retorna json a partir da url desejada
        '''
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        '''
        Retorna updates do bot com timeout = 100
        '''
        url = self.URL + 'getUpdates?timeout=100'
        if offset:
            url += '&offset={}'.format(offset)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None):
        '''
        Retorna mensagem a ser mostrada para o usuário pelo bot
        '''
        text = urllib.parse.quote_plus(text)
        url = self.URL + 'sendMessage?text={}&chat_id={}&parse_mode=Markdown'\
                         .format(text, chat_id)
        if reply_markup:
            url += '&reply_markup={}'.format(reply_markup)
        self.get_url(url)

    def get_last_update_id(self, updates):
        '''
        Pega id do último update do bot
        '''
        update_ids = []
        for update in updates['result']:
            update_ids.append(int(update['update_id']))
        return max(update_ids)
