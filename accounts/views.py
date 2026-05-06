from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserCreateForm, MessageForm
from .models import SystemMessage, UserProfile
from django.http import JsonResponse


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/intro/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/intro/')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('/login/')


@never_cache
@login_required
def intro_view(request):
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else 'employee'
    if request.user.is_staff: role = 'manager'
    return render(request, 'intro.html', {'user_role': role})


from .decorators import hr_required, manager_or_hr_required


@never_cache
@manager_or_hr_required
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/user_list.html', {'users': users})


@never_cache
@hr_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('/dashboard/users/')
    else:
        form = UserCreateForm()
    return render(request, 'dashboard/user_create.html', {'form': form})


@never_cache
@hr_required
def user_toggle_active(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        # Prevent HR from deactivating themselves or superusers
        if target_user == request.user or target_user.is_superuser:
            messages.error(request, "Authority check failed: Cannot deactivate yourself or a superuser.")
            return redirect('/dashboard/users/')
            
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = "activated" if target_user.is_active else "deactivated"
        messages.success(request, f"User {target_user.username} {status}.")
    return redirect('/dashboard/users/')


@never_cache
@manager_or_hr_required
def send_message(request, user_id):
    if request.method == 'POST':
        recipient = get_object_or_404(User, id=user_id)
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = recipient
            msg.save()
            messages.success(request, f"Urgent nudge sent to {recipient.username}.")
    return redirect('/dashboard/users/')


@never_cache
@login_required
def acknowledge_message(request, message_id):
    if request.method == 'POST':
        msg = get_object_or_404(SystemMessage, id=message_id, recipient=request.user)
        msg.is_read = True
        msg.save()
        return JsonResponse({'status': 'success'})
@never_cache
@login_required
@require_POST
def update_profile_flag(request):
    from .models import UserProfile
    flag = request.POST.get('flag')
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if flag == 'has_seen_onboarding':
        profile.has_seen_onboarding = True
        profile.save()
        return JsonResponse({'status': 'success'})
    elif flag == 'has_seen_tutorial':
        profile.has_seen_tutorial = True
        profile.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid flag'}, status=400)
