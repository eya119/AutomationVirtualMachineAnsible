from django.urls import path, re_path
from . import consumers  # Import your consumers

websocket_urlpatterns = [
    path('ws/vm-list/', consumers.VMListConsumer.as_asgi()),
    path('ws/vm-detail/', consumers.VMDetailConsumer.as_asgi()),
   # path(r'^ws/backup/(?P<channel_name>\w+)/$', consumers.BackupConsumer.as_asgi()),
]
