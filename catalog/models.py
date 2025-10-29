from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

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