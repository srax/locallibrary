from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
    path('room/<int:conversation_id>/', views.chat_room, name='room'),
]
