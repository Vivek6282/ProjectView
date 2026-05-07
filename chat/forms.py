from django import forms
from django.contrib.auth.models import User
from .models import ChatRoom


class ChatRoomForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'pv-member-check'}),
        required=True,
        label='Select Members',
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'members']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control pv-input',
                'placeholder': 'e.g. Sprint Review, Design Team, Quick Question...',
            }),
        }

    def __init__(self, *args, exclude_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if exclude_user:
            self.fields['members'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id=exclude_user.id)
