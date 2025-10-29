from django.contrib import admin

# Register your models here.

from .models import Category, Thread, Post, UserProfile


# Register Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'thread_count', 'created_date')
    search_fields = ['name', 'description']


# Inline for Posts in Thread
class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = ['author', 'content', 'created_date']
    readonly_fields = ['created_date']


# Register Thread
@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_pinned', 'is_locked', 'created_date', 'views')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_date')
    search_fields = ['title']
    ordering = ['-is_pinned', '-created_date']
    
    inlines = [PostInline]


# Register Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'created_date', 'is_edited')
    list_filter = ('created_date', 'is_edited')
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_date', 'updated_date']


# Register UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'joined_date', 'post_count', 'thread_count')
    search_fields = ['user__username', 'location']
    readonly_fields = ['joined_date']
