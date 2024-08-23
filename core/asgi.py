# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from django.urls import path
import os

from core import consumers, routing as homerouting

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(homerouting.websocket_urlpatterns)
    ),
})

