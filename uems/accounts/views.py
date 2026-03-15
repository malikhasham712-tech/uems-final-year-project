from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .forms import RegisterForm
from .models import Profile
from events.models import Event  # Import your Event model
import uuid

# Home
def home(request):
    return render(request, 'accounts/home.html')


# Register
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True  # Email verification will control login separately
            user.save()

            role = form.cleaned_data['role']
            verification_token = str(uuid.uuid4())
            profile = Profile.objects.create(user=user, role=role, verification_token=verification_token)

            # Send verification email
            verify_link = request.build_absolute_uri(
                reverse('verify-email', args=[verification_token])
            )

            send_mail(
                subject='Verify your UEMS Account',
                message=f'Click the link to verify your account:\n{verify_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# Verify Email
def verify_email(request, token):
    try:
        profile = Profile.objects.get(verification_token=token)
        profile.email_verified = True
        profile.save()
        messages.success(request, 'Email verified successfully! You can now login.')
    except Profile.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')

    return redirect('login')


# Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                if not user.profile.email_verified:
                    messages.error(request, 'Please verify your email before login.')
                    return redirect('login')
            except Profile.DoesNotExist:
                messages.error(request, 'Profile missing. Contact admin.')
                return redirect('login')

            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'accounts/login.html')


# Dashboard
def dashboard(request):
    user_events = Event.objects.filter(organizer=request.user)  # Only events created by logged-in user
    return render(request, 'accounts/dashboard.html', {'user_events': user_events})


# Logout
def logout_view(request):
    logout(request)
    return redirect('login')