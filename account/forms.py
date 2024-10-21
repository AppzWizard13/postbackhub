from django import forms
from django.contrib.auth import get_user_model
User = get_user_model() 
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'last_name', 'email','username',  'password1', 'password2' ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].help_text = None
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control m-2'

class UserLoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'exampleInputEmail1',
            'aria-describedby': 'emailHelp',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        label="Password",
        max_length=100,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'exampleInputPassword1',
            'placeholder': 'Password'
        })
    )

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-2'

    def label_from_instance(self, obj):
        return obj.username  # or any other field you want to display as label



class UserprofileUpdate(forms.ModelForm):
    # specify the name of model to use
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username" ,  "email", "dhan_client_id", "dhan_access_token" ]

    def __init__(self, *args, **kwargs):
        super(UserprofileUpdate, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-1'

from django import forms
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import User  # Assuming User is your custom user model

# Custom form for User with specified fields
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'phone_number', 
            'email',
            'country', 
            'dhan_client_id', 
            'status', 
            'dhan_access_token', 
            # 'profile_image',  # Optional field
        ]
        widgets = {
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control m-1'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-1'

from django import forms
from .models import Control
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomControlCreationForm(forms.ModelForm):
    # You can add any specific fields you want for customization here
    class Meta:
        model = Control
        fields = ['max_order_limit', 'max_loss_limit', 'max_profit_limit', 
                  'max_profit_mode', 'max_order_count_mode', 'is_killed_once', 'user']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove default help texts and add Bootstrap form-control class
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control m-2'
            field.help_text = None  # Remove help texts if needed


from django import forms
from .models import Control

class ControlForm(forms.ModelForm):
    class Meta:
        model = Control
        fields = ['max_order_limit', 'max_loss_limit', 'max_profit_limit','max_loss_mode',
                  'max_profit_mode', 'max_order_count_mode', 'is_killed_once', 'user']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove default help texts and add Bootstrap form-control class
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control m-2'
            field.help_text = None  # Remove help texts if needed