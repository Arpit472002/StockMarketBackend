from .companies import Companies
from .cards import getShuffledCards,getCardStack
import random
import math
import pprint
import json

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
        self.currentTurn = 0
        self.playerOrder=[]
        self.circuitValues={}
        self.transactions = []
        self.netChangeInCompanyByUsers={}
        self.adminId=0

        for i in Companies:
            self.companyValues[i["id"]]={"companyShareValue":i["startingPrice"],
                                      "stocksAvailable":200000}
            self.priceBook[i["id"]]=[i["startingPrice"]]
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
                self.userState[i]["holdings"][j["id"]] = 0
    
    def findWinner(self):
        winnerDict={}
        response=[]
        for playerId in range(self.noOfPlayers):
            totalWorth = self.userState[playerId]['cashInHand']+self.userState[playerId]['cashInStocks']
            winnerDict[playerId]=totalWorth
        sorted_winnerDict = dict(sorted(winnerDict.items(), key=lambda x:x[1], reverse=True))
        for i in sorted_winnerDict:
            response.append({"id":i,
                            "username":self.userState[i]['username'],
                            "cashInHand":self.userState[i]['cashInHand'],
                            "cashInStocks":self.userState[i]['cashInStocks']})
        return response
    
    def nextTurn(self):
        self.currentTurn=(self.currentTurn+1)%self.noOfPlayers
        if self.currentTurn==0:
            self.currentSubRound+=1
        if self.currentSubRound==5:
            self.endMegaRound()

    def distributeCardsTo(self):
        # shuffledCards = getShuffledCards()
        Cards,CrystalCards=getCardStack()
        for i in range(self.noOfPlayers):
            self.userState[i]["cardsHeld"] = Cards[6:12]+CrystalCards[:5]
            # shuffledCards= shuffledCards[10:]
            
    
    def startMegaRound(self):
        random.shuffle(self.playerOrder)
        self.distributeCardsTo()
        self.currentMegaRound+=1
        self.currentSubRound=1
        self.currentTurn = 0
        for i in Companies:
            self.circuitValues[i["id"]] = {
                "UP":None,
                "LOW":None
            }


    def endMegaRound(self):
        self.calculateNewStockPrice()

        for userId in range(self.noOfPlayers):
            self.calculateCashInStocks(userId)
        
        if self.totalMegaRounds == self.currentMegaRound:
            self.endGame()

    def endGame(self):
        return self.findWinner()        
                
    def calculateNewStockPrice(self):
        # CompanyId -> [netChange] |  netChange by a user in a company is being calculated 
        self.netChangeInCompanyByUsers = {} 
        totalChangeInCompany = [0 for _ in range(7)]
        for i in Companies:
            self.netChangeInCompanyByUsers[i["id"]]=[0 for _ in range(self.noOfPlayers)]

        for i in range(self.noOfPlayers):
            for card in self.userState[i]["cardsHeld"]:
                if card["type"] == "NORMAL":
                    self.netChangeInCompanyByUsers[card["companyId"]][i]+=card["netChange"]
        for idx in range(len(totalChangeInCompany)):
            totalChangeInCompany[idx] = sum(self.netChangeInCompanyByUsers[idx+1])
        
        # Circuit Calculation
        for idx in range(len(totalChangeInCompany)):
            netChange = totalChangeInCompany[idx]
            if netChange>0:
                if self.circuitValues[idx+1]["UP"]!=None and self.circuitValues[idx+1]["UP"]<netChange:
                    netChange = self.circuitValues[idx+1]["UP"]
            elif netChange<0:
                if self.circuitValues[idx+1]["LOW"]!=None and self.circuitValues[idx+1]["LOW"]<netChange*-1:
                    netChange = self.circuitValues[idx+1]["LOW"] * -1
            totalChangeInCompany[idx] = netChange
        
        # priceBook updation and comapnyShareValue updation
        for i in Companies:
            newPrice=self.companyValues[i["id"]]["companyShareValue"] + totalChangeInCompany[i["id"]-1]
            if newPrice<0:
                newPrice=0
            self.priceBook[i["id"]].append(newPrice)
            self.companyValues[i["id"]]["companyShareValue"] = self.priceBook[i["id"]][-1]


    def calculateCashInStocks(self,userId):
        newCashInStock =0
        for company in Companies:
            newCashInStock+=self.userState[userId]["holdings"][company["id"]]*self.companyValues[company["id"]]["companyShareValue"]
        self.userState[userId]["cashInStocks"] = newCashInStock
            

    def buy_check(self,userId,companyId,numberOfStocks,companyShareValue):
        availableStocks=self.companyValues[companyId]["stocksAvailable"]
        if availableStocks<=numberOfStocks:
            numberOfStocks=availableStocks
        transactionAmount=numberOfStocks*companyShareValue
        cashInHand=self.userState[userId]["cashInHand"]
        if transactionAmount>=cashInHand:
            numberOfStocks=math.floor(cashInHand/(companyShareValue*1000))*1000
        if companyShareValue==0:
            numberOfStocks=0
        return numberOfStocks

    def buy(self,userId,companyId,numberOfStocks):
        if userId!=self.playerOrder[self.currentTurn]:
            return
        companyShareValue=self.companyValues[companyId]["companyShareValue"]
        numberOfStocks=self.buy_check(userId,companyId,numberOfStocks,companyShareValue)
        transactionAmount = numberOfStocks*companyShareValue
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
    
    def sell_check(self,userId,companyId,numberOfStocks,companyShareValue):
        stocks_held=self.userState[userId]["holdings"][companyId]
        if numberOfStocks>=stocks_held:
            numberOfStocks=stocks_held
        if companyShareValue==0:
            numberOfStocks=0
        return numberOfStocks

    def sell(self,userId,companyId,numberOfStocks):
        if userId!=self.playerOrder[self.currentTurn]:
            return
        companyShareValue=self.companyValues[companyId]["companyShareValue"]
        numberOfStocks=self.sell_check(userId,companyId,numberOfStocks,companyShareValue)
        transactionAmount = numberOfStocks*companyShareValue
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

    def crystal(self,userId, crystalType,companyId=1,numberOfStocks=0):
        if crystalType=="FRAUD":
            companyShareValue=self.companyValues[companyId]["companyShareValue"]
            newStockValue = math.floor(int(0.7 * companyShareValue)/5)*5
            numberOfStocks=self.buy_check(userId,companyId,numberOfStocks,newStockValue)
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
            companyShareValue = self.companyValues[companyId]["companyShareValue"]
            if numberOfHoldings>=self.companyValues[companyId]["stocksAvailable"]:
                numberOfHoldings=self.companyValues[companyId]["stocksAvailable"]
            if companyShareValue==0:
                numberOfHoldings=0
            transactionAmount=numberOfHoldings*companyShareValue
            self.userState[userId]["holdings"][companyId] += numberOfHoldings
            self.companyValues[companyId]["stocksAvailable"]-=numberOfHoldings
            self.userState[userId]["cashInStocks"]+=transactionAmount

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
            companyShareValue=self.companyValues[companyId]["companyShareValue"]
            if companyShareValue!=0:
                companyShareValue=10
            numberOfHoldings=self.buy_check(userId,companyId,numberOfHoldings,companyShareValue)
            transactionAmount = numberOfHoldings*companyShareValue
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
        cardToBeRemoved=self.transactions[0]["type"][8:]
        for i in self.userState[userId]["cardsHeld"]:
            if i["type"]=="CRYSTAL":
                if i["crystalType"]==cardToBeRemoved:
                    self.userState[userId]["cardsHeld"].remove(i)
                    break
        self.nextTurn()
    
    def printDetails(self):
        pprint.pprint(
            (
            self.companyValues,
            self.priceBook,
            self.userState,
            self.currentMegaRound,
            self.currentSubRound,
            self.totalMegaRounds,
            self.noOfPlayers,
            self.currentTurn,
            self.playerOrder,
            self.circuitValues,
            self.transactions)
        )
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=False, indent=4)
    def checkIsAdmin(self,leftPlayerIndex):
        if leftPlayerIndex==0:
            self.adminId+=1
# obj = Gamestate(["bhavik","arun","arpit"],1)

# obj.startMegaRound()
# obj.buy(obj.playerOrder[obj.currentTurn],1,5000)
# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.passTransaction(obj.playerOrder[obj.currentTurn])

# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.passTransaction(obj.playerOrder[obj.currentTurn])

# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.crystal(obj.playerOrder[obj.currentTurn],"LOAN_ON_STOCK",1,1000)
# obj.passTransaction(obj.playerOrder[obj.currentTurn])

# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.passTransaction(obj.playerOrder[obj.currentTurn])
# obj.passTransaction(obj.playerOrder[obj.currentTurn])

# obj.printDetails()
