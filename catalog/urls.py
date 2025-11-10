from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('category/<int:pk>', views.CategoryDetailView.as_view(), name='category-detail'),
    path('threads/', views.ThreadListView.as_view(), name='threads'),
    path('thread/<int:pk>', views.ThreadDetailView.as_view(), name='thread-detail'),
    path('profile/<int:pk>', views.UserProfileDetailView.as_view(), name='profile-detail'),
    path('mythreads/', views.MyThreadsListView.as_view(), name='my-threads'),
    path('moderator/threads/', views.AllThreadsByUserListView.as_view(), name='all-threads-moderator'),
]

# Library URLs
urlpatterns += [
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'),
]

# Book renewal URL for librarians
urlpatterns += [
    path('book/<uuid:pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
]

# All borrowed books view for staff
urlpatterns += [
    path('borrowed/', views.LoanedBooksAllListView.as_view(), name='all-borrowed'),
]

# Author CRUD URLs
urlpatterns += [
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
]
