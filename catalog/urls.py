from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('category/<int:pk>', views.CategoryDetailView.as_view(), name='category-detail'),
    path('threads/', views.ThreadListView.as_view(), name='threads'),
    path('thread/<int:pk>', views.ThreadDetailView.as_view(), name='thread-detail'),
    path('profile/<int:pk>', views.UserProfileDetailView.as_view(), name='profile-detail'),
    path('profile/<int:pk>/edit/', views.UserProfileUpdateView.as_view(), name='profile-edit'),
    path('api/time/', views.time_proxy, name='time-proxy'),
    path('users/', views.UserListView.as_view(), name='users'),
]
