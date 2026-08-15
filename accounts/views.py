from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import User, UserProfile
from .forms import RegisterForm, ProfileForm
from blog.models import BlogPost
from django.contrib.auth.models import Group
from core.models import SiteSettings
from django.utils import timezone


def user_register(request):

    site_settings = SiteSettings.objects.filter(
        singleton_key='global'
    ).first()

    if (
        site_settings
        and not site_settings.registration_enabled
    ):

        return render(
            request,
            'accounts/register_closed.html'
        )
    
    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()
            author_group, created = Group.objects.get_or_create(
                name='Author'
            )

            user_group, created = Group.objects.get_or_create(
                name='User'
            )


            user.groups.add(
                author_group
            )

            user.groups.add(
                user_group
            )
            login(request, user)
            
            return redirect('blog:post_list')

    else:

        form = RegisterForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


def user_login(request):

    error = None

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('blog:post_list')

        else:

            error = 'Username or password is incorrect.'

    return render(
        request,
        'accounts/login.html',
        {'error': error}
    )


@require_POST
def user_logout(request):

    logout(request)

    return redirect('core:landing')

@login_required(login_url='login')
def user_profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    posts = BlogPost.objects.filter(
        author_user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'accounts/profile.html',
        {
            'profile': profile,
            'posts': posts,
        }
    )


@login_required(login_url='login')
def profile_update(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            form.save()

            return redirect('profile')

    else:

        form = ProfileForm(
            instance=profile
        )

    return render(
        request,
        'accounts/profile_update.html',
        {'form': form}
    )


def author_profile(request, username):

    author = get_object_or_404(
        User,
        username=username,
        is_active=True
    )

    profile, created = UserProfile.objects.get_or_create(
        user=author
    )

    posts = BlogPost.objects.filter(
        author_user=author,
        status='published',
        published_at__lte=timezone.now()
    ).order_by(
        '-published_at'
    )

    return render(
        request,
        'accounts/author_profile.html',
        {
            'author': author,
            'profile': profile,
            'posts': posts,
        }
    )