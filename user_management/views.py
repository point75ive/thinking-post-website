from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse


def sign_up(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("user_management:login"))
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/sign_up.html", {"form": form})



def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Check the user's role and redirect accordingly
            if user.roles.filter(name='HOD').exists():
                return redirect(request.POST.get('next', reverse('dashboard')))
            elif user.roles.filter(name='Lecturer').exists():
                return redirect(request.POST.get('next', reverse('dashboard')))
            elif user.roles.filter(name='Registrar').exists():
                return redirect(request.POST.get('next', reverse('dashboard')))
            elif user.roles.filter(name='Student').exists():
                return redirect(request.POST.get('next', reverse('dashboard')))
            else:
                # Default fallback for users without a role
                return redirect(request.POST.get('next', reverse('dashboard')))
        else:
            messages.error(request, 'Invalid username or password.')
    
    # Pass the 'next' parameter to the template
    next_url = request.GET.get('next', '')
    return render(request, 'registration/login.html', {'next': next_url})


def home(request):
    return render(request, 'users/home.html')

def about(request):
    return render(request, 'users/about.html')

def contact(request):
    return render(request, 'users/contact.html')

