import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from game.gamestate import Gamestate
# from channels_presence.models import Room
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
        self.room_name, {"type": "getRoomDetails", "data":{"message":"Someone Left","RoomMembers":userDict[self.room_name]}}
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
                return
            else:
                raise Exception("User not authorized to start the game")
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, {"type":"getRoomDetails","data":message}
        )

    def onStartGame(self,event):
        print(event)
        event["gameState"]=Gamestate(event["data"]["userArr"][self.room_name],event["data"]["totalMegaRounds"])
        self.send(text_data=json.dumps(event))

    # Called when group_send is called or message is sent to frontend
    def getRoomDetails(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))

