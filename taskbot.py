#!/usr/bin/env python3

import json
import requests
import time
import urllib
from pathlib import Path
from dateutil import parser
import sqlalchemy
import db
from db import Task
import os
import json
import requests
from datetime import datetime


class Bot():
    def __init__(self):
        self.TOKEN = self.get_infos_file("/token_my_routinebot.txt", False)
        self.URL = "https://api.telegram.org/bot{}/".format(self.TOKEN)
        self.HELP = """
                    /new NOME
                    /todo ID
                    /doing ID
                    /done ID
                    /delete ID
                    /list
                    /rename ID NOME
                    /dependson ID ID...
                    /duplicate ID
                    /priority ID PRIORITY{low, medium, high}
                    /help
                    """

    # new_task = Task()

    def get_infos_file(self, input_file, set_password=False):
        home = str(Path.home())
        # input_file = "/token_my_routinebot.txt"
        with open(home + input_file) as infile:
            if set_password == True:
                lines = infile.readline()[1:]
            lines = infile.readline()
        info = ""
        for line in lines:
            info += line
        info = info.rstrip('\n')
        return info

    def make_github_issue(self, title, body=None):
        '''Create an issue on github.com using the given parameters.'''
        # Our url to create issues via POST
        url = 'https://api.github.com/repos/TecProg-20181/my_routinebot/issues'
        # Create an authenticated session to create the issue
        session = requests.Session()
        session.auth = (get_infos_file("/username_git.txt", False),
                        get_infos_file("/username_git.txt", True))
        # Create our issue
        issue = {'title': title,
                 'body': body}
        # Add the issue to our repository
        r = session.post(url, json.dumps(issue))
        if r.status_code == 201:
            print ('Successfully created Issue {0:s}'.format(title))
        else:
            print ('Could not create Issue {0:s}'.format(title))
            print ('Response:', r.content)

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown"\
                         .format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def deps_text(self, task, chat, preceed=''):
        text = ''
        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = db.session.query(Task)\
                                     .filter_by(id=int(task.dependencies\
                                                .split(',')[:-1][i]),\
                                                chat=chat)
            # dep = self.query_one(int(task.dependencies\
            #                          .split(',')[:-1][i]), chat)
            dep = query.one()

            icon = '\U0001F195'
            if dep.status == 'DOING':
                icon = '\U000023FA'
            elif dep.status == 'DONE':
                icon = '\U00002611'

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line
        return text


