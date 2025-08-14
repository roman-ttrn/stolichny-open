from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from .models import Profile

class RegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=20,
        min_length=2,
        label="Имя",
        widget=forms.TextInput(attrs={'placeholder': 'Имя'}),
    )
    email = forms.EmailField(
        max_length=50,
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'stolichny_user228@gmail.com'}),
    )
    phone = forms.CharField(
        label="Номер телефона",
        validators=[
            RegexValidator(r'^9\d{9}$',  message="Введите корректный номер телефона, начинающийся с 9")
        ],
        widget=forms.TextInput(attrs={'placeholder': '9*********'}),
        max_length=10
    )

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=20,
        label='Имя',
        widget=forms.TextInput(attrs={'placeholder': 'Ваше имя'})
    )

    email = forms.EmailField(
        required=False,
        max_length=50,
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'stolichny_user228@gmail.com '})
    )

    class Meta:
        model = User
        fields = ['first_name', 'email']

class AddressUpdateForm(forms.ModelForm):
    address = forms.CharField(
        max_length=100,
        label='Адрес',
        widget=forms.TextInput(attrs={'placeholder': 'Ваш адрес'})
    )

    class Meta:
        model = Profile
        fields = ['address']