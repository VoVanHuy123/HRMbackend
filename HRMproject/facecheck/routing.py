from django.urls import path
from .consumers import FaceTrackingConsumer
from .Test import Test

websocket_urlpatterns = [
    path("ws/face/", FaceTrackingConsumer.as_asgi()),
    path("ws/test/", Test.as_asgi())
]
 