from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/orders/<str:username>/", consumers.OrderUpdateConsumer.as_asgi()),
]

