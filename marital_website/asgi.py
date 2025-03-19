"""
ASGI config for marital_website project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import marital.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marital_website.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket' : AuthMiddlewareStack(
        URLRouter(
            marital.routing.websocket_urlpatterns
        )
    ),
})
