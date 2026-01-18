from random import randint
from django.core.mail import send_mail
from django.contrib.auth.models import User
import uuid

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def validate_email_format(email: str) -> bool:
    """Проверяет, что email корректного формата."""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def generate_verification_code():
    return randint(100000, 999999)

def send_email_verification_code(email, code):
    send_mail(
        'Код подтверждения',
        f'Ваш код подтверждения: {code}',
        'tatarinroman234@gmail.com',
        [email], # the function expects a list of recipients
        fail_silently=False # if the email sending fails, it will raise an exception, if it is True it will not
    )

def send_email(email, subject, message):
    send_mail(
        subject,
        message,
        'tatarinroman234@gmail.com',
        [email], # the function expects a list of recipients
        fail_silently=False # if the email sending fails, it will raise an exception, if it is True it will not
    )

def send_sms_verification(phone_number, code):
    pass

def generate_unique_username():
    while True:
        username = f"user_{uuid.uuid4().hex[:10]}"
        if not User.objects.filter(username=username).exists():
            return username