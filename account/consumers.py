import json
from channels.generic.websocket import AsyncWebsocketConsumer
import websockets

class DhanWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        
        # Establish connection with DhanHQ WebSocket API
        self.dhan_ws_url = 'wss://api-order-update.dhan.co'
        self.client_id = '1102930301'  # Replace with your ClientId
        self.token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMyMTg3MTM1LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiaHR0cHM6Ly9wb3N0YmFjay1odWIub25yZW5kZXIuY29tL3Bvc3RiYWNrLWZldGNoLyIsImRoYW5DbGllbnRJZCI6IjExMDI5MzAzMDEifQ.pCRo4yTLWBD4aTM4wTZWueasQp5AdsXiPcvxkeg8jc4GeUbW0eBgwb2MXJQb-x_IER-TrmQlJF37FIk50uNLTw'  # Replace with the actual JWT token

        # Start the connection in a background task
        await self.start_dhan_ws()

    async def disconnect(self, close_code):
        # Close the connection gracefully
        if hasattr(self, 'dhan_ws'):
            await self.dhan_ws.close()

    async def receive(self, text_data):
        # Handle messages sent from the client to WebSocket (Optional)
        pass

    async def start_dhan_ws(self):
        try:
            async with websockets.connect(self.dhan_ws_url) as ws:
                self.dhan_ws = ws
                
                # Send the login authorization message
                auth_message = {
                    "LoginReq": {
                        "MsgCode": 42,
                        "ClientId": self.client_id,
                        "Token": self.token
                    },
                    "UserType": "SELF"
                }
                
                await ws.send(json.dumps(auth_message))
                print("INFO: Sent login request to DhanHQ WebSocket API.")
                
                # Listen for messages from DhanHQ
                async for message in ws:
                    data = json.loads(message)
                    await self.handle_order_update(data)
                    
        except Exception as e:
            print(f"ERROR: Error while connecting to Dhan WebSocket: {e}")

    async def handle_order_update(self, data):
        # Handle the incoming message from DhanHQ (order updates)
        print(f"INFO: Received message: {data}")
        
        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps(data))
