from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User

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
