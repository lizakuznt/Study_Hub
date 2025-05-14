from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Имя пользователя обязательно")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        group, _ = Group.objects.get_or_create(name="Пользователь")
        user.groups.add(group)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class Users(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100, verbose_name="Имя", blank=True)
    last_name = models.CharField(max_length=100, verbose_name="Фамилия", blank=True)
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    createdat = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(Group, related_name='customuser_set', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='customuser_permissions', blank=True)
    favorites = models.ManyToManyField('Program', related_name='favorited_by', blank=True)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username

class Section(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Module(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='modules')

    def __str__(self):
        return self.name

class Program(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='programs')
    goal = models.TextField()
    skills = models.TextField()
    certificate_image = models.ImageField(upload_to='certificates/', null=True, blank=True)
    curators = models.ManyToManyField(Users, related_name='curated_programs', blank=True)

    def __str__(self):
        return self.name

class ProgramModule(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

class Assignment(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class Material(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='materials/')
    description = models.TextField()
    file_type = models.CharField(
        max_length=20,
        choices=[('pdf', 'PDF'), ('video', 'Видео'), ('doc', 'Документ'), ('other', 'Другое')],
        default='pdf'
    )

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='enrollments')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrollments')
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'program')

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    answer_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('submitted', 'Отправлено'),
        ('accepted', 'Принято'),
        ('rejected', 'Требует доработки')
    ], default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.assignment.title}"

class Certificate(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    file = models.FileField(upload_to='certificates/')
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'program')

class MaterialProgress(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'material')
