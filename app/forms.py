from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from .models import (
    Users, Program, Enrollment, AssignmentSubmission,
    Material, Assignment, Certificate
)

class BaseBootstrapForm(forms.ModelForm):
    def apply_bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.FileInput):
                widget.attrs.update({'class': 'form-control'})
            elif isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-select'})
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({'class': 'form-control', 'rows': 4})
            else:
                widget.attrs.update({'class': 'form-control'})

            # Красивые лейблы, если нет своих
            if not field.label:
                field.label = name.replace('_', ' ').capitalize()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


# 🔐 Регистрация
class RegistrationForm(BaseBootstrapForm):
    first_name = forms.CharField(label='Имя', required=False)
    last_name = forms.CharField(label='Фамилия', required=False)
    middle_name = forms.CharField(label='Отчество', required=False)
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}))
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}))

    class Meta:
        model = Users
        fields = ['username', 'first_name', 'last_name', 'middle_name']
        labels = {
            'username': 'Имя пользователя',
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name="Пользователь")
            user.groups.add(group)
        return user



# 🔐 Авторизация
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя", widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите имя пользователя',
        'autofocus': True
    }))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Введите пароль'
    }))


# 👤 Профиль
class ProfileEditForm(BaseBootstrapForm):
    class Meta:
        model = Users
        fields = ['username', 'first_name', 'last_name', 'middle_name']


# 🧾 Запись на программу
class EnrollmentForm(BaseBootstrapForm):
    class Meta:
        model = Enrollment
        fields = []


# 📝 Отправка задания
class AssignmentSubmissionForm(BaseBootstrapForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['answer_text', 'answer_file']
        labels = {
            'answer_text': 'Ответ текстом',
            'answer_file': 'Файл с решением',
        }
        widgets = {
            'answer_text': forms.Textarea(attrs={'placeholder': 'Введите ваш ответ…'}),
        }


# 🧑‍🏫 Проверка задания
class SubmissionReviewForm(BaseBootstrapForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['status']
        labels = {'status': 'Статус проверки'}
        widgets = {
            'status': forms.Select(choices=[
                ('accepted', 'Принято'),
                ('rejected', 'Требует доработки')
            ])
        }


# 📁 Материал
class MaterialForm(BaseBootstrapForm):
    class Meta:
        model = Material
        fields = ['module', 'title', 'file', 'file_type', 'description']
        labels = {
            'module': 'Модуль',
            'title': 'Название материала',
            'file': 'Файл',
            'file_type': 'Тип файла',
            'description': 'Описание',
        }
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Краткое описание материала'}),
        }


# 🗒️ Задание
class AssignmentForm(BaseBootstrapForm):
    class Meta:
        model = Assignment
        fields = ['module', 'title', 'description']
        labels = {
            'module': 'Модуль',
            'title': 'Название задания',
            'description': 'Описание задания',
        }
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Введите описание задания'}),
        }


# 🎓 Программа
class ProgramForm(BaseBootstrapForm):
    class Meta:
        model = Program
        fields = ['name', 'description', 'section', 'goal', 'skills', 'certificate_image', 'curators']
        labels = {
            'name': 'Название программы',
            'description': 'Описание программы',
            'section': 'Раздел',
            'goal': 'Цель обучения',
            'skills': 'Навыки после завершения',
            'certificate_image': 'Изображение сертификата',
            'curators': 'Кураторы',
        }
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Общее описание программы'}),
            'goal': forms.Textarea(attrs={'placeholder': 'Что изучат участники'}),
            'skills': forms.Textarea(attrs={'placeholder': 'Какие навыки получат'}),
            'certificate_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


# 🏅 Сертификат
class CertificateForm(BaseBootstrapForm):
    class Meta:
        model = Certificate
        fields = ['user', 'program', 'file']
        labels = {
            'user': 'Пользователь',
            'program': 'Программа',
            'file': 'Файл сертификата',
        }


# ⭐ Избранное
class AddFavoriteForm(forms.Form):
    program_id = forms.IntegerField(widget=forms.HiddenInput())
