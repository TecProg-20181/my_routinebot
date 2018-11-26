#!/usr/bin/env python3

import time
from handletask import HandleTask

class TaskBot():
    if __name__ == '__main__':
        last_update_id = None
        task = HandleTask()
        while True:
            print('Updates')
            print(last_update_id)
            updates = task.get_updates(last_update_id)

            if len(updates['result']) > 0:
                last_update_id = task.get_last_update_id(updates) + 1
                task.handle_updates(updates)

            time.sleep(0.5)

taskbot = TaskBot()