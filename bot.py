import json
import requests
import time
import urllib
from pathlib import Path

class Bot():
    def __init__(self):
        self.TOKEN = self.get_infos_file('/token_my_routinebot.txt', False)
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

    def get_infos_file(self, input_file, set_password=False):
        '''
        Pega informações como token e identificações do arquivo de acordo
        com os parametros input_file e set_password
        '''
        with open('my_routinebot_files' + input_file) as infile:
            if set_password == True:
                lines = infile.readline()[1:]
            lines = infile.readline()
        info = ""
        for line in lines:
            info += line
        info = info.rstrip('\n')
        return info

    def make_github_issue(self, title, body=None):
        '''
        Cria nova issue no repositório de acordo com a url
        '''
        url = 'https://api.github.com/repos/TecProg-20181/my_routinebot/issues'
        session = requests.Session()
        session.auth = (self.get_infos_file("/username_git.txt", False),
                        self.get_infos_file("/username_git.txt", True))
        issue = {'title': title,
                 'body': body}
        r = session.post(url, json.dumps(issue))
        if r.status_code == 201:
            print ('Successfully created Issue {0:s}'.format(title))
        else:
            print ('Could not create Issue {0:s}'.format(title))
            print ('Response:', r.content)

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