class HandleTask(Bot):
    def __init__(self):
        Bot.__init__(self)

    def query_one(self, task_id, chat):
        query = db.session.query(Task).filter_by(id=task_id,
                                                 chat=chat)
        task = query.one()
        return task

    def task_not_found_msg(self, task_id, chat):
        self.send_message("_404_ Task {} not found x.x"\
                     .format(task_id), chat)

    def check_msg_not_exists(self, msg):
        if not msg.isdigit():
            return True

    def msg_no_task(self, chat):
        self.send_message("You must inform the task id", chat)

    def new_task(self, command, msg, chat):
        i = len(msg.split())
        msg = msg.split()
        for i in range(i):
            task = Task(chat=chat, name=''.join(msg[i]), status='TODO',
                        dependencies='', parents='', priority='')
            print('\ntask',task)
            db.session.add(task)
            db.session.commit()
            text_message = 'New task *TODO* [[{}]] {}'
            self.send_message(text_message\
                        .format(task.id, task.name), chat)
        # comentado para não abrir issues no repositório
        # self.make_github_issue(task.name, 'Task of ID:[[{}]].\n\\\
                                    #   Name of task:{}\n'\
                                    #   .format(task.id, task.name))

    def condition_test(self, msg):
        if len(msg.split(' ', 1)) > 1:
            return True

    def split_msg(self, msg, element):
        return msg.split(' ', 1)[element]

    def msg_not_empty(self, msg):
        if msg != '':
            return True

    def rename(self, command, msg, chat):
        text = ''
        if self.msg_not_empty(msg):
            if self.condition_test(msg):
                text = self.split_msg(msg, 1)
            msg = self.split_msg(msg, 0)

        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id,
                                                     chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return

            if text == '':
                text_message = ("You want to modify task {},"
                    " but you didn't provide any new text")
                self.send_message(text_message\
                              .format(task_id), chat)
                return

            old_text = task.name
            task.name = text
            db.session.commit()
            text_message = ("You want to modify task {},"
                    " but you didn't provide any new text")
            self.send_message(text_message\
                         .format(task_id, old_text, text), chat)

    def duplicate(self, command, msg, chat):
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return


            dep_task = Task(chat=task.chat, name=task.name, status=task.status,
                         dependencies=task.dependencies, parents=task.parents,
                         priority=task.priority, duedate=task.duedate)
            db.session.add(dep_task)

            for t in task.dependencies.split(',')[:-1]:
                query_dep = db.session.query(Task).\
                                            filter_by(id=int(t),\
                                                      chat=chat)
                t = query_dep.one()
                t.parents += '{},'.format(dep_task.id)
            db.session.commit()
            text_message = 'New task *TODO* [[{}]] {}'
            self.send_message(text_message\
                        .format(dep_task.id, dep_task.name), chat)


    def delete(self, command, msg, chat):
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task)\
                                     .filter_by(id=task_id, chat=chat)
            task = self.query_one(task_id, chat)

            for t in task.dependencies.split(',')[:-1]:
                query_dep = db.session.query(Task)\
                                      .filter_by(id=int(t), chat=chat)
                try:
                    t = query_dep.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    return
                t.parents = t.parents\
                            .replace('{},'.format(task.id), '')

            if task.parents:
                for t in task.parents.split(',')[:-1]:
                    query_par = db.session.query(Task)\
                                      .filter_by(id=int(t), chat=chat)
                    try:
                        t = query_par.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.task_not_found_msg(task_id, chat)
                        return

                    task_dep = t.dependencies.split(',')
                    task_dep.pop()
                    if task_dep == None:
                        task_dep = ''.join(task_dep)
                    else:
                        task_dep.remove(str(task_id))
                        task_dep = ','.join(task_dep)
                        if len(task_dep) > 0:
                            task_dep = task_dep + ','

                    t.dependencies = task_dep



            db.session.delete(task)
            db.session.commit()
            text_message = 'Task [[{}]] deleted'
            self.send_message(text_message\
                         .format(task_id), chat)

    def todo(self, command, msg, chat):
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task)\
                                    .filter_by(id=task_id, chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return
            task.status = 'TODO'
            db.session.commit()
            text_message = '*TODO* task [[{}]] {}'
            self.send_message(text_message\
                         .format(task.id, task.name), chat)

    def doing(self, command, msg, chat):
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task)\
                                     .filter_by(id=task_id, chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return
            task.status = 'DOING'
            db.session.commit()
            text_message = '*DOING* task [[{}]] {}'
            self.send_message(text_message\
                         .format(task.id, task.name), chat)

    def done(self, command, msg, chat):
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task)\
                              .filter_by(id=task_id, chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return

            task.status = 'DONE'
            db.session.commit()
            text_message = '*DONE* task [[{}]] {}'
            self.send_message(text_message\
                         .format(task.id, task.name), chat)

    def task_status(self, status, chat):
        msg_user = ''

        if status == 'TODO':
            msg_user += '\n\U0001F195 *TODO*\n'
        elif status == 'DOING':
            msg_user += '\n\U0001F563 *DOING*\n'
        elif status == 'DONE':
            msg_user += '\n\U00002611 *DONE*\n'

        query = db.session.query(Task)\
                                 .filter_by(status=status, chat=chat)\
                                 .order_by(Task.id)

        for task in query.all():
            msg_user += '\u27A1[[{}]] {}\n'.format(task.id, task.name)

        return msg_user

    def task_priority(self, priority, chat):
        msg_user = ''

        if priority == 'high':
            msg_user += '\U0001F198 high priority\n'
        elif priority == 'medium':
            msg_user += '\u203C medium priority\n'
        elif priority == 'low':
            msg_user += '\u2757 low priority\n'

        query = db.session.query(Task)\
                                 .filter_by(priority=priority, chat=chat)\
                                 .order_by(Task.id)

        for task in query.all():
            msg_user += '\u27A1[[{}]] {}\n'.format(task.id, task.name)

        return msg_user

    def list(self, command, msg, chat):
        msg_user = ''

        msg_user += '\U0001F4CB Task List\n'
        query = db.session.query(Task)\
                                .filter_by(parents='',\
                                           chat=chat).order_by(Task.id)
        for task in query.all():
            icon = '\U0001F195'
            if task.status == 'DOING':
                icon = '\U000023FA'
            elif task.status == 'DONE':
                icon = '\U00002611'
            elif task.priority == 'priority':
                icon = 'u"\U0001F6A8"'

            if task.duedate:
                msg_user += "[[{}]] {} {} \U0001F4C6{}\n".format(task.id,\
                                                            icon, task.name,\
                                                            task.duedate)
            else:
                msg_user += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
            msg_user += self.deps_text(task, chat)

        self.send_message(msg_user, chat)
        msg_user = ''

        msg_user += '\U0001F4DD _Status_\n'
        msg_user += self.task_status('TODO', chat)
        msg_user += self.task_status('DOING', chat)
        msg_user += self.task_status('DONE', chat)


        msg_user += '\n\U0001F6A8 *PRIORITY*\n'
        msg_user += self.task_priority('high', chat)
        msg_user += self.task_priority('medium', chat)
        msg_user += self.task_priority('low', chat)

        self.send_message(msg_user, chat)

    def search_parent(self, task, target, chat):
        if not task.parents == '':
            parent_id = task.parents.split(',')
            parent_id.pop()

            numbers = [ int(id_pai) for id_pai in parent_id ]

            if target in numbers:
                return False
            else:
                parent = self.query_one(numbers[0], chat)
                return self.search_parent(parent, target, chat)

        return True

    def dependson(self, command, msg, chat):
        text = ''
        if self.msg_not_empty(msg):
            if self.condition_test(msg):
                text = self.split_msg(msg, 1)
            msg = self.split_msg(msg, 0)

        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id,\
                                                     chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return


            if text == '':
                for i in task.dependencies.split(',')[:-1]:
                    i = int(i)
                    q = db.session.query(Task).filter_by(id=i,\
                                                         chat=chat)
                    t = q.one()
                    t.parents = t.parents.replace('{},'\
                                                  .format(task.id), '')

                task.dependencies = ''
                self.send_message("Dependencies removed from task {}"\
                             .format(task_id), chat)
            else:
                for depid in text.split(' '):
                    if not depid.isdigit():
                        self.send_message("All dependencies ids must be\\\
                                      numeric, and not {}"\
                                      .format(depid), chat)
                    else:
                        depid = int(depid)
                        query = db.session.query(Task)\
                                                 .filter_by(id=depid,\
                                                 chat=chat)
                        try:
                            taskdep = self.query_one(depid, chat)
                            list_dependencies = taskdep.dependencies\
                                                       .split(',')

                            if self.search_parent(task, taskdep.id, chat):
                                taskdep.parents += str(task.id) + ','
                            else:
                                self.send_message("Essa tarefa já é filha\\\
                                              da sub tarefa", chat)
                                break
                        except sqlalchemy.orm.exc.NoResultFound:
                            self.send_message("_404_ Task {} not found x.x"\
                                         .format(depid), chat)
                            continue
                        deplist = task.dependencies.split(',')
                        if str(depid) not in deplist:
                            task.dependencies += str(depid) + ','

            db.session.commit()
            text_message = 'Task {} dependencies up to date'
            self.send_message(text_message\
                         .format(task_id), chat)

    def priority(self, command, msg, chat):
        text = ''
        if self.msg_not_empty(msg):
            if self.condition_test(msg):
                text = self.split_msg(msg, 1)
            msg = self.split_msg(msg, 0)

        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task)\
                                     .filter_by(id=task_id, chat=chat)
            try:
                task = self.query_one(task_id, chat)
            except sqlalchemy.orm.exc.NoResultFound:
                self.task_not_found_msg(task_id, chat)
                return


            if text == '':
                task.priority = ''
                self.send_message("_Cleared_ all priorities from task {}"\
                             .format(task_id), chat)
            else:
                if text.lower() not in ['high', 'medium', 'low']:
                    self.send_message("The priority *must be* one of the\\\
                                 following: high, medium, low", chat)
                else:
                    task.priority = text.lower()
                    self.send_message("*Task {}* priority has priority\\\
                                 *{}*".format(task_id, text.lower()),\
                                 chat)
            db.session.commit()

    def correct_date(self, text):
        try:
            datetime.strptime(text, '%d/%m/%Y')
            return True
        except ValueError:
            return False


    def duedate(self, command, msg, chat):
        text = ''
        msg_aux = msg
        print('\nmsg_aux:',msg_aux)
        i = len(msg_aux.split())
        print('i:',i)
        msg_aux = msg_aux.split()
        # for i in range(i):
        msg_final = msg_aux[::2]
        text_final = msg_aux[1::2]
        print('msg_final:',msg_final)
        print('text_final:', text_final)


        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
                print('\ntext',text)
            msg = msg.split(' ', 1)[0]
            print('\nmsg dps split:',msg)
        if self.check_msg_not_exists(msg):
            self.msg_no_task(chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                return

            if text == '':
                task.duedate = None
                self.send_message("_Cleared_ all duedates from task {}".format(task_id), chat)
            else:
                if not self.correct_date(text):
                    self.send_message("The duedate *must follow* the pattern: dd/mm/aaaa", chat)
                else:
                    task.duedate = datetime.strptime(text, '%d/%m/%Y')
                    self.send_message("*Task {}* duedate: *{}*".format(task_id, text.lower()), chat)
            db.session.commit()

    def handle_updates(self, updates):
        for update in updates["result"]:
            if 'message' in update:
                message = update['message']
            elif 'edited_message' in update:
                message = update['edited_message']
            else:
                print('Can\'t process! {}'.format(update))
                return

            command = message["text"].split(" ", 1)[0]
            msg = ''
            if len(message["text"].split(" ", 1)) > 1:
                msg = message["text"].split(" ", 1)[1].strip()

            chat = message["chat"]["id"]
            print(command, msg, chat)

            if command == '/new':
                self.new_task(command, msg, chat)

            elif command == '/rename':
                self.rename(command, msg, chat)

            elif command == '/duplicate':
                self.duplicate(command, msg, chat)

            elif command == '/delete':
                self.delete(command, msg, chat)

            elif command == '/todo':
                self.todo(command, msg, chat)

            elif command == '/doing':
                self.doing(command, msg, chat)

            elif command == '/done':
                self.done(command, msg, chat)

            elif command == '/list':
                self.list(command, msg, chat)

            elif command == '/dependson':
                self.dependson(command, msg, chat)

            elif command == '/priority':
                self.priority(command, msg, chat)

            elif command == '/duedate':
                self.duedate(command, msg, chat)

            elif command == '/start':
                self.send_message("Welcome! Here is msg_user list of things you can do."\
                             , chat)
                self.send_message(self.HELP, chat)

            elif command == '/help':
                self.send_message("Here is msg_user list of things you can do.", chat)
                self.send_message(self.HELP, chat)
            else:
                self.send_message("I'm sorry dave. I'm afraid I can't do that."\
                             , chat)



def main():
    last_update_id = None
    task = HandleTask()
    while True:
        print("Updates")
        updates = task.get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = task.get_last_update_id(updates) + 1
            task.handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
