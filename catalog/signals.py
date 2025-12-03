from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Post, Notification


def get_thread_participants(thread, exclude_user=None):
    """
    Get all unique participants in a thread efficiently.
    Participants include:
    - Thread author
    - All users who have posted in the thread

    Args:
        thread: Thread instance
        exclude_user: User to exclude (typically the commenter)

    Returns:
        Set of user IDs
    """
    participant_ids = set()

    # Add thread author
    if thread.author_id:
        participant_ids.add(thread.author_id)

    # Get all post authors in this thread (single query)
    post_author_ids = Post.objects.filter(
        thread=thread
    ).exclude(
        author__isnull=True
    ).values_list('author_id', flat=True).distinct()

    participant_ids.update(post_author_ids)

    # Exclude the commenter
    if exclude_user and exclude_user.id in participant_ids:
        participant_ids.discard(exclude_user.id)

    return participant_ids


@receiver(post_save, sender=Post)
def create_post_notifications(sender, instance, created, **kwargs):
    """
    Create notifications for all thread participants when a new post is created.

    Triggers when:
    - A new post is created (created=True)
    - The post has an author (not anonymous)

    Notifies:
    - Thread author
    - All users who have previously posted in the thread
    - EXCLUDES the post author (commenter) themselves
    """
    if not created:
        return  # Only notify on new posts, not edits

    if not instance.author:
        return  # Skip if no author

    thread = instance.thread
    actor = instance.author

    # Get all participants except the commenter
    participant_ids = get_thread_participants(thread, exclude_user=actor)

    if not participant_ids:
        return  # No one to notify

    # Build notification message
    title = thread.title[:50]
    if len(thread.title) > 50:
        title += "..."
    message = f"{actor.username} posted in '{title}'"

    # Bulk create notifications for all participants
    notifications = [
        Notification(
            recipient_id=user_id,
            notification_type='new_post',
            post=instance,
            actor=actor,
            message=message,
        )
        for user_id in participant_ids
    ]

    Notification.objects.bulk_create(notifications)
