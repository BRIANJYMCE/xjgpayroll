from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm

from django.contrib.sessions.models import Session
from django.utils import timezone
from django.templatetags.static import static


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_main_menu')
        return redirect('user_menu')

    account_deactivated = False

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Invalidate previous sessions
            user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in user_sessions:
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(user.id):
                    session.delete()

            auth_login(request, user)

            if user.is_superuser:
                return redirect('admin_main_menu')
            return redirect('user_menu')
        else:
            # Check if user exists and is inactive
            username = request.POST.get('username')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    account_deactivated = True
            except User.DoesNotExist:
                pass

            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'account_deactivated': account_deactivated
    })



def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session['account_created'] = True
            return redirect('account_created')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def account_created_view(request):
    if not request.session.pop('account_created', False):
        return redirect('login')  # or register
    return render(request, 'accounts/account_created.html')





def account_deactivated_view(request):

    return render(request, "accounts/account_deactivated.html")


def og_imae(request):
    og_image_url = request.build_absolute_uri(static('theme/og_image_xjg.jpg'))
    return render(request, "base.html", {"og_image_url": og_image_url})
