from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """First step: Basic user account creation."""
    email = forms.EmailField(
        required=True,
        help_text='Required. Enter a valid email address.'
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text='Optional.'
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text='Optional.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_username(self):
        """Check if username is already taken (case-insensitive)."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        """Check if email is already taken."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('This email address is already registered.')
        return email


class UserProfileRegistrationForm(forms.ModelForm):
    """Second step: User profile details."""
    
    class Meta:
        model = UserProfile
        fields = ('bio', 'location', 'website', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us a bit about yourself...'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g., New York, USA'
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://example.com'
            }),
            'avatar': forms.TextInput(attrs={
                'placeholder': 'Avatar image URL (optional)'
            }),
        }
