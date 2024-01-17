from companies import Companies
from cards import getShuffledCards
import random

class Gamestate:
    def __init__(self,playersName, totalMegaRounds = 10):
        noOfPlayers = len(playersName)
        self.companyValues = {}
        self.priceBook = {}
        self.userState = {}
        self.currentMegaRound = 1
        self.currentSubRound = 1
        self.totalMegaRounds = totalMegaRounds
        self.noOfPlayers = noOfPlayers
        self.currentTurn = 1
        self.playerOrder=[]

        for i in Companies:
            self.companyValues[i.id]={"companyShareValue":i["startingPrice"],
                                      "stocksAvailable":200000}
            self.priceBook[i.id]=[i["startingPrice"]]

        for i in range(noOfPlayers):
            self.playerOrder.append(i)
            self.userState[i] = {
                "id":i,
                "username":playersName[i],
                "cashInHand": 800000,
                "cashInStocks":0,
                "holdings": {},
                "cardsHeld": [],
            }
            for j in Companies:
                self.userState[i]["holdings"][j[["id"]]] = 0
    
    def findWinner(self):
        highestValue = 0
        winnerId = None
        for playerId in range(self.noOfPlayers):
            totalWorth = self.userState[playerId]['cashInHand']
            for company in Companies:
                totalWorth += self.companyValues[company['id']]["companyShareValue"] * self.userState[playerId]['holdings'][company['id']]
            if totalWorth > highestValue:
                highestValue = totalWorth
                winnerId = playerId
        return winnerId
    
    def distributeCardsTo(self):
        shuffledCards = getShuffledCards()
        for i in range(self.noOfPlayers):
            self.userState[i]["cardsHeld"] = shuffledCards[:10]
            shuffledCards= shuffledCards[10:]
    
    def startMegaRound(self):
        random.shuffle(self.playerOrder)
        self.distributeCardsTo()
        self.currentMegaRound+=1
        self.currentSubRound=1
        for i in Companies:
            self.priceBook[i["id"]].append(self.companyValues[i["id"]]["companyShareValue"])

    def endMegaRound(self):
        pass

    def buy(self,userId,companyId,numberOfStocks):
        if userId!=self.currentTurn:
            return
        transactionAmount = numberOfStocks*self.companyValues[companyId]["companyShareValue"]
        self.userState[userId]["holdings"][companyId]+=numberOfStocks
        self.userState[userId]["cashInHand"]-=transactionAmount
        self.userState[userId]["cashInStocks"]+=transactionAmount
        self.companyValues[companyId]["stocksAvailable"]-=numberOfStocks

    def sell(self,userId,companyId,numberOfStocks):
        if userId!=self.currentTurn:
            return
        transactionAmount = numberOfStocks*self.companyValues[companyId]["companyShareValue"]
        self.userState[userId]["holdings"][companyId]-=numberOfStocks
        self.userState[userId]["cashInHand"]+=transactionAmount
        self.userState[userId]["cashInStocks"]-=transactionAmount
        self.companyValues[companyId]["stocksAvailable"]+=numberOfStocks

    def circuit(self,userId,companyId, circuitType, denomination):
        pass

    


