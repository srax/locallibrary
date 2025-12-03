from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from .models import Conversation, Message


@login_required
def conversation_list(request):
    """Display all conversations for the current user."""
    conversations = request.user.conversations.all().prefetch_related('participants')

    # Build conversation data with other participant and last message
    conversation_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(request.user)

        conversation_data.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    return render(request, 'chat/conversation_list.html', {
        'conversations': conversation_data,
    })


@login_required
def start_conversation(request, user_id):
    """Start or open a conversation with another user."""
    other_user = get_object_or_404(User, id=user_id)

    # Can't start conversation with yourself
    if other_user == request.user:
        return redirect('chat:list')

    # Get or create conversation
    conversation, created = Conversation.get_or_create_conversation(request.user, other_user)

    return redirect('chat:room', conversation_id=conversation.id)


@login_required
def chat_room(request, conversation_id):
    """Display a chat room for a conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Verify user is a participant
    if not conversation.participants.filter(id=request.user.id).exists():
        raise Http404("Conversation not found")

    other_user = conversation.get_other_participant(request.user)

    # Mark messages as read when viewing the room
    conversation.message_set.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return render(request, 'chat/room.html', {
        'conversation': conversation,
        'other_user': other_user,
    })
