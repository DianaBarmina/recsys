from django import forms
from datetime import date
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm

from .models import UserStudent, UserCourse, UserPlatform, Platform


'''class SignUpForm(UserCreationForm):

    class Meta:
        model = Traveler
        fields = ('username', 'first_name', 'last_name', 'birth_date', 'passport', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
'''


class UserStudentRegistrationForm(UserCreationForm):

    class Meta:
        model = UserStudent
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserStudentRegistrationForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class UserCourseForm(forms.ModelForm):

    class Meta:
        model = UserCourse
        exclude = ['user', 'course', 'source', 'date_added', 'score']


class UsernameChangeForm(forms.ModelForm):
    class Meta:
        model = UserStudent
        fields = ['username']


class PasswordChangeCustomForm(PasswordChangeForm):
    class Meta:
        model = UserStudent


class UserPlatformForm(forms.ModelForm):
    class Meta:
        model = UserPlatform
        fields = ['user_platform_id', 'platform']  # Поля, которые пользователь будет заполнять

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Упрощаем выбор платформы, отображая только существующие платформы в базе
        self.fields['platform'].queryset = Platform.objects.all()
        self.fields['platform'].label = "Select Platform"
        self.fields['user_platform_id'].label = "User Platform ID"