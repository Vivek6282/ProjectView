from django import forms
from django.contrib.auth.models import User
from .models import SystemMessage


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control pv-input','placeholder': 'Create password'}))
    password_confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control pv-input','placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control pv-input', 'placeholder': 'Enter unique username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control pv-input', 'placeholder': 'Optional email address'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input ms-0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input ms-0'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class MessageForm(forms.ModelForm):
    class Meta:
        model = SystemMessage
        fields = ['content', 'is_urgent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control pv-input',
                'placeholder': 'Type your message to the employee...',
                'rows': 4
            }),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
