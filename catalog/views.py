from asyncio.log import logger
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseServerError
from django.core.cache import cache
import urllib.request, urllib.error, json
from datetime import datetime
import os

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

