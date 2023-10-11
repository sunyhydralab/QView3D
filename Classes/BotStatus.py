class BotStatus:
    
    # use this class to retrieve bot by ID and then change the status in the Bot class 
     
    def __init__(self, botDict): # provides an easy way to look up bots / set status. 
        # every time a new bot is created, add it to the DB and also to bot Dict. 
        self.__botDict = botDict

    def getBot(self, id): # id: BotObject 
        return self.__botDict.get(id)
    
    def registerBot(self, bot, id): 
        self.botDict[id] = bot  
    
    def deregisterBot(self, id): 
        self.__botDict.pop(id)
        
    def getBotList(self): 
        return self.__botDict