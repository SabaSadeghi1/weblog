from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST

from .forms import RegisterForm


def user_register(request):

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

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