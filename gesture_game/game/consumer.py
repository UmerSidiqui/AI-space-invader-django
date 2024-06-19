import json
from channels.generic.websocket import WebsocketConsumer

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        # Handle data received from the client
        self.send(text_data=json.dumps({
            'message': data['message']
        }))
