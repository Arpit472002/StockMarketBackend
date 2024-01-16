import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    gameState = {
        'companyValues': {
            'companyId': {
                'companyShareValue': 1000,
                'stocksAvailable': 40
            },
        },
        'userState': {
            'userId': {
                'userName': "arpit",
                'cashInHand': 400000,
                'cashInStocks': 8000000,
                'holdings': {
                    'companyId': 1400000,
                },
                'cardsHeld': ["card1", "card2"]
            },
        },
        'currentMegaRound': 0,
        'currentSubRound': 0,
        'totalMegaRounds': 10,
        'priceBook': {
            'companyId': ["historyStockValues"]
        }
    }

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()
        self.send(text_data=json.dumps({"type":"testing","data": "Hello"}))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
