from django.db import models

class LoginAttempt(models.Model):
    ip = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip} — {self.timestamp}"