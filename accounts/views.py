from django.shortcuts import render, redirect
from .forms import RegisterForm

def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:landing')
    else:
       form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})