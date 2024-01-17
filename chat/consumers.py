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
        

    # Message sent by Client is received by Host and sent to other clients
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, {"type": "chat_message", "message": message}
        )

    # Message sent by Host is received by Client
    def chat_message(self, event):
        message = event["message"]
        print(event)
        # Send message to WebSocket
        if event["type"]=="DisconnectionRequest":
            self.disconnect()
        self.send(text_data=json.dumps({"message": message}))
