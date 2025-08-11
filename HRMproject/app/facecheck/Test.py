
from channels.generic.websocket import AsyncWebsocketConsumer

class Test(AsyncWebsocketConsumer):
    async def connect(self):
        print("User:", self.scope['user'])
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.last_frame = 0
            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        await self.send_json({
            "status": "ok",
        }) 

    async def disconnect(self, code):
        pass