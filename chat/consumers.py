import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from game.gamestate import Gamestate

userDict={}
gameDict={}
class ChatConsumer(WebsocketConsumer):
    
    def stringToBool(self,string):
        if string=="True":
            return True 
        else: 
            return False

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.queryString=self.scope["query_string"].decode("utf-8")
        self.create, self.join, self.username = self.queryString.split('&')
        self.create = self.stringToBool(self.create[7:])
        self.join = self.stringToBool(self.join[5:])
        self.username = self.username[9:]
        if self.create:
            userList=[]
            userList.append(self.username)
            userDict[self.room_name]=userList
        else:
            try:
                userList=userDict[self.room_name]
                userList.append(self.username)
                if len(userList)>7:
                    raise Exception("Room limit exceeded")
                userDict[self.room_name]=userList
            except:
                raise Exception("Room trying to join does not exist")
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name
        )
        self.accept()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, {"type": "getRoomDetails", "data": {"room_name":self.room_name,"userArr":userDict[self.room_name],"room_status":True}}
        )



    def disconnect(self, close_code=1000):
        # Leave room group
        userDict[self.room_name].remove(self.username)
        async_to_sync(self.channel_layer.group_send)(
        self.room_name, {"type": "getRoomDetails", "data":{"message":"Someone Left","userArr":userDict[self.room_name]}}
        )
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )
    

    # Called when message is received from frontend
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["data"]
        type=text_data_json["type"]
        if type=="onStartGame":
            if userDict[self.room_name][0]==self.username:
                gameState=Gamestate(userDict[self.room_name],message["totalMegaRounds"])
                gameState.startMegaRound()
                gameDict[self.room_name]=gameState
                async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type": "onStartGame", "data":{"userArr":userDict[self.room_name],"totalMegaRounds":message["totalMegaRounds"]}}
                )
            else:
                raise Exception("User not authorized to start the game")
        elif type=="buy":
            gameDict[self.room_name].buy(message["userId"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="sell":
            gameDict[self.room_name].sell(message["userId"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )        
        elif type=="pass":
            gameDict[self.room_name].passTransaction(message["userId"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="crystal":
            gameDict[self.room_name].crystal(message["userId"],message["crystalType"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="circuit":
            gameDict[self.room_name].circuit(message["companyId"],message["circuitType"],message["denomination"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="startMegaRound":
            gameDict[self.room_name].startMegaRound()
            gameDict[self.room_name].netChangeInCompanyByUsers={}
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="getRoomDetails":
            async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type":"getRoomDetails","data":message}
            )
        elif type=="endMegaRound":
            netChange=gameDict[self.room_name].netChangeInCompanyByUsers
            priceBook=gameDict[self.room_name].priceBook
            response={"type":"endMegaRound","data":{"netChange":netChange,"priceBook":priceBook}}
            self.send(json.dumps(response))
        elif type=="endGame":
            response=gameDict[self.room_name].endGame()
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"endGame","data":{"results":response}}
            )

    def onStartGame(self,event):
        response={"type":"onStartGame"}
        gameState=gameDict[self.room_name]
        event=gameState.toJSON()
        event=json.loads(event)
        response["data"]=event
        self.send(text_data=json.dumps(response))

    def transaction(self,event):
        response={"type":"roundInfo"}
        event=event["data"].toJSON()
        event=json.loads(event)
        response["data"]=event
        self.send(text_data=json.dumps(response))

    def endGame(self,event):
        self.send(text_data=json.dumps(event))
    # Called when group_send is called or message is sent to frontend
    def getRoomDetails(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

