class HashTable:
    def __init__(self):
        self.__table = {}

    def set(self, key, item):
        self.__table[key] = item

    def get(self, key):
        return self.__table[key]

    def remove(self, key):
        self.__table.pop(key)
