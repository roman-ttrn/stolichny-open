from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    address = models.CharField(max_length=100, null=False, blank=True)
    active_deliveries = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    attempts = models.IntegerField(default=0) 
    resend_attempts = models.IntegerField(default=0) 

    is_blocked_until = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def is_blocked(self): #!!!!!
        return self.is_blocked_until and self.is_blocked_until > timezone.now()

    def block(self, duration=timedelta(minutes=5)):
        self.is_blocked_until = timezone.now() + duration
        self.save()#!!!!


