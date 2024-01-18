import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# from channels_presence.models import Room
userDict={}
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
            self.room_name, {"type": "chat_message", "message": {"room_name":self.room_name,"userArr":userDict[self.room_name],"room_status":True}}
        )



    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name, self.channel_name
        )
        userDict[self.room_name].remove(self.username)
    

    # Called when message is received from frontend
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if text_data_json["type"]=="DisconnectionRequest":
            self.disconnect()
        elif text_data_json["type"]=="StartGameRequest":
            if userDict[self.room_name][0]==self.username:
                async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type": "start_game", "message": message,"roomMembers":userDict[self.room_name]}
                )
                return
            else:
                raise Exception("User not authorized to start the game")
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, {"type": "chat_message", "message": message}
        )

    def start_game(self,event):
        self.send(text_data=json.dumps(event))

    # Called when group_send is called or message is sent to frontend
    def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
