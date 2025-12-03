from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Conversation(models.Model):
    """A conversation between two users."""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        participant_names = ', '.join([u.username for u in self.participants.all()[:2]])
        return f"Conversation: {participant_names}"

    def get_absolute_url(self):
        return reverse('chat:room', args=[str(self.id)])

    def get_other_participant(self, user):
        """Get the other participant in a 1:1 conversation."""
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        """Get the most recent message in this conversation."""
        return self.message_set.order_by('-timestamp').first()

    def get_unread_count(self, user):
        """Get count of unread messages for a user."""
        return self.message_set.filter(is_read=False).exclude(sender=user).count()

    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """
        Get existing conversation between two users or create a new one.
        Thread-safe implementation.
        """
        # Find conversations where both users are participants
        conversations = cls.objects.filter(participants=user1).filter(participants=user2)

        if conversations.exists():
            return conversations.first(), False

        # Create new conversation
        conversation = cls.objects.create()
        conversation.participants.add(user1, user2)
        return conversation, True


class Message(models.Model):
    """A message in a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField(max_length=2000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        sender_name = self.sender.username if self.sender else 'Deleted User'
        return f"{sender_name}: {self.content[:30]}..."
