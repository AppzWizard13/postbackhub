"""
ASGI config for trade_wiz project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from your_app.consumers import DhanWebSocketConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_wiz.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/dhan/', DhanWebSocketConsumer.as_asgi()),  # WebSocket endpoint
        ])
    ),
})
