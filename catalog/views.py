from asyncio.log import logger
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseServerError
from django.core.cache import cache
from django.contrib import messages
import urllib.request, urllib.error, json
from datetime import datetime
import os
from django.db.models import Q

# Create your views here.

from .models import Category, Thread, Post, UserProfile, Notification
from .forms import UserRegistrationForm, UserProfileRegistrationForm
from .mixins import ModeratorRequiredMixin, is_moderator


def index(request):
    """View function for home page of forum site."""

    # Generate counts of main objects
    num_categories = Category.objects.all().count()
    num_threads = Thread.objects.all().count()
    num_posts = Post.objects.all().count()
    num_users = User.objects.count()

    # Get recent threads
    recent_threads = Thread.objects.all().order_by('-created_date')[:5]

    context = {
        'num_categories': num_categories,
        'num_threads': num_threads,
        'num_posts': num_posts,
        'num_users': num_users,
        'recent_threads': recent_threads,
    }


    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


def thread_search(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    # Starting with all the current threads
    threads = Thread.objects.all().select_related("category", "author")

    if query:
        threads = threads.filter(
            Q(title__icontains=query) | 
            Q(post__content__icontains=query)
        ).distinct()

    if category_id:
        threads = threads.filter(category_id=category_id)

    categories = Category.objects.all().order_by("name")

    context = {
        "threads": threads,
        "query": query,
        "categories": categories,
        "selected_category": category_id,
    }

    return render(request, "catalog/search_results.html", context)


def help_page(request):
    """View function for help page."""
    return render(request, 'catalog/help.html')


class CategoryListView(generic.ListView):
    model = Category
    paginate_by = 10


class CategoryDetailView(generic.DetailView):
    model = Category


class ThreadListView(generic.ListView):
    model = Thread
    paginate_by = 20


class ThreadDetailView(generic.DetailView):
    model = Thread
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Increment view count
        thread = self.get_object()
        thread.views += 1
        thread.save(update_fields=['views'])
        return context


class UserProfileDetailView(generic.DetailView):
    model = UserProfile
    template_name = 'catalog/userprofile_detail.html'
    context_object_name = 'userprofile'


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """Allow a user to edit their own profile."""
    model = UserProfile
    fields = ['bio', 'location', 'website', 'avatar']
    template_name = 'catalog/userprofile_form.html'

    def get_success_url(self):
        return reverse_lazy('profile-detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        # Only allow the owner of the profile or staff to edit
        user = self.request.user
        obj = self.get_object()
        return bool(user and (user.is_staff or obj.user == user))


def time_proxy(request):
    """Proxy endpoint for the TimezoneDB API.

    Clients should call this endpoint instead of the external API to avoid
    CORS/rate-limit/connectivity issues.
    
    Uses TimezoneDB API to get timezone information based on coordinates or zone name.
    If no parameters provided, defaults to UTC timezone.
    """
    # Get optional query parameters for timezone lookup
    zone = request.GET.get('zone', 'UTC')  # e.g., 'America/New_York'
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    try:
        # Build API URL based on parameters
        api_key = os.environ.get('TIMEZONEDB_API_KEY')
        if not api_key:
            raise Exception("TIMEZONEDB_API_KEY environment variable not set")
        
        base_url = 'http://api.timezonedb.com/v2.1/get-time-zone'
        
        if lat and lng:
            # Get timezone by coordinates
            api_url = f'{base_url}?key={api_key}&format=json&by=position&lat={lat}&lng={lng}'
        else:
            # Get timezone by zone name
            api_url = f'{base_url}?key={api_key}&format=json&by=zone&zone={zone}'
        
        with urllib.request.urlopen(api_url, timeout=5) as resp:
            body = resp.read()
            payload = json.loads(body.decode())
            
            # Check if API request was successful
            if payload.get('status') != 'OK':
                raise Exception(f"TimezoneDB API error: {payload.get('message', 'Unknown error')}")
            
            # Format the response to match expected structure
            result = {
                'datetime': payload.get('formatted'),  # Pre-formatted datetime string
                'timestamp': payload.get('timestamp'),  # Unix timestamp
                'timezone': payload.get('zoneName'),
                'abbreviation': "EST",
                'gmtOffset': payload.get('gmtOffset'),  # Offset from GMT in seconds
                'dst': payload.get('dst'),  # Whether DST is active (0 or 1)
                'zoneStart': payload.get('zoneStart'),  # Unix timestamp of zone start
                'zoneEnd': payload.get('zoneEnd'),  # Unix timestamp of zone end
                'countryCode': payload.get('countryCode'),
                'countryName': payload.get('countryName'),
            }
            
            return JsonResponse(result)
    except Exception as e:
        # On failure, fall back to server UTC time so clients can keep working.
        fallback = {
            'datetime': datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(datetime.now(datetime.timezone.utc).timestamp()),
            'abbreviation': 'UTC',
            'timezone': 'UTC',
            'gmtOffset': 0,
            'dst': 0,
            'fallback': True,
            'error': str(e),
        }
        return JsonResponse(fallback, status=200)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    """Simple list view for Django users.

    Provides a paginated list of users. Template should be placed at
    `catalog/user_list.html` if customized.
    """
    model = User
    template_name = 'catalog/user_list.html'
    paginate_by = 5
    ordering = ['username']  # Order by username alphabetically
    # When the test fails, redirect to the login page instead of raising 403
    # (AccessMixin.handle_no_permission will redirect to login when raise_exception is False)
    raise_exception = False

    def test_func(self):
        # Only allow staff or superuser to view the users list
        user = self.request.user
        return bool(user and (user.is_staff or user.is_superuser))

class UserDetailView(generic.DetailView):
    model = User
    template_name = 'catalog/userprofile_detail.html'


class MyPostsListView(LoginRequiredMixin, generic.ListView):
    """List view showing all posts by the logged-in user."""
    model = Post
    template_name = 'catalog/my_posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        # Only show posts by the current user
        return Post.objects.filter(author=self.request.user).order_by('-created_date')


class PostCreateView(LoginRequiredMixin, generic.CreateView):
    """Create a new post in a thread."""
    model = Post
    fields = ['thread', 'content']
    template_name = 'catalog/post_form.html'
    
    def form_valid(self, form):
        # Set the author to the current user
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to the thread detail page
        return reverse_lazy('thread-detail', kwargs={'pk': self.object.thread.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """Update an existing post."""
    model = Post
    fields = ['content']
    template_name = 'catalog/post_form.html'
    
    def form_valid(self, form):
        # Mark the post as edited
        form.instance.is_edited = True
        return super().form_valid(form)
    
    def test_func(self):
        # Only allow the author or staff to edit
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_success_url(self):
        # Redirect to the thread detail page
        return reverse_lazy('thread-detail', kwargs={'pk': self.object.thread.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """Delete a post."""
    model = Post
    template_name = 'catalog/post_confirm_delete.html'
    
    def test_func(self):
        # Only allow the author or staff to delete
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_success_url(self):
        # Redirect to my posts page
        return reverse_lazy('my-posts')


@login_required
def post_bulk_delete(request):
    """Delete multiple posts at once."""
    if request.method == 'POST':
        post_ids = request.POST.getlist('post_ids')
        if post_ids:
            # Only delete posts that belong to the current user
            posts_to_delete = Post.objects.filter(
                pk__in=post_ids,
                author=request.user
            )
            count = posts_to_delete.count()
            posts_to_delete.delete()
            messages.success(request, f'Successfully deleted {count} post(s).')
        else:
            messages.warning(request, 'No posts selected for deletion.')
    
    return redirect('my-posts')


def register_step1(request):
    """Step 1: Create user account."""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Automatically create an empty UserProfile for this user
            UserProfile.objects.create(user=user)
            
            # Store user ID in session for step 2
            request.session['registration_user_id'] = user.id
            
            # Redirect to step 2
            return redirect('register-step2')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register_step1.html', {'form': form})


def register_step2(request):
    """Step 2: Update user profile details."""
    # Check if user came from step 1
    user_id = request.session.get('registration_user_id')
    if not user_id:
        messages.error(request, 'Please complete step 1 first.')
        return redirect('register-step1')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid registration session.')
        return redirect('register-step1')
    
    # Get the user's profile (should always exist now)
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        # Fallback: create profile if it doesn't exist for some reason
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        form = UserProfileRegistrationForm(request.POST, instance=profile)
        if form.is_valid():
            # Update the profile with user's input
            form.save()
            
            # Log the user in
            login(request, user)
            
            # Clear the session
            del request.session['registration_user_id']
            
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('index')
    else:
        # Pre-populate form with existing profile data (will be empty fields)
        form = UserProfileRegistrationForm(instance=profile)
    
    context = {
        'form': form,
        'username': user.username,
    }
    return render(request, 'registration/register_step2.html', context)


def register_skip(request):
    """Allow users to skip step 2 and complete their profile later."""
    if request.method == 'POST':
        user_id = request.session.get('registration_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # Log the user in
                login(request, user)
                # Clear the session
                del request.session['registration_user_id']
                messages.info(request, f'Welcome {user.username}! You can complete your profile anytime from your profile page.')
            except User.DoesNotExist:
                pass
    
    return redirect('index')


@login_required
def toggle_dark_mode(request):
    """Toggle dark mode preference for authenticated users."""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            # Toggle the dark mode setting
            profile.dark_mode = not profile.dark_mode
            profile.save(update_fields=['dark_mode'])
            return JsonResponse({'dark_mode': profile.dark_mode})
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user, dark_mode=True)
            return JsonResponse({'dark_mode': profile.dark_mode})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ============================================
# NOTIFICATION VIEWS
# ============================================

class NotificationListView(LoginRequiredMixin, generic.ListView):
    """Display all notifications for the current user."""
    model = Notification
    template_name = 'catalog/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('actor', 'post', 'post__thread')


@login_required
def notification_mark_read(request, pk):
    """Mark a single notification as read and redirect to the post."""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    # Redirect to the notification target (the post)
    return redirect(notification.get_absolute_url())


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read for the current user."""
    if request.method == 'POST':
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        messages.success(request, f'Marked {updated} notification(s) as read.')

    return redirect('notifications')


# ============================================
# AI SUMMARIZE VIEW
# ============================================

@login_required
def summarize_thread(request, pk):
    """Generate an AI summary of a thread using Claude."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    thread = get_object_or_404(Thread, pk=pk)

    # Gather thread info
    posts = thread.post_set.select_related('author').order_by('created_date')

    # Build the content to summarize
    thread_content = f"Thread Title: {thread.title}\n"
    thread_content += f"Category: {thread.category.name}\n"
    thread_content += f"Author: {thread.author.username}\n"
    thread_content += f"Created: {thread.created_date}\n\n"
    thread_content += "Posts:\n"

    for i, post in enumerate(posts[:20], 1):  # Limit to first 20 posts
        author_name = post.author.username if post.author else 'Anonymous'
        thread_content += f"\n--- Post {i} by {author_name} ---\n"
        thread_content += post.content[:500]  # Limit each post to 500 chars
        if len(post.content) > 500:
            thread_content += "..."

    try:
        import anthropic

        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'AI service not configured'}, status=500)

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"Please provide a brief, 2-3 sentence summary of what this forum thread is about. Focus on the main topic and key points discussed.\n\n{thread_content}"
                }
            ]
        )

        summary = message.content[0].text

        return JsonResponse({'summary': summary})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# MODERATOR VIEWS
# ============================================

class ModeratorDashboardView(ModeratorRequiredMixin, generic.TemplateView):
    """Main dashboard for moderators."""
    template_name = 'catalog/moderator_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent posts for moderation
        context['recent_posts'] = Post.objects.all().select_related('author', 'thread').order_by('-created_date')[:20]
        
        # Statistics
        context['total_posts'] = Post.objects.count()
        context['total_threads'] = Thread.objects.count()
        context['total_users'] = User.objects.count()
        
        return context


class ModeratorPostListView(ModeratorRequiredMixin, generic.ListView):
    """List all posts for moderator review."""
    model = Post
    template_name = 'catalog/moderator_post_list.html'
    context_object_name = 'posts'
    paginate_by = 20
    ordering = ['-created_date']
    
    def get_queryset(self):
        return Post.objects.all().select_related('author', 'thread')


class ModeratorPostDeleteView(ModeratorRequiredMixin, generic.DeleteView):
    """Allow moderators to delete any post."""
    model = Post
    template_name = 'catalog/moderator_post_delete.html'
    success_url = reverse_lazy('moderator-dashboard')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Post deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_moderator)
def moderator_bulk_delete(request):
    """Delete multiple posts at once (moderator only)."""
    if request.method == 'POST':
        post_ids = request.POST.getlist('post_ids')
        if post_ids:
            posts_to_delete = Post.objects.filter(pk__in=post_ids)
            count = posts_to_delete.count()
            posts_to_delete.delete()
            messages.success(request, f'Successfully deleted {count} post(s).')
        else:
            messages.warning(request, 'No posts selected for deletion.')
    
    return redirect('moderator-dashboard')
