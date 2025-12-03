from .models import Notification
from chat.models import Message


def notifications(request):
    """
    Context processor to add notification and message data to all templates.

    Provides:
    - unread_notification_count: Integer count of unread notifications
    - recent_notifications: QuerySet of 5 most recent unread notifications
    - unread_messages_count: Integer count of unread chat messages

    Returns empty values for anonymous users.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        recent = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).select_related('actor', 'post', 'post__thread')[:5]

        # Count unread chat messages (messages in conversations where user is a participant,
        # that are not from the user, and are unread)
        unread_messages = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()

        return {
            'unread_notification_count': unread_count,
            'recent_notifications': recent,
            'unread_messages_count': unread_messages,
        }

    return {
        'unread_notification_count': 0,
        'recent_notifications': [],
        'unread_messages_count': 0,
    }
