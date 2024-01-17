from companies import Companies
from cards import getShuffledCards
import random
import math

class Gamestate:
    def __init__(self,playersName, totalMegaRounds = 10):
        noOfPlayers = len(playersName)
        self.companyValues = {}
        self.priceBook = {}
        self.userState = {}
        self.currentMegaRound = 0
        self.currentSubRound = 1
        self.totalMegaRounds = totalMegaRounds
        self.noOfPlayers = noOfPlayers
        self.currentTurn = 1
        self.playerOrder=[]
        self.circuitValues={}
        self.transactions = []

        for i in Companies:
            self.companyValues[i.id]={"companyShareValue":i["startingPrice"],
                                      "stocksAvailable":200000}
            self.priceBook[i.id]=[i["startingPrice"]]
            self.circuitValues[i["id"]] = {
                "UP":None,
                "LOW":None
            }

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
    
    def nextTurn(self):
        self.currentTurn=(self.currentTurn+1)%self.noOfPlayers
        if self.currentTurn==0:
            self.currentSubRound+=1
        if self.currentSubRound==5:
            self.endMegaRound()

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
        self.currentTurn = 0

    def endMegaRound(self):
        self.calculateNewStockPrice()

        for userId in range(self.noOfPlayers):
            self.calculateCashInStocks(userId)
        
        if self.totalMegaRounds == self.currentMegaRound:
            self.endGame()

    def endGame(self):
        self.findWinner()        
                
    def calculateNewStockPrice(self):
        # CompanyId -> [netChange] |  netChange by a user in a company is being calculated 
        netChangeInCompanyByUsers = {} 
        totalChangeInCompany = [0 for _ in range(7)]
        for i in Companies:
            netChangeInCompanyByUsers[i["id"]]=[0 for _ in range(self.noOfPlayers)]

        for i in range(self.noOfPlayers):
            for card in self.userState[i]["cardsHeld"]:
                if card["type"] == "NORMAL":
                    netChangeInCompanyByUsers[card["companyId"]][i]+=card["netChange"]
        for idx in len(totalChangeInCompany):
            totalChangeInCompany[idx] = sum(netChangeInCompanyByUsers[idx+1])
        
        # Circuit Calculation
        for idx in len(totalChangeInCompany):
            netChange = totalChangeInCompany[idx]
            if netChange>0:
                if self.circuitValues[idx+1]["UP"]!=None and self.circuitValues[idx+1]["UP"]<netChange:
                    netChange = self.circuitValues[idx+1]["UP"]
            elif netChange<0:
                if self.circuitValues[idx+1]["DOWN"]!=None and self.circuitValues[idx+1]["DOWN"]<netChange*-1:
                    netChange = self.circuitValues[idx+1]["DOWN"] * -1
            totalChangeInCompany[idx] = netChange
        
        # priceBook updation and comapnyShareValue updation
        for i in Companies:
            self.priceBook[i["id"]].append(self.companyValues[i["id"]]["companyShareValue"] + totalChangeInCompany[i["id"]-1])
            self.companyValues[i["id"]]["companyShareValue"] = self.priceBook[i["id"]]


    def calculateCashInStocks(self,userId):
        newCashInStock =0
        for company in Companies:
            newCashInStock+=self.userState[userId]["holdings"][company["id"]]*self.companyValues[company["id"]]["companyShareValue"]
        self.userState[userId]["cashInStocks"] = newCashInStock
            


    def buy(self,userId,companyId,numberOfStocks):
        if userId!=self.currentTurn:
            return
        transactionAmount = numberOfStocks*self.companyValues[companyId]["companyShareValue"]
        self.userState[userId]["holdings"][companyId]+=numberOfStocks
        self.userState[userId]["cashInHand"]-=transactionAmount
        self.userState[userId]["cashInStocks"]+=transactionAmount
        self.companyValues[companyId]["stocksAvailable"]-=numberOfStocks
        self.appendTransaction({
            "userId":userId,
            "type":"BUY",
            "companyId": companyId,
            "numberOfStocks": numberOfStocks,
            "stockPrice": self.companyValues[companyId]["companyShareValue"],
            "circuitValue": 0

        })
        self.nextTurn()
        

    def sell(self,userId,companyId,numberOfStocks):
        if userId!=self.currentTurn:
            return
        transactionAmount = numberOfStocks*self.companyValues[companyId]["companyShareValue"]
        self.userState[userId]["holdings"][companyId]-=numberOfStocks
        self.userState[userId]["cashInHand"]+=transactionAmount
        self.userState[userId]["cashInStocks"]-=transactionAmount
        self.companyValues[companyId]["stocksAvailable"]+=numberOfStocks
        self.appendTransaction({
            "userId":userId,
            "type":"SELL",
            "companyId": companyId,
            "numberOfStocks": numberOfStocks,
            "stockPrice": self.companyValues[companyId]["companyShareValue"],
            "circuitValue": 0

        })
        self.nextTurn()


    def circuit(self,companyId, circuitType, denomination):
        self.circuitValues[companyId][circuitType]=denomination
        self.appendTransaction({
            "userId":self.playerOrder[self.currentTurn],
            "type":"CIRCUIT:"+circuitType,
            "companyId": companyId,
            "numberOfStocks": 0,
            "stockPrice": 0,
            "circuitValue": denomination

        })
        self.nextTurn()

    def passTransaction(self,userId):
        self.appendTransaction({
            "userId":userId,
            "type":"PASS",
            "companyId": 0,
            "numberOfStocks": 0,
            "stockPrice": 0,
            "circuitValue": 0

        })
        self.nextTurn()

    def appendTransaction(self,transaction):
        self.transactions.insert(0,transaction)
        if len(self.transactions) > 40:
            self.transactions.pop()

    def crystal(self,userId, crystalType,companyId,numberOfStocks):
        if crystalType=="FRAUD":
            newStockValue = math.floor(int(0.7 * self.companyValues[companyId]["comapanyShareValue"])/5)*5
            transactionAmount = numberOfStocks*newStockValue
            self.userState[userId]["holdings"][companyId]+=numberOfStocks
            self.userState[userId]["cashInHand"]-=transactionAmount
            self.userState[userId]["cashInStocks"]+=transactionAmount
            self.companyValues[companyId]["stocksAvailable"]-=numberOfStocks

            self.appendTransaction({
                "userId":userId,
                "type":"CRYSTAL:FRAUD",
                "companyId": companyId,
                "numberOfStocks": numberOfStocks,
                "stockPrice": newStockValue,
                "circuitValue": 0
            })

        elif crystalType=="DIVIDEND":
            cashValue = self.userState[userId]["holdings"][companyId]*5
            self.userState[userId]["cashInHand"]+=cashValue

            self.appendTransaction({
                "userId":userId,
                "type":"CRYSTAL:DIVIDEND",
                "companyId": companyId,
                "numberOfStocks": self.userState[userId]["holdings"][companyId],
                "stockPrice": cashValue,
                "circuitValue": 0
            })

        elif crystalType=="BONUS_SHARE":
            numberOfHoldings = math.floor(self.userState[userId]["holdings"][companyId] /5000) *1000
            self.userState[userId]["holdings"][companyId] += numberOfHoldings
            self.companyValues[companyId]["stocksAvailable"]-=numberOfHoldings

            self.appendTransaction({
                "userId":userId,
                "type":"CRYSTAL:BONUS_SHARE",
                "companyId": companyId,
                "numberOfStocks": numberOfHoldings,
                "stockPrice": 0,
                "circuitValue": 0
            })

            
        
        elif crystalType=="RIGHT_ISSUE":

            numberOfHoldings = math.floor(self.userState[userId]["holdings"][companyId] /2000) *1000
            transactionAmount = numberOfHoldings*10
            self.userState[userId]["holdings"][companyId] += numberOfHoldings
            self.companyValues[companyId]["stocksAvailable"]-=numberOfHoldings
            self.userState[userId]["cashInHand"]-=transactionAmount
            self.userState[userId]["cashInStocks"]+=transactionAmount

            self.appendTransaction({
                "userId":userId,
                "type":"CRYSTAL:RIGHT_ISSUE",
                "companyId": companyId,
                "numberOfStocks": numberOfHoldings,
                "stockPrice": 10,
                "circuitValue": 0
            })


        elif crystalType=="LOAN_ON_STOCK":
            self.userState[userId]["cashInHand"]+=100000

            self.appendTransaction({
                "userId":userId,
                "type":"CRYSTAL:LOAN_ON_STOCK",
                "companyId": companyId,
                "numberOfStocks": 0,
                "stockPrice": 0,
                "circuitValue": 0
            })



    


