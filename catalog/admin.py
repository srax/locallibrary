from django.contrib import admin

# Register your models here.

from .models import Category, Thread, Post, UserProfile, Genre, Language, Author, Book, BookInstance


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


# Library models admin

# Register Genre and Language
admin.site.register(Genre)
admin.site.register(Language)


# Inline for BookInstance in Book
class BooksInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0


# Inline for Books in Author
class BooksInline(admin.TabularInline):
    model = Book
    extra = 0


# Register Author
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]

    inlines = [BooksInline]


# Register Book
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')

    inlines = [BooksInstanceInline]


# Register BookInstance
@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'status', 'borrower', 'due_back', 'id')
    list_filter = ('status', 'due_back')

    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )
