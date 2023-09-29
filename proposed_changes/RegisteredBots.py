import Bot 
class RegisteredBots:
    def __init__(self):
        self.__bots = {}
        
    def registerBot(self, number, model):
        bot = Bot(number, model)
        self.__bots[number] = bot # add bot 
    
    def getBot(self, number):
        return self.__bots[number] # return bot