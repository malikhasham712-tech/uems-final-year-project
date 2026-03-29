from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from .forms import RegisterForm
from .models import Profile
from events.models import Event
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.contrib.auth.models import User

# ----------------------
# HOME
# ----------------------
def home(request):
    return render(request, 'accounts/home.html')


# ----------------------
# REGISTER
# ----------------------
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True
            user.save()

            role = form.cleaned_data['role']
            verification_token = str(uuid.uuid4())

            Profile.objects.create(
                user=user,
                role=role,
                verification_token=verification_token,
                is_organizer=(role == 'organizer')
            )

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

            messages.success(request, 'Account created! Please verify your email.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# ----------------------
# VERIFY EMAIL
# ----------------------
def verify_email(request, token):
    try:
        profile = Profile.objects.get(verification_token=token)
        profile.email_verified = True
        profile.save()
        messages.success(request, 'Email verified successfully! You can login now.')
    except Profile.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')

    return redirect('login')


# ----------------------
# LOGIN
# ----------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            try:
                if not user.profile.email_verified:
                    messages.error(request, 'Please verify your email before login.')
                    return redirect('login')
            except Profile.DoesNotExist:
                messages.error(request, 'Profile missing. Contact admin.')
                return redirect('login')

            login(request, user)

            # ✅ CHECK IF USER IS ORGANIZER BY EVENT ASSIGNMENT
            if Event.objects.filter(organizer=user).exists():
                return redirect('dashboard')  # organizer view
            else:
                return redirect('student_events')

        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


# ----------------------
# LOGOUT
# ----------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# ----------------------
# DASHBOARD (IMPORTANT FIX)
# ----------------------
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    events = Event.objects.filter(organizer=request.user)

    if events.exists():
        # Organizer interface
        return render(request, 'organizer_dashboard.html', {'events': events})
    else:
        # Student interface
        return render(request, 'student_dashboard.html')


# ----------------------
# HELPER: Assign organizer
# ----------------------
def assign_organizer(user_username, event_name):
    user = User.objects.get(username=user_username)
    event = Event.objects.get(name=event_name)

    # ✅ FIXED (use single organizer)
    event.organizer = user
    event.save()

    # Ensure profile updated
    user.profile.is_organizer = True
    user.profile.save()

    print(f"{user.username} assigned as organizer to {event.name}")


# ----------------------
# HELPER: Fix existing users
# ----------------------
def fix_existing_organizers():
    organizer_users = ['Hasham', 'Sir_Ubaid']

    for u_name in organizer_users:
        user = User.objects.get(username=u_name)
        user.profile.is_organizer = True
        user.profile.save()
        print(f"{user.username} is now an organizer")