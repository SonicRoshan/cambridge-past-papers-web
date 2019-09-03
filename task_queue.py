"""This file will keep track of all current tasks their timestamp"""
import pickle
import random
import string
from datetime import datetime

def random_string(string_length=32):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))

class Queue():
    """This file will keep track of all current tasks their timestamp"""

    def __init__(self, filename="data.pickle"):
        """Initializes"""
        self.filename = filename

        try:
            file = open("queue_data/{}".format(filename), "rb")
            self.queue_data = pickle.load(file)
            file.close()
        except FileNotFoundError:
            file = open("queue_data/{}".format(filename), "wb")
            self.queue_data = {}
            pickle.dump(self.queue_data, file)
            file.close()

    def update(self):
        """Updates queue data"""
        file = open("queue_data/{}".format(self.filename), "wb")
        pickle.dump(self.queue_data, file)
        file.close()

    def add_task(self):
        """Adds tasks, and returns a unique id"""
        id_found = False
        cur_id = ""
        while not id_found:
            cur_id = random_string()
            id_found = cur_id not in self.queue_data

        self.queue_data[cur_id] = datetime.now()
        self.update()
        return cur_id

    def find_expired_tasks(self):
        """Returnes ids of all expired tasks and deletes them"""
        expired_tasks = []
        for task_id, timestamp in self.queue_data.items():
            cur_time = datetime.now()
            if (cur_time - timestamp).seconds > 1 * 60 * 60:
                expired_tasks.append(task_id)

        for task in expired_tasks:
            del self.queue_data[task]
        self.update()
        return expired_tasks
