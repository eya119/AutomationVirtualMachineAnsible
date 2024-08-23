from django.urls import path
from . import consumers  # Import your consumers

websocket_urlpatterns = [
    path('ws/vm-list/', consumers.VMListConsumer.as_asgi()),
    path('ws/vm-detail/', consumers.VMDetailConsumer.as_asgi()),
]
