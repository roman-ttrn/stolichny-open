from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend #
from django.db.models import Q #

class PhoneOrEmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        if username is None or password is None:
            return

        try:
            user = User.objects.get(Q(email_iexact=username) | Q(prodfile__phone_number=username)) #

        except User.DoesNotExist:
            return None

        if user.check_password(password): #
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None