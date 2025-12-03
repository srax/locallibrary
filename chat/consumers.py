import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify user is a participant in this conversation
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark messages as read when user connects
        await self.mark_messages_read()

        # Send chat history
        history = await self.get_chat_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': history
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '').strip()

        if not message_content:
            return

        # Save message to database
        message_data = await self.save_message(message_content)

        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Mark message as read if recipient is viewing
        if message['sender_id'] != self.user.id:
            await self.mark_single_message_read(message['id'])

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))

    @database_sync_to_async
    def check_participant(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        return {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'timestamp': message.timestamp.strftime('%b %d, %Y %H:%M'),
            'is_read': message.is_read
        }

    @database_sync_to_async
    def get_chat_history(self):
        conversation = Conversation.objects.get(id=self.conversation_id)
        messages = conversation.message_set.select_related('sender').order_by('timestamp')[:100]
        return [
            {
                'id': msg.id,
                'content': msg.content,
                'sender': msg.sender.username if msg.sender else 'Deleted User',
                'sender_id': msg.sender.id if msg.sender else None,
                'timestamp': msg.timestamp.strftime('%b %d, %Y %H:%M'),
                'is_read': msg.is_read
            }
            for msg in messages
        ]

    @database_sync_to_async
    def mark_messages_read(self):
        conversation = Conversation.objects.get(id=self.conversation_id)
        conversation.message_set.filter(is_read=False).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def mark_single_message_read(self, message_id):
        Message.objects.filter(id=message_id, is_read=False).exclude(sender=self.user).update(is_read=True)
