import json
import asyncio
import websockets
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

class OrderUpdateConsumer(AsyncWebsocketConsumer):
    """
    A Django Channels consumer to manage WebSocket connections for order updates from the DhanHQ API.
    """

    async def connect(self):
        """
        Handles the initial connection to the WebSocket.
        """
        # Extract the username from the WebSocket URL
        self.username = self.scope["url_route"]["kwargs"].get("username")
        
        # Fetch the user's Dhan credentials from the database
        user = await self.get_user_credentials(self.username)
        if user:
            self.dhan_client_id = user.dhan_client_id
            self.dhan_access_token = user.dhan_access_token
            self.order_feed_wss = "wss://api-order-update.dhan.co"
            
            # Accept the WebSocket connection
            await self.accept()
            
            # Start the asynchronous order update connection
            asyncio.create_task(self.connect_order_update())
        else:
            # Reject connection if user not found
            await self.close()

    async def connect_order_update(self):
        """
        Connects to the Dhan WebSocket for order updates.
        """
        async with websockets.connect(self.order_feed_wss) as websocket:
            auth_message = {
                "LoginReq": {
                    "MsgCode": 42,
                    "ClientId": self.client_id,
                    "Token": self.access_token
                },
                "UserType": "SELF"
            }

            # Send authentication message
            await websocket.send(json.dumps(auth_message))
            print(f"Sent subscribe message: {auth_message}")

            # Listen for incoming messages
            async for message in websocket:
                data = json.loads(message)
                await self.handle_order_update(data)

    async def handle_order_update(self, order_update):
        """
        Processes incoming order update messages and sends them to the client.

        Args:
            order_update (dict): The order update message received from the WebSocket.
        """
        if order_update.get('Type') == 'order_alert':
            data = order_update.get('Data', {})
            if "orderNo" in data:
                order_id = data["orderNo"]
                status = data.get("status", "Unknown status")
                update_message = {
                    "status": status,
                    "order_id": order_id,
                    "data": data
                }
                await self.send(text_data=json.dumps(update_message))
                print(f"Status: {status}, Order ID: {order_id}, Data: {data}")
            else:
                await self.send(text_data=json.dumps({"message": "Order Update received", "data": data}))
        else:
            await self.send(text_data=json.dumps({"message": "Unknown message received", "data": order_update}))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes. You can perform cleanup here if necessary.
        """
        print("WebSocket disconnected")

    async def receive(self, text_data):
        """
        Receives messages from the client (if any). This is optional and can be used if the client needs to send data.
        """
        data = json.loads(text_data)
        print(f"Received data from client: {data}")
