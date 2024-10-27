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
from account import routing  # Change to your app name



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_wiz.settings')
print("000000000000000000000000000000000")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Import your routing
        )
    ),
})
