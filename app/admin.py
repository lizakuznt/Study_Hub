from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import (
    Users, Program, Section, Module, ProgramModule,
    Enrollment, Assignment, AssignmentSubmission,
    Material, Certificate, MaterialProgress
)

# ——— INLINES ——— #

class CuratorInline(admin.TabularInline):
    model = Program.curators.through
    extra = 1
    verbose_name = "Куратор"
    verbose_name_plural = "Кураторы"

class FavoritesInline(admin.TabularInline):
    model = Users.favorites.through
    extra = 1
    verbose_name = "Избранное"
    verbose_name_plural = "Избранные программы"

class ProgramModuleInline(admin.TabularInline):
    model = ProgramModule
    extra = 1

class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 1

class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1

# ——— USERS ADMIN ——— #

@admin.register(Users)
class UsersAdmin(BaseUserAdmin):
    list_display = ('username', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username',)
    ordering = ('username',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')

    fieldsets = (
        ('Основное', {'fields': ('username', 'password')}),
        ('Доступ', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {'fields': ('last_login',)}),
    )

    readonly_fields = ('last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    inlines = [FavoritesInline]


# ——— PROGRAM ADMIN ——— #

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    search_fields = ('name',)
    list_filter = ('section',)
    inlines = [CuratorInline, ProgramModuleInline]

# ——— SECTION ADMIN ——— #

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# ——— MODULE ADMIN ——— #

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    search_fields = ('name',)
    list_filter = ('section',)
    inlines = [AssignmentInline, MaterialInline]

# ——— ASSIGNMENT ADMIN ——— #

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module')
    search_fields = ('title',)
    list_filter = ('module__section',)

# ——— MATERIAL ADMIN ——— #

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'module')
    search_fields = ('title',)
    list_filter = ('module__section',)

# ——— ENROLLMENT ADMIN ——— #

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'is_approved')
    list_filter = ('is_approved', 'program__section')
    search_fields = ('user__username', 'program__name')
    autocomplete_fields = ('user', 'program')

# ——— ASSIGNMENT SUBMISSION ADMIN ——— #

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'assignment', 'status', 'submitted_at')
    list_filter = ('status', 'assignment__module__section')
    search_fields = ('user__username', 'assignment__title')
    readonly_fields = ('submitted_at',)

# ——— CERTIFICATE ADMIN ——— #

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'issued_at')
    readonly_fields = ('issued_at',)
    search_fields = ('user__username', 'program__name')

# ——— MATERIAL PROGRESS ADMIN ——— #

@admin.register(MaterialProgress)
class MaterialProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'material')
    search_fields = ('user__username', 'material__title')
    list_filter = ('material__module__section',)
    autocomplete_fields = ('user', 'material')
