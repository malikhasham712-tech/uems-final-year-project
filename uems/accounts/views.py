import profile
from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.auth.models import User

from .forms import RegisterForm
from .models import Profile
from events.models import Event, EventRegistration

from django.core.mail import send_mail
from django.conf import settings
import uuid


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
# LOGIN (FIXED)
# ----------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        login_errors = {}

        if not username:
            login_errors['username'] = 'This field is required.'

        if not password:
            login_errors['password'] = 'This field is required.'

        if login_errors:
            return render(request, 'accounts/login.html', {
                'login_errors': login_errors,
                'username_value': username,
            })

        user = authenticate(request, username=username, password=password)

        if user is not None:

            try:
                profile = user.profile
            except:
                messages.error(request, 'Profile missing. Contact admin.')
                return redirect('login')

            if not profile.email_verified:
                messages.error(request, 'Please verify your email.')
                return redirect('login')

            login(request, user)

            # CHECK FOR ?next= PARAMETER (QR ATTENDANCE FLOW)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            # DEFAULT REDIRECT
            if profile.role == 'organizer':
                return redirect('events:dashboard')
            else:
                return redirect('events:dashboard')

        # 🔥 IMPORTANT: RETURN HERE WAS MISSING
        messages.error(request, 'Invalid username or password.')
        return render(request, 'accounts/login.html', {
            'username_value': username,
        })

    # GET request always returns page
    return render(request, 'accounts/login.html')
# ----------------------
# LOGOUT
# ----------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# ----------------------
# DASHBOARD
# ----------------------
@login_required
def dashboard(request):
    user = request.user

    if hasattr(user, 'profile') and user.profile.role == 'organizer':
        user_events = Event.objects.filter(organizer=user).annotate(
            total_registrations=Count('registrations')
        )

        total_events = user_events.count()
        total_registrations = sum(e.total_registrations for e in user_events)

        context = {
            'role': 'organizer',
            'user_events': user_events,
            'total_events': total_events,
            'total_registrations': total_registrations,
        }

    else:
        registered_events = EventRegistration.objects.filter(
            student=user
        ).select_related('event')

        available_events = Event.objects.filter(status='announced')

        context = {
            'role': 'student',
            'registered_events': [r.event for r in registered_events],
            'available_events': available_events,
        }

    return render(request, 'accounts/dashboard.html', context)


# ----------------------
# VIEW EVENT (FIXED)
# ----------------------
@login_required
def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if hasattr(request.user, 'profile') and request.user.profile.role != 'organizer':
        if not EventRegistration.objects.filter(student=request.user, event=event).exists():
            messages.error(request, 'You are not registered for this event.')
            return redirect('events:my_events')   # ✅ FIXED RETURN

    return render(request, 'accounts/view_event.html', {
        'event': event,
        'organizer': event.organizer,
    })


# ----------------------
# HELPERS
# ----------------------
def assign_organizer(user_username, event_name):
    user = User.objects.get(username=user_username)
    event = Event.objects.get(name=event_name)

    event.organizer = user
    event.save()

    user.profile.is_organizer = True
    user.profile.role = 'organizer'
    user.profile.save()


def fix_existing_organizers():
    organizer_users = ['Sir_Ubaid']

    for username in organizer_users:
        user = User.objects.get(username=username)
        user.profile.is_organizer = True
        user.profile.role = 'organizer'
        user.profile.save()
