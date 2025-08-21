from time import *
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages

from .models import *
from .forms import RegistrationForm
from .utils.utils import *
from .forms import *


def profile(request):
    return render(request, 'userapp/profile.html')

@ratelimit(key='ip', rate='20/h', method='POST', block=True)
@login_required
def profile_edit(request):
    user = request.user
    current_data = {
                'first_name': user.first_name,
                'email': user.email,
            }

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, instance=user)

        if profile_form.is_valid():
            
            # Получаем новые данные из формы
            new_data = {
                'first_name': profile_form.cleaned_data['first_name'],
                'email': profile_form.cleaned_data['email'],
            }
            
            # Проверяем, есть ли изменения
            if current_data == new_data:
                messages.info(request, 'Данные не были изменены.')
                return redirect('profile')
            else:
                messages.success(request, 'Данные успешно обновлены.')
                profile_form.save()
                return redirect('profile')
        
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в введенных данных.')
            return redirect('profile_edit')

    else:
        profile_form = ProfileUpdateForm(instance=user)

    return render(request, 'userapp/profile_edit.html', {'form': profile_form})


@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def login_email(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        print(email)

        try:
            user_exists = User.objects.filter(email=email).exists()
            if not user_exists:
                messages.error(request, 'Пользователь с таким email не найден.')
                return render(request, 'userapp/login_email.html')
            
            code_entry, created = EmailVerificationCode.objects.get_or_create(email=email, verified=False)

            if code_entry.is_blocked():
                messages.error(request, 'Слишком много попыток. Повторите позже.')
                return render(request, 'userapp/login_email.html')

            code = generate_verification_code()
            code_entry.code = code
            code_entry.created_at = timezone.now()
            code_entry.attempts = 0
            code_entry.resend_attempts += 1

            if code_entry.resend_attempts > 5:
                code_entry.block()
                messages.error(request, 'Превышен лимит отправок. Повторите через час.')
                return render(request, 'userapp/login_email.html')

            code_entry.save()
            print('код')
            send_email_verification_code(email, code)
            print('отправлен')
            request.session['reg_data'] = {'email': email}
            request.session['email'] = email
            print('redirect')
            return redirect('login_email_verify', email=email)

        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден.')
            return render(request, 'userapp/login_email.html')

    return render(request, 'userapp/login_email.html')


@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def login_email_verify(request, email):
    if request.user.is_authenticated:
        return redirect('/')

    try:
        code_entry = EmailVerificationCode.objects.get(email=email, verified=False)
    except EmailVerificationCode.DoesNotExist:
        messages.error(request, 'Вы не запрашивали код для входа.')
        return redirect('login_email')

    if code_entry.is_blocked():
        messages.error(request, 'Слишком много неверных попыток. Повторите позже.')
        return redirect('login_email')

    if request.method == 'POST':
        input_code = request.POST.get('code')

        if code_entry.is_expired():
            messages.error(request, 'Код истёк. Запросите новый.')
            return redirect('login_email')

        if input_code != code_entry.code:
            code_entry.attempts += 1
            code_entry.save()

            if code_entry.attempts > 5:
                code_entry.block()
                messages.error(request, 'Слишком много попыток. Повторите позже.')
                return redirect('login_email')

            messages.error(request, 'Неверный код подтверждения.')
            return redirect('login_email_verify', email=email)

        # Код верен
        code_entry.verified = True
        code_entry.save()

        user = User.objects.get(email=email)
        login(request, user)

        # очищаем старые коды (по желанию — можно удалять вручную)
        EmailVerificationCode.objects.filter(email=email).delete()

        messages.success(request, 'Вы успешно вошли в аккаунт.')
        return redirect('catalog')

    return render(request, 'userapp/email_verify.html', {'user_email': email})


def signup_email(request):
    if request.user.is_authenticated:
        return redirect('/')

    form = RegistrationForm()

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            print(email)
            phone = form.cleaned_data['phone']

            if User.objects.filter(email=email).exists() or Profile.objects.filter(phone_number=phone).exists():
                messages.error(request, 'Пользователь с такой почтой или номером телефона уже существует.')
                return render(request, 'userapp/signup_email.html', {'form': form})

            # Проверка на блокировку
            code_entry, created = EmailVerificationCode.objects.get_or_create(email=email, verified=False)
            if code_entry.is_blocked():
                messages.error(request, 'Слишком много попыток. Повторите через час.')
                return render(request, 'userapp/signup_email.html', {'form': form})

            # Генерация кода
            code = generate_verification_code()
            code_entry.code = code
            code_entry.created_at = timezone.now()
            code_entry.attempts = 0
            code_entry.resend_attempts += 1

            if code_entry.resend_attempts > 5:
                code_entry.block()
                messages.error(request, 'Превышен лимит отправок. Повторите через час.')
                return render(request, 'userapp/signup_email.html', {'form': form})

            code_entry.save()
            send_email_verification_code(email, code)

            request.session['reg_data'] = {'email': email, 'phone': phone, 'first_name': form.cleaned_data['first_name']}
            print(email)
            return redirect('signup_email_verification')

        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

    return render(request, 'userapp/signup_email.html', {'form': form})



@ratelimit(key='ip', rate='20/h', method='POST', block=True)
def signup_email_verification(request):
    email = request.session.get('reg_data')['email']
    try:
        code_entry = EmailVerificationCode.objects.get(email=email, verified=False)
    except EmailVerificationCode.DoesNotExist:
        messages.error(request, 'Код не запрашивался или уже использован.')
        return redirect('signup_email')

    if code_entry.is_blocked():
        messages.error(request, 'Слишком много попыток. Повторите позже.')
        return redirect('signup_email')

    if request.method == 'POST':
        input_code = request.POST.get('code')

        if code_entry.is_expired():
            messages.error(request, 'Код истек. Запросите новый.')
            return redirect('signup_email')

        if code_entry.code != input_code:
            code_entry.attempts += 1
            code_entry.save()

            if code_entry.attempts > 5:
                code_entry.block()
                messages.error(request, 'Слишком много неверных попыток. Повторите через час.')
                return redirect('signup_email')

            messages.error(request, 'Неверный код подтверждения.')
            return redirect('signup_email_verification')

        # Код верен
        code_entry.verified = True
        code_entry.save()

        # Получаем user данные через форму (в реальном проде лучше использовать промежуточную модель)
        form = RegistrationForm(request.session.get('reg_data') or {})  # если ты решишь сохранять reg_data как словарь в сессии

        if not form.is_valid():
            messages.error(request, 'Ошибка данных регистрации. Повторите.')
            return redirect('signup_email')

        user = User.objects.create_user(
            username=form.cleaned_data['email'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
        )
        if user.profile:
            user.profile.phone_number=form.cleaned_data['phone']
        else:
            sleep(2)
            user.profile.phone_number=form.cleaned_data['phone']

        login(request, user)

        if 'reg_data' in request.session:
            del request.session['reg_data']
        if 'email' in request.session:
            del request.session['email']

        messages.success(request, 'Аккаунт успешно создан.')
        return redirect('catalog')

    return render(request, 'userapp/email_verify.html', {'user_email': email})


def logout_user(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('/')

@csrf_protect
@require_POST
@ratelimit(key='ip', rate='20/h', block=True)
def resend_code(request):
    email = request.session.get('reg_data')['email']

    code_obj, created = EmailVerificationCode.objects.get_or_create(email=email, verified=False)

    if code_obj.is_blocked():
        print('Слишком много попыток. Повторите позже.')
        return JsonResponse({'error': 'Слишком много попыток. Повторите позже.'}, status=429)

    code_obj.resend_attempts += 1
    if code_obj.resend_attempts > 5:
        code_obj.block()
        print('Превышено число попыток. Повторите через 10 минут.')
        return JsonResponse({'error': 'Превышено число попыток. Повторите через 10 минут.'}, status=429)

    code_obj.code = generate_verification_code()
    code_obj.created_at = timezone.now()
    code_obj.save()

    try:
        send_email_verification_code(email, code_obj.code)
    except Exception:
        print('Ошибка отправки письма. Повторите позже.')
        return JsonResponse({'error': 'Ошибка отправки письма. Повторите позже.'}, status=500)
    print('success')
    return JsonResponse({'success': True})


#verify_user_id in sign up and Profile editing address problem!