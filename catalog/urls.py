from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('help/', views.help_page, name='help'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('category/<int:pk>', views.CategoryDetailView.as_view(), name='category-detail'),
    path('threads/', views.ThreadListView.as_view(), name='threads'),
    path('thread/<int:pk>', views.ThreadDetailView.as_view(), name='thread-detail'),
    path('profile/<int:pk>', views.UserProfileDetailView.as_view(), name='profile-detail'),
    path('profile/<int:pk>/edit/', views.UserProfileUpdateView.as_view(), name='profile-edit'),
    path('api/time/', views.time_proxy, name='time-proxy'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('my-posts/', views.MyPostsListView.as_view(), name='my-posts'),
    path('post/new/', views.PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post-edit'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post-delete'),
    path('post/bulk-delete/', views.post_bulk_delete, name='post-bulk-delete'),
    path('search/', views.thread_search, name='thread-search'),
    path('register/step1/', views.register_step1, name='register-step1'),
    path('register/step2/', views.register_step2, name='register-step2'),
    path('register/skip/', views.register_skip, name='register-skip'),
]
