from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
import uuid
from datetime import date

# Create your models here.

class Category(models.Model):
    """Model representing a forum category."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter a forum category (e.g. General Discussion, Technology, Sports, etc.)"
    )
    description = models.TextField(
        max_length=500,
        help_text="Enter a brief description of this category"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='category_name_case_insensitive_unique',
                violation_error_message = "Category already exists (case insensitive match)"
            ),
        ]

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular category instance."""
        return reverse('category-detail', args=[str(self.id)])
    
    def thread_count(self):
        """Returns the number of threads in this category."""
        return self.thread_set.count()


class Thread(models.Model):
    """Model representing a forum thread (discussion topic)."""
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='threads')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False, help_text="Pin this thread to the top")
    is_locked = models.BooleanField(default=False, help_text="Lock this thread (no new posts)")
    views = models.IntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-updated_date']
        permissions = (("can_moderate_thread", "Can view all threads and moderate"),)

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this thread."""
        return reverse('thread-detail', args=[str(self.id)])
    
    def post_count(self):
        """Returns the number of posts in this thread."""
        return self.post_set.count()
    
    def last_post(self):
        """Returns the last post in this thread."""
        return self.post_set.order_by('-created_date').first()


class Post(models.Model):
    """Model representing a post within a thread."""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posts')
    content = models.TextField(max_length=10000, help_text="Enter your post content")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_date']

    def __str__(self):
        """String for representing the Model object."""
        return f'Post by {self.author} in {self.thread.title}'

    def get_absolute_url(self):
        """Returns the URL to access this post."""
        return reverse('post-detail', args=[str(self.id)])


class UserProfile(models.Model):
    """Extended user profile for forum users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, help_text="Tell us about yourself")
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    avatar = models.CharField(max_length=500, blank=True, null=True, help_text="Avatar URL")
    
    def __str__(self):
        """String for representing the Model object."""
        return f'{self.user.username} Profile'
    
    def post_count(self):
        """Returns the number of posts by this user."""
        return self.user.posts.count()
    
    def thread_count(self):
        """Returns the number of threads created by this user."""
        return self.user.threads.count()


# Library models for the forms tutorial

class Genre(models.Model):
    """Model representing a book genre."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)"
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular genre instance."""
        return reverse('genre-detail', args=[str(self.id)])


class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
                           unique=True,
                           help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)")

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular language instance."""
        return reverse('language-detail', args=[str(self.id)])


class Author(models.Model):
    """Model representing an author."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name}, {self.first_name}'


class Book(models.Model):
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.RESTRICT, null=True)
    summary = models.TextField(
        max_length=1000, help_text="Enter a brief description of the book")
    isbn = models.CharField('ISBN', max_length=13,
                           unique=True,
                           help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn'
                                     '">ISBN number</a>')
    genre = models.ManyToManyField(
        Genre, help_text="Select a genre for this book")
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """Create a string for the Genre. This is required to display genre in Admin."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'


class BookInstance(models.Model):
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                         help_text="Unique ID for this particular book across whole library")
    book = models.ForeignKey(Book, on_delete=models.RESTRICT, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='m',
        help_text='Book availability',
    )

    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'

    @property
    def is_overdue(self):
        """Determines if the book is overdue based on due date and current date."""
        if self.due_back and date.today() > self.due_back:
            return True
        return False