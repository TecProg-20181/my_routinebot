import sqlalchemy
import db
from db import Task
from datetime import datetime
from bot import Bot

# Emoji constants
NEW = '\U0001F195'
CIRCLE = '\U000023FA'
CHECK = '\U00002611'
CALENDAR = '\U0001F4C6'
CLOCK = '\U0001F563'
SOS = '\U0001F198'
LIGHT = '\U0001F6A8'
MEMO = '\U0001F4DD'
CLIPBOARD = '\U0001F4CB'
ARROW = '\u27A1'
EXCLAMATION_2 = '\u203C'
EXCLAMATION = '\u2757'


class HandleTask(Bot):
    def __init__(self):
        Bot.__init__(self)

    def query_one(self, task_id, chat):
        '''
        Realiza query de uma linha do banco de acordo com seu id
        '''
        query = db.session.query(Task).filter_by(id=task_id,
                                                 chat=chat)
        task = query.one()
        return task

    def task_not_found_msg(self, task_id, chat):
        '''
        Retorna mensagem em que a task não foi encontrada
        '''
        self.send_message('_404_ Task {} not found x.x'.format(task_id), chat)

    def check_msg_not_exists(self, msg):
        '''
        Retorna True caso a mensagem não for um dígito
        '''
        if not msg.isdigit():
            return True

    def msg_no_task(self, chat):
        '''
        Retorna mensagem pedindo para o usuário informar o id da task
        '''
        self.send_message('You must inform the task id', chat)

    def strip_message(self, msg):
        return [i.strip() for i in msg.split(',')]

    def new_task(self, command, msg, chat):
        '''
        Retorna uma nova task e abre uma nova issue no repositório
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            task = Task(chat=chat, name=''.join(msg[i]), status='TODO',
                        dependencies='', parents='', priority='')
            print('\ntask', task)
            db.session.add(task)
            db.session.commit()
            text_message = 'New task *TODO* [[{}]] {}'
            self.send_message(text_message.format(task.id, task.name), chat)
            self.make_github_issue(task.name, 'Task of ID:[[{}]].\n\
                                               Name of task:{}'
                                               .format(task.id, task.name))

    def condition_len_msg(self, msg):
        '''
        Retorna true caso o tamanho da mensagem seja maior que uma palavra
        '''
        if len(msg.split(' ', 1)) > 1:
            return True

    def split_msg(self, msg, element):
        '''
        Realiza o split de uma mensagem
        '''
        return msg.split(' ', 1)[element]

    def msg_not_empty(self, msg):
        '''
        Retorna true caso a mensagem não esteja vazia
        '''
        if msg != '':
            return True

    def rename(self, command, msg, chat):
        '''
        Renomeia uma task
        '''
        text = ''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if msg is not None:
                if len(msg[i].split()) > 1:
                    text = msg[i].split()[1]
                msg_indice = msg[i].split()[0]

            if self.check_msg_not_exists(msg_indice):
                self.msg_no_task(chat)
            else:
                task_id = int(msg_indice)

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue
                if text == '':
                    text_message = ('You want to modify task {},'
                                    ' but you didn\t provide any new text')
                    self.send_message(text_message.format(task_id), chat)
                else:
                    old_text = task.name
                    task.name = text
                    db.session.commit()
                    text_message = ('taks {} renamed')
                    self.send_message(text_message.format(task_id, old_text,
                                                          text), chat)

    def deps_text(self, task, chat, preceed=''):
        '''
        Retorna texto para tasks com dependência
        '''
        text = ''
        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = db.session.query(Task).filter_by(id=int(task.dependencies
                                                            .split(',')
                                                            [:-1][i]),
                                                     chat=chat)
            dep = query.one()

            icon = NEW
            if self.task_condition(dep.status, 'DOING'):
                icon = CIRCLE
            elif self.task_condition(dep.status, 'DONE'):
                icon = CHECK

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                if dep.duedate:
                    line += '└── [[{}]] {} {} {}{}\n'.format(dep.id, icon,
                                                             dep.name,
                                                             CALENDAR,
                                                             dep.duedate)
                else:
                    line += '└── [[{}]] {} {}\n'.format(dep.id, icon,
                                                        dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                if dep.duedate:
                    line += '├── [[{}]] {} {} {}{}\n'.format(dep.id, icon,
                                                             dep.name,
                                                             CALENDAR,
                                                             dep.duedate)
                else:
                    line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line
        return text

    def duplicate(self, command, msg, chat):
        '''
        Duplica uma task
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if self.check_msg_not_exists(msg[i]):
                self.msg_no_task(chat)
            else:
                task_id = int(msg[i])

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue
                dep_task = Task(chat=task.chat, name=task.name,
                                status=task.status,
                                dependencies=task.dependencies,
                                parents=task.parents,
                                priority=task.priority, duedate=task.duedate)
                db.session.add(dep_task)
                for t in task.dependencies.split(',')[:-1]:
                    query_dep = db.session.query(Task).\
                                                filter_by(id=int(t),
                                                          chat=chat)
                    t = query_dep.one()
                    t.parents += '{},'.format(dep_task.id)
                db.session.commit()
                text_message = 'New task *TODO* [[{}]] {}'
                self.send_message(text_message.format(dep_task.id,
                                                      dep_task.name),
                                  chat)
                self.make_github_issue(task.name, 'Task of ID:[[{}]].\n\
                                       Name of task:{}'
                                      .format(task.id, task.name))


    def delete(self, command, msg, chat):
        '''
        Deleta uma task
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if self.check_msg_not_exists(msg[i]):
                self.msg_no_task(chat)
            else:
                task_id = int(msg[i])

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue

                for t in task.dependencies.split(',')[:-1]:
                    query_dep = db.session.query(Task)\
                                          .filter_by(id=int(t), chat=chat)
                    try:
                        t = query_dep.one()
                    except sqlalchemy.orm.exc.NoResultFound:
                        self.task_not_found_msg(task_id, chat)
                        return
                    t.parents = t.parents.replace('{},'.format(task.id), '')

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
                        if task_dep is None:
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
                self.send_message(text_message.format(task_id), chat)

    def todo(self, command, msg, chat):
        '''
        Adiciona uma task para o status TODO
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if self.check_msg_not_exists(msg[i]):
                self.msg_no_task(chat)
            else:
                task_id = int(msg[i])

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue
                task.status = 'TODO'
                db.session.commit()
                text_message = '*TODO* task [[{}]] {}'
                self.send_message(text_message
                                  .format(task.id, task.name), chat)

    def doing(self, command, msg, chat):
        '''
        Adiciona uma task para o status DgiOING
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if self.check_msg_not_exists(msg[i]):
                self.msg_no_task(chat)
            else:
                task_id = int(msg[i])

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue
                task.status = 'DOING'
                db.session.commit()
                text_message = '*DOING* task [[{}]] {}'
                self.send_message(text_message
                                  .format(task.id, task.name), chat)

    def done(self, command, msg, chat):
        '''
        Adiciona uma task para o status DONE
        '''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if self.check_msg_not_exists(msg[i]):
                self.msg_no_task(chat)
            else:
                task_id = int(msg[i])

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue

                task.status = 'DONE'
                db.session.commit()
                text_message = '*DONE* task [[{}]] {}'
                self.send_message(text_message.format(task.id, task.name),
                                  chat)

    def task_condition(self, task, condition):
        if task  == condition:
            return True

    def task_status(self, status, chat):
        '''
        Retorna a mensagem informando o status da task ao usuário
        '''
        msg_user = ''

        if self.task_condition(status, 'TODO'):
            msg_user += '\n' + NEW + ' *TODO*\n'
        elif self.task_condition(status, 'DOING'):
            msg_user += '\n' + CLOCK + ' *DOING*\n'
        elif self.task_condition(status, 'DONE'):
            msg_user += '\n' + CHECK + ' *DONE*\n'

        query = db.session.query(Task).filter_by(status=status,
                                                 chat=chat).order_by(Task.id)

        for task in query.all():
            msg_user += '{}[[{}]] {}\n'.format(ARROW, task.id, task.name)

        return msg_user

    def task_priority(self, priority, chat):
        '''
        Retorna a mensagem informando a prioridade da task ao usuário
        '''
        msg_user = ''

        if self.task_condition(priority, 'high'):
            msg_user += SOS + ' high priority\n'
        elif self.task_condition(priority, 'medium'):
            msg_user += EXCLAMATION_2 + ' medium priority\n'
        elif self.task_condition(priority, 'low'):
            msg_user += EXCLAMATION + ' low priority\n'

        query = db.session.query(Task).filter_by(priority=priority,
                                                 chat=chat).order_by(Task.id)

        for task in query.all():
            msg_user += '{}[[{}]] {}\n'.format(ARROW, task.id, task.name)

        return msg_user

    def task_settings_msg(self, chat, msg_user):
        msg_user += MEMO + ' _Status_\n'
        msg_user += self.task_status('TODO', chat)
        msg_user += self.task_status('DOING', chat)
        msg_user += self.task_status('DONE', chat)

        msg_user += '\n' + LIGHT + ' *PRIORITY*\n'
        msg_user += self.task_priority('high', chat)
        msg_user += self.task_priority('medium', chat)
        msg_user += self.task_priority('low', chat)
        return msg_user

    def list(self, command, msg, chat):
        '''
        Lista todas tasks suas prioridades, status e duedates
        '''
        msg_user = ''
        msg_user += CLIPBOARD + ' Task List\n'
        query = db.session.query(Task).filter_by(parents='',
                                                 chat=chat).order_by(Task.id)
        for task in query.all():
            icon = NEW
            if self.task_condition(task.status, 'DOING'):
                icon = CLOCK
            elif self.task_condition(task.status, 'DONE'):
                icon = CHECK
            elif self.task_condition(task.priority, 'priority'):
                icon = LIGHT
            if task.duedate:
                msg_user += '[[{}]] {} {} {}{}\n'.format(task.id,
                                                         icon, task.name,
                                                         CALENDAR,
                                                         datetime.strptime\
                                                         (str(task.duedate),\
                                                         '%Y-%m-%d')\
                                                         .strftime('%d/%m/%Y'))
            else:
                msg_user += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
            msg_user += self.deps_text(task, chat)

        self.send_message(msg_user, chat)
        msg_user = ''
        msg_user = self.task_settings_msg(chat,msg_user)
        self.send_message(msg_user, chat)

    def search_parent(self, task, target, chat):
        '''
        Busca os pais de uma task utilizando recursividade
        '''
        if not task.parents == '':
            parent_id = task.parents.split(',')
            parent_id.pop()

            numbers = [int(id) for id in parent_id]

            if target in numbers:
                return False
            else:
                parent = self.query_one(numbers[0], chat)
                return self.search_parent(parent, target, chat)

        return True

    def dependson(self, command, msg, chat):
        '''
        Adiciona dependência a uma task
        '''
        text = ''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if msg is not None:
                if len(msg[i].split()) > 1:
                    text = msg[i].split()[1]
                msg_indice = msg[i].split()[0]

            if self.check_msg_not_exists(msg_indice):
                self.msg_no_task(chat)
            else:
                task_id = int(msg_indice)

                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue

                if text == '':
                    for i in task.dependencies.split(',')[:-1]:
                        i = int(i)
                        q = db.session.query(Task).filter_by(id=i,
                                                             chat=chat)
                        t = q.one()
                        t.parents = t.parents.replace('{},'
                                                      .format(task.id), '')

                    task.dependencies = ''
                    self.send_message("Dependencies removed from task {}"
                                      .format(task_id), chat)
                else:
                    for depid in text.split(' '):
                        if not depid.isdigit():
                            self.send_message("All dependencies ids must be"
                                              " numeric, and not {}"
                                              .format(depid), chat)
                        else:
                            depid = int(depid)

                            try:
                                taskdep = self.query_one(depid, chat)

                                if self.search_parent(task, taskdep.id, chat):
                                    taskdep.parents += str(task.id) + ','
                                else:
                                    self.send_message("Essa tarefa já é filha"
                                                      " da sub tarefa", chat)
                                    break
                            except sqlalchemy.orm.exc.NoResultFound:
                                self.task_not_found_msg(task_id, chat)
                                continue
                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','

                db.session.commit()
                text_message = 'Task {} dependencies up to date'
                print('\nchat:',chat)
                self.send_message(text_message.format(task_id), chat)

    def priority(self, command, msg, chat):
        '''
        Adiciona a prioridade a uma task
        '''
        text = ''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if msg is not None:
                if len(msg[i].split()) > 1:
                    text = msg[i].split()[1]
                msg_indice = msg[i].split()[0]

            if self.check_msg_not_exists(msg_indice):
                self.msg_no_task(chat)
            else:
                task_id = int(msg_indice)
                try:
                    task = self.query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue
                if text == '':
                    task.priority = ''
                    self.send_message("_Cleared_ all priorities from task {}"
                                      .format(task_id), chat)
                else:
                    if text.lower() not in ['high', 'medium', 'low']:
                        self.send_message("The priority *must be* one of the "
                                          "following: high, medium, low", chat)
                    else:
                        task.priority = text.lower()
                        self.send_message("*Task {}* priority has priority "
                                          "*{}*".format(task_id, text.lower()),
                                          chat)
                db.session.commit()

    def correct_date(self, text):
        '''
        Retorna True caso o formato de data seja válido, False caso contrário
        '''
        try:
            datetime.strptime(text, '%d/%m/%Y')
            return True
        except ValueError:
            return False

    def duedate(self, command, msg, chat):
        '''
        Define a duedate de uma task
        '''
        text = ''
        msg = self.strip_message(msg)
        for i in range(len(msg)):
            if msg is not None:
                if len(msg[i].split()) > 1:
                    text = msg[i].split()[1]
                msg_indice = msg[i].split()[0]

            if self.check_msg_not_exists(msg_indice):
                self.msg_no_task(chat)
            else:
                task_id = int(msg_indice)
                print('task_id', task_id)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    self.task_not_found_msg(task_id, chat)
                    continue

                if text == '':
                    task.duedate = None
                    self.send_message("_Cleared_ all duedates"
                                      " from task {}".format(task_id), chat)
                else:
                    if not self.correct_date(text):
                        self.send_message("The duedate *must follow* "
                                          "the pattern: dd/mm/aaaa", chat)
                    else:
                        task.duedate = datetime.strptime(text, '%d/%m/%Y')
                        self.send_message("*Task {}* duedate: *{}*"
                                          .format(task_id, text), chat)
                db.session.commit()

    def handle_updates(self, updates):
        '''
        Loop em que todas funções do bot são realizadas
        '''
        for update in updates['result']:
            if 'message' in update:
                message = update['message']
            elif 'edited_message' in update:
                message = update['edited_message']
            else:
                print('Can\'t process! {}'.format(update))
                return
            command = message['text'].split(" ", 1)[0]
            msg = ''
            if len(message['text'].split(" ", 1)) > 1:
                msg = message['text'].split(" ", 1)[1].strip()
            chat = message['chat']['id']
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
                self.send_message("Welcome! Here is msg_user list"
                                  " of things you can do.", chat)
                self.send_message(self.HELP, chat)
            elif command == '/help':
                self.send_message("Here is msg_user list"
                                  " of things you can do.", chat)
                self.send_message(self.HELP, chat)
            else:
                self.send_message("I'm sorry dave. I'm afraid"
                                  " I can't do that.", chat)
