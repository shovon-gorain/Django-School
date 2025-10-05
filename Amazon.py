# single_file_blog.py
import os
import sys
from django.conf import settings
from django.urls import path
from django.core.wsgi import get_wsgi_application
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone

# Configure Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='django-insecure-your-secret-key-here',
    ROOT_URLCONF=__name__,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'single_file_blog.db',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.admin',
    ],
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ],
    STATIC_URL='/static/',
)

# Create database tables
from django.core.management import execute_from_command_line
from django.db.utils import OperationalError

try:
    from django.db import connections
    for conn in connections.all():
        conn.ensure_connection()
except OperationalError:
    pass

# Define Models
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        app_label = __name__

# Register models with admin
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_date', 'published_date']
    list_filter = ['created_date', 'published_date']
    search_fields = ['title', 'content']

# Create views
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def home(request):
    return HttpResponse("""
    <html>
        <head>
            <title>Single File Django Blog</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .post { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Welcome to Single File Django Blog</h1>
            <p>This entire Django application runs from a single Python file!</p>
            <ul>
                <li><a href="/posts/">View All Posts</a></li>
                <li><a href="/admin/">Admin Panel</a></li>
            </ul>
        </body>
    </html>
    """)

# URL configuration
urlpatterns = [
    path('', home, name='home'),
    path('posts/', post_list, name='post_list'),
    path('post/<int:pk>/', post_detail, name='post_detail'),
    path('admin/', admin.site.urls),
]

# Create templates as strings (in a real app, you'd use template files)
def get_template(template_name):
    templates = {
        'blog/post_list.html': '''
        <html>
        <head>
            <title>Blog Posts</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .post { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .post h2 { margin-top: 0; }
                .date { color: #666; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>Blog Posts</h1>
            <a href="/">← Home</a>
            <hr>
            {% for post in posts %}
            <div class="post">
                <h2><a href="/post/{{ post.id }}/">{{ post.title }}</a></h2>
                <p class="date">Published: {{ post.published_date|date:"M d, Y" }}</p>
                <p>{{ post.content|truncatewords:30 }}</p>
            </div>
            {% empty %}
            <p>No posts yet.</p>
            {% endfor %}
        </body>
        </html>
        ''',
        'blog/post_detail.html': '''
        <html>
        <head>
            <title>{{ post.title }}</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .post { border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
                .date { color: #666; font-size: 0.9em; }
                .actions { margin-top: 20px; }
            </style>
        </head>
        <body>
            <a href="/posts/">← Back to all posts</a>
            <div class="post">
                <h1>{{ post.title }}</h1>
                <p class="date">Published: {{ post.published_date|date:"M d, Y" }}</p>
                <p class="date">Author: {{ post.author.username }}</p>
                <hr>
                <p>{{ post.content|linebreaks }}</p>
            </div>
        </body>
        </html>
        '''
    }
    return templates.get(template_name, '<h1>Template not found</h1>')

# Monkey-patch template loading to use our string templates
from django.template import engines
from django.template.backends.django import DjangoTemplates
import django.template.loaders.app_directories

original_loaders = None

def setup_templates():
    global original_loaders
    
    class StringLoader(django.template.loaders.base.Loader):
        def get_contents(self, origin):
            return get_template(origin.template_name)
        
        def get_template_sources(self, template_name):
            yield Origin(
                name=template_name,
                template_name=template_name,
                loader=self,
            )

    # Replace template loaders
    for engine in engines.all():
        if isinstance(engine, DjangoTemplates):
            original_loaders = engine.engine.loaders
            engine.engine.loaders = [('single_file_blog.StringLoader',)]
            break

class Origin:
    def __init__(self, name, template_name, loader):
        self.name = name
        self.template_name = template_name
        self.loader = loader

# Setup template system
setup_templates()

# WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    # Create database tables
    from django.core.management import execute_from_command_line
    
    if len(sys.argv) > 1 and sys.argv[1] in ['runserver', 'migrate', 'createsuperuser']:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', __name__)
        try:
            execute_from_command_line(sys.argv)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Default: run the development server
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', __name__)
        from django.core.management import execute_from_command_line
        execute_from_command_line([sys.argv[0], 'migrate'])
        execute_from_command_line([sys.argv[0], 'runserver', '8000'])
