from django.urls import path
from . import views

urlpatterns = [
    # --- Аутентификация ---
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),

    # --- Главная и профиль ---
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),

    # --- Сертификаты ---
    path('certificate/<int:certificate_id>/download/', views.download_certificate, name='download_certificate'),

    # --- Программы и избранное ---
    path('program/<int:pk>/', views.program_detail, name='program_detail'),
    path('program/<int:program_id>/enroll/', views.enroll, name='enroll'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/add/', views.add_to_favorites, name='add_to_favorites'),
    path('programs/my/', views.my_programs, name='my_programs'),

    # --- CRUD программ (куратор/админ) ---
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),

    # --- Задания ---
    path('assignments/', views.assignments, name='assignments'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),

    # --- Проверка заданий (куратор) ---
    path('submissions/', views.submissions_to_check, name='submissions_to_check'),
    path('submissions/<int:submission_id>/review/', views.review_submission, name='review_submission'),

    # --- Материалы ---
    path('materials/', views.materials, name='materials'),
    path('materials/<int:pk>/', views.material_detail, name='material_detail'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('materials/upload/', views.upload_material, name='upload_material'),
    path('materials/<int:material_id>/viewed/', views.mark_material_viewed, name='mark_material_viewed'),

    # --- Разделы (секции) ---
    path('sections/', views.sections, name='sections'),
    path('sections/create/', views.section_create, name='section_create'),
    path('sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),

    # --- Кураторы ---
    path('curators/', views.curators, name='curators'),

    # --- Управление заявками ---
    path('enrollments/manage/', views.manage_enrollments, name='enrollments_manage'),
    path('enrollments/<int:pk>/toggle/', views.enrollment_toggle_approval, name='enrollment_toggle_approval'),

    # --- Статистика (только админ) ---
    path('stats/', views.statistics, name='stats'),
]
