


from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from oauth2_provider.models import AccessToken
import json
from datetime import datetime
from asgiref.sync import sync_to_async

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        protocols = scope.get("subprotocols", [])
        token = None
        # Nếu frontend gửi ["access_token", "<token>"]
        print("protocols: ",protocols)
        if len(protocols) >= 2 and protocols[0] == "access_token":
            token = protocols[1]

        if token:
            try:
                # Chạy ORM trong async
                access_token = await sync_to_async(
                    AccessToken.objects.select_related("user").get
                )(token=token)
                print("access_token",access_token)
                if(access_token): print("vao")
                if access_token.expires > datetime.now(access_token.expires.tzinfo):
                    scope["user"] = access_token.user
                else:
                    scope["user"] = AnonymousUser()
            except AccessToken.DoesNotExist:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)