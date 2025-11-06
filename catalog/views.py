from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseServerError
from django.core.cache import cache
import urllib.request, urllib.error, json
from datetime import datetime

# Create your views here.

from .models import Category, Thread, Post, UserProfile


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
    """Proxy endpoint for the worldtime API with simple caching.

    Clients should call this endpoint instead of the external API to avoid
    CORS/rate-limit/connectivity issues. We cache successful responses for
    a short time to reduce outbound calls.
    """
    cache_key = 'worldtimeapi:latest'
    data = cache.get(cache_key)
    if data:
        return JsonResponse(data)

    try:
        with urllib.request.urlopen('https://worldtimeapi.org/api/ip', timeout=5) as resp:
            body = resp.read()
            payload = json.loads(body.decode())
            result = {
                'datetime': payload.get('datetime'),
                'abbreviation': payload.get('abbreviation'),
                'timezone': payload.get('timezone'),
            }
            # cache for 60 seconds
            cache.set(cache_key, result, 60)
            return JsonResponse(result)
    except Exception:
        # On failure, fall back to server UTC time so clients can keep working.
        fallback = {
            'datetime': datetime.now(datetime.timezone.utc).isoformat() + 'Z',
            'abbreviation': 'UTC',
            'timezone': 'UTC',
            'fallback': True,
        }
        return JsonResponse(fallback, status=200)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    """Simple list view for Django users.

    Provides a paginated list of users. Template should be placed at
    `catalog/user_list.html` if customized.
    """
    model = User
    template_name = 'catalog/user_list.html'
    paginate_by = 1
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

