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
        print(self.username)
        userDict[self.room_name].remove(self.username)
        async_to_sync(self.channel_layer.group_send)(
        self.room_name, {"type": "getRoomDetails", "data":{"message":"Someone Left","userArr":userDict[self.room_name]}}
        )
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )
        print("User removed from list")
    

    # Called when message is received from frontend
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["data"]
        if text_data_json["type"]=="onStartGame":
            if userDict[self.room_name][0]==self.username:
                async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type": "onStartGame", "data":{"userArr":userDict[self.room_name],"totalMegaRounds":message["totalMegaRounds"]}}
                )
            else:
                raise Exception("User not authorized to start the game")
        elif text_data_json["type"]=="buy":
            gameDict[self.room_name].buy(text_data_json["data"]["userId"],text_data_json["data"]["companyId"],text_data_json["data"]["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif text_data_json["type"]=="sell":
            gameDict[self.room_name].sell(text_data_json["data"]["userId"],text_data_json["data"]["companyId"],text_data_json["data"]["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )        
        elif text_data_json["type"]=="pass":
            gameDict[self.room_name].passTransaction(text_data_json["data"]["userId"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif text_data_json["type"]=="crystal":
            gameDict[self.room_name].crystal(text_data_json["data"]["userId"],text_data_json["data"]["crystalType"],text_data_json["data"]["companyId"],text_data_json["data"]["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif text_data_json["type"]=="circuit":
            gameDict[self.room_name].circuit(text_data_json["data"]["companyId"],text_data_json["data"]["circuitType"],text_data_json["data"]["denomination"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif text_data_json["type"]=="startMegaRound":
            gameDict[self.room_name].startMegaRound()
            gameDict[self.room_name].netChangeInCompanyByUsers={}
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif text_data_json["type"]=="getRoomDetails":
            async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type":"getRoomDetails","data":message}
            )

    def onStartGame(self,event):
        response={"type":"onStartGame"}
        gameState=Gamestate(event["data"]["userArr"],event["data"]["totalMegaRounds"])
        gameState.startMegaRound()
        gameDict[self.room_name]=gameState
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


    # Called when group_send is called or message is sent to frontend
    def getRoomDetails(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

