import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            print("Unauthenticated user rejected")
            await self.close()
            return

        # Sort usernames to ensure consistency (e.g., chat_admin_sita or chat_sita_admin)
        usernames = sorted([self.user.username, self.room_name])
        self.room_group_name = f'chat_{usernames[0]}_{usernames[1]}'
        
        print(f"User {self.user.username} joining {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        room_name = text_data_json['room_name']
        
        print(f"Received message: {message} from {username}")
        await self.save_message(username, room_name, message)
        
        print(f"Broadcasting to {self.room_group_name}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': username,
                'timestamp': timezone.now().strftime('%H:%M')
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']
        
        print(f"Sending to client: {message} from {sender}")
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def save_message(self, username, room_name, message):
        try:
            sender = User.objects.get(username=username)
            receiver = User.objects.get(username=room_name)
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message
            )
            print(f"Saved message: {message} from {username} to {room_name}")
        except User.DoesNotExist as e:
            print(f"User not found: {e}")