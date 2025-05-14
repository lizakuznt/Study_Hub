from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
import os
from django.db.models import Count
from .models import (
    Users, Program, Section, Module, Assignment,
    Enrollment, AssignmentSubmission, Material, Certificate, MaterialProgress
)
from .forms import (
    RegistrationForm, LoginForm, ProfileEditForm, EnrollmentForm,
    AssignmentSubmissionForm, MaterialForm, AssignmentForm, ProgramForm,
    CertificateForm, AddFavoriteForm, SubmissionReviewForm
)
from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from transliterate import translit

def generate_certificate_pdf(username, program_name):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    # Заменим всё на латиницу
    username = translit(username, 'ru', reversed=True)
    program_name = translit(program_name, 'ru', reversed=True)

    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, height - 4 * cm, "CERTIFICATE")

    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 6 * cm, f"User: {username}")

    p.setFont("Helvetica-Oblique", 14)
    p.drawCentredString(width / 2, height - 8 * cm, f"For completed the program: {program_name}")

    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2, 3 * cm, "Congratulate!")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f'{username}_{program_name}_certificate.pdf'.replace(' ', '_')
    return ContentFile(buffer.read(), name=filename)



# 🔐 Группы
def in_group(user, name): return user.groups.filter(name=name).exists()
def is_participant(user): return in_group(user, 'Пользователь')
def is_curator(user): return in_group(user, 'Куратор')
def is_admin(user): return user.is_superuser or in_group(user, 'Администратор')
def check_program_completion(user):
    approved_programs = Program.objects.filter(
        enrollments__user=user,
        enrollments__is_approved=True
    )

    for program in approved_programs:
        section = program.section
        modules = section.modules.all()
        assignments = Assignment.objects.filter(module__in=modules)

        total = assignments.count()
        if total == 0:
            continue

        accepted_count = AssignmentSubmission.objects.filter(
            assignment__in=assignments,
            user=user,
            status='accepted'
        ).count()

        if accepted_count == total:
            Certificate.objects.get_or_create(user=user, program=program)


# 🏠 Главная
def index(request):
    query = request.GET.get('q', '')
    section_id = request.GET.get('section')

    filters = Q()
    if query:
        filters &= Q(name__icontains=query)
    if section_id:
        filters &= Q(section_id=section_id)

    programs = Program.objects.filter(filters)
    sections = Section.objects.all()

    context = {
        'programs': programs,
        'sections': sections,
        'query': query,
        'selected_section': int(section_id) if section_id else None
    }
    return render(request, 'index.html', context)



# 🔐 Авторизация
def user_login(request):
    form = LoginForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('index')
    return render(request, 'login.html', {'form': form})


# 🔐 Регистрация
def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('index')
    return render(request, 'register.html', {'form': form})


# 🚪 Выход
@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


# 👤 Профиль + Сертификаты
@login_required
def profile(request):
    user = request.user
    form = ProfileEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные обновлены')
        return redirect('profile')

    enrollments = Enrollment.objects.filter(user=user)
    certificates = Certificate.objects.filter(user=user)

    total = Assignment.objects.filter(module__section__in=[e.program.section for e in enrollments if e.is_approved]).count()
    completed = AssignmentSubmission.objects.filter(user=user, status='accepted').count()
    progress_percent = int((completed / total) * 100) if total else 0

    return render(request, 'profile.html', {
        'form': form,
        'enrollments': enrollments,
        'certificates': certificates,
        'progress_percent': progress_percent
    })


# 📥 Скачать сертификат
@login_required
def download_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    username = request.user.username
    program_name = certificate.program.name

    # 🔥 Генерируем PDF на лету
    content = generate_certificate_pdf(username, program_name)

    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{content.name}"'
    return response

# ⭐ Избранное
@login_required
def add_to_favorites(request):
    form = AddFavoriteForm(request.POST)
    if form.is_valid():
        program = get_object_or_404(Program, id=form.cleaned_data['program_id'])

        # Переключаем состояние: если уже есть — удалим, иначе добавим
        if program in request.user.favorites.all():
            request.user.favorites.remove(program)
            messages.success(request, 'Удалено из избранного')
        else:
            request.user.favorites.add(program)
            messages.success(request, 'Добавлено в избранное')

    # 🔁 Вернуться обратно на ту же страницу, откуда пришли
    return redirect(request.META.get('HTTP_REFERER', 'index'))



@login_required
def favorites(request):
    return render(request, 'favorites.html', {'favorites': request.user.favorites.all()})


# 📋 Программа
@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    enrolled = Enrollment.objects.filter(user=request.user, program=program, is_approved=True).exists()
    form = AddFavoriteForm(initial={'program_id': program.id})
    return render(request, 'program_detail.html', {
        'program': program,
        'enrolled': enrolled,
        'form': form
    })


# 📥 Подать заявку
@login_required
@user_passes_test(is_participant)
def enroll(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    Enrollment.objects.get_or_create(user=request.user, program=program)
    messages.success(request, 'Заявка подана')
    return redirect('program_detail', pk=program_id)


# 📝 Задания
@login_required
def assignments(request):
    user = request.user

    if is_curator(user):
        filters = Q()
        if module := request.GET.get('module'):
            filters &= Q(module_id=module)
        if program := request.GET.get('program'):
            filters &= Q(module__section__programs__id=program)

        assignments = Assignment.objects.filter(filters).select_related('module').distinct()

        # Куратор не проверяет submissions
        assignments_with_submissions = [(a, None) for a in assignments]

        context = {
            'assignments_with_submissions': assignments_with_submissions,
            'is_curator': True,
            'module_filter': request.GET.get('module'),
            'program_filter': request.GET.get('program'),
        }
        return render(request, 'assignments.html', context)

    # === Участник ===
    if not Enrollment.objects.filter(user=user, is_approved=True).exists():
        return render(request, 'assignments.html', {'message': 'Запишитесь на программу'})

    filters = Q()
    if status := request.GET.get('status'):
        filters &= Q(submissions__status=status)
    if module := request.GET.get('module'):
        filters &= Q(module_id=module)
    if program := request.GET.get('program'):
        filters &= Q(module__section__programs__id=program)

    assignments = Assignment.objects.filter(filters).distinct() if filters else Assignment.objects.all()

    assignments_with_submissions = []
    for assignment in assignments:
        submission = assignment.submissions.filter(user=user).first()
        assignments_with_submissions.append((assignment, submission))

    context = {
        'assignments_with_submissions': assignments_with_submissions,
        'status_filter': request.GET.get('status'),
        'module_filter': request.GET.get('module'),
        'program_filter': request.GET.get('program'),
        'is_curator': False
    }
    return render(request, 'assignments.html', context)


@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def assignment_create(request):
    form = AssignmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Задание создано')
        return redirect('assignments')
    return render(request, 'assignment_form.html', {'form': form})


@login_required
@user_passes_test(is_curator)
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    form = AssignmentForm(request.POST or None, instance=assignment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Задание обновлено')
        return redirect('assignments')
    return render(request, 'assignment_form.html', {'form': form})


@login_required
@user_passes_test(is_curator)
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment.delete()
    messages.success(request, 'Задание удалено')
    return redirect('assignments')


@login_required
@user_passes_test(is_participant)
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = AssignmentSubmission.objects.filter(user=request.user, assignment=assignment).first()

    status = submission.status if submission else None

    is_locked = status in ['submitted', 'accepted']  # Заблокировано полностью
    is_editable = status in [None, 'rejected']       # Можно редактировать

    if request.method == 'POST':
        if not is_editable:
            messages.warning(request, 'Вы не можете изменить это задание.')
            return redirect('assignment_detail', pk=pk)

        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            new_submission = form.save(commit=False)
            new_submission.user = request.user
            new_submission.assignment = assignment
            new_submission.status = 'submitted'
            new_submission.save()
            messages.success(request, 'Ответ отправлен на проверку.')
            return redirect('assignments')
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'form': form,
        'is_locked': is_locked,
        'status': status,
    })






# 📝 Отправить задание
@login_required
@user_passes_test(is_participant)
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    # Найти существующую попытку
    submission = AssignmentSubmission.objects.filter(user=request.user, assignment=assignment).first()

    # Задание уже принято — ничего редактировать нельзя
    if submission and submission.status in ['accepted', 'rejected']:
        messages.warning(request, 'Вы не можете изменить уже проверенное задание.')
        return redirect('assignment_detail', assignment_id)

    # Если есть черновик (submitted) — редактируем
    form = AssignmentSubmissionForm(request.POST or None, request.FILES or None, instance=submission)

    if request.method == 'POST' and form.is_valid():
        submission = form.save(commit=False)
        submission.user = request.user
        submission.assignment = assignment
        submission.status = 'submitted'  # сбрасываем статус
        submission.save()
        messages.success(request, 'Задание отправлено')
        return redirect('assignments')

    return render(request, 'submit_assignment.html', {
        'form': form,
        'assignment': assignment,
        'editing': bool(submission)
    })



# 📚 Материалы + фильтрация по модулю
@login_required
def materials(request):
    user = request.user
    module_id = request.GET.get('module')
    queryset = Material.objects.all()

    is_curator_flag = is_curator(user)
    is_admin_flag = is_admin(user)
    is_participant_flag = is_participant(user)

    if is_curator_flag or is_admin_flag:
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        return render(request, 'materials.html', {
            'materials': queryset,
            'viewed_ids': set(),  # Куратору/админу это не надо
            'is_curator': is_curator_flag,
            'is_admin': is_admin_flag,
            'is_participant': is_participant_flag,
        })

    # Участник
    if not Enrollment.objects.filter(user=user, is_approved=True).exists():
        return render(request, 'materials.html', {
            'message': 'Запишитесь на программу',
            'is_curator': is_curator_flag,
            'is_admin': is_admin_flag,
            'is_participant': is_participant_flag,
        })

    if module_id:
        queryset = queryset.filter(module_id=module_id)

    viewed_ids = set(MaterialProgress.objects.filter(user=user).values_list('material_id', flat=True))

    return render(request, 'materials.html', {
        'materials': queryset,
        'viewed_ids': viewed_ids,
        'is_curator': is_curator_flag,
        'is_admin': is_admin_flag,
        'is_participant': is_participant_flag,
    })


@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material, pk=pk)

    if is_participant(request.user):
        viewed, _ = MaterialProgress.objects.get_or_create(user=request.user, material=material)
    else:
        viewed = None  # неважно для куратора

    return render(request, 'material_detail.html', {
        'material': material,
        'viewed': viewed,
        'is_curator': is_curator(request.user),
    })



@login_required
@user_passes_test(is_curator)
def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    form = MaterialForm(request.POST or None, request.FILES or None, instance=material)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Материал обновлён')
        return redirect('materials')
    return render(request, 'material_form.html', {'form': form})


@login_required
@user_passes_test(is_curator)
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    material.delete()
    messages.success(request, 'Материал удалён')
    return redirect('materials')



# ✅ Пройденный материал
@login_required
def mark_material_viewed(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    MaterialProgress.objects.get_or_create(user=request.user, material=material)
    return redirect('materials')


# 🧑‍🏫 Проверка заданий (куратор)
@login_required
@user_passes_test(is_curator)
def submissions_to_check(request):
    submissions = AssignmentSubmission.objects.filter(status='submitted')
    return render(request, 'review_submissions.html', {'submissions': submissions})


@login_required
@user_passes_test(is_curator)
def review_submission(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    form = SubmissionReviewForm(request.POST or None, instance=submission)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if submission.status == 'accepted':
            check_program_completion(submission.user)
        messages.success(request, 'Статус задания обновлен')
        return redirect('submissions_to_check')

    return render(request, 'review_submission.html', {'form': form, 'submission': submission})


# 🧑‍🏫 Загрузка материалов (куратор)
@login_required
@user_passes_test(is_curator)
def upload_material(request):
    form = MaterialForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Материал загружен')
        return redirect('materials')
    return render(request, 'upload_material.html', {'form': form})


# 👩‍🏫 Кураторы
@login_required
def curators(request):
    query = request.GET.get('q', '')
    curators = Users.objects.filter(groups__name='Куратор')

    if query:
        curators = curators.filter(username__icontains=query)

    # 👇 Правильный related_name — Program.curator -> curated_programs
    curators = curators.annotate(programs_count=Count('curated_programs'))

    return render(request, 'curators.html', {'curators': curators, 'query': query})


@login_required
def sections(request):
    query = request.GET.get('q', '')
    sections = Section.objects.all()

    if query:
        sections = sections.filter(name__icontains=query)

    # 📊 Аннотация: количество программ и количество материалов через module -> materials
    sections = sections.annotate(
        programs_count=Count('programs', distinct=True),          # <- OK
        materials_count=Count('modules__materials', distinct=True)  # <- FIX: modules__materials
    )

    context = {
        'sections': sections,
        'query': query,
        'is_curator': is_curator(request.user)
    }
    return render(request, 'sections.html', context)


# ✅ Одобрение заявок (Куратор, Админ)
@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def manage_enrollments(request):
    enrollments = Enrollment.objects.all()
    return render(request, 'manage_enrollments.html', {'enrollments': enrollments})

# 📈 Статистика (только Админ)
@login_required
@user_passes_test(is_admin)
def statistics(request):
    participants_count = Users.objects.filter(groups__name='Пользователь').count()
    curators_count = Users.objects.filter(groups__name='Куратор').count()
    programs_count = Program.objects.count()

    context = {
        'participants_count': participants_count,
        'curators_count': curators_count,
        'programs_count': programs_count
    }
    return render(request, 'statistics.html', context)


# --- Программы: CRUD ---
@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def program_create(request):
    form = ProgramForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Программа добавлена')
        return redirect('my_programs')
    return render(request, 'program_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    form = ProgramForm(request.POST or None, request.FILES or None, instance=program)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Программа обновлена')
        return redirect('my_programs')
    return render(request, 'program_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    program.delete()
    messages.success(request, 'Программа удалена')
    return redirect('my_programs')


@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def enrollment_toggle_approval(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    enrollment.is_approved = not enrollment.is_approved
    enrollment.save()
    messages.success(request, f'Заявка {"одобрена" if enrollment.is_approved else "отклонена"}')
    return redirect('enrollments_manage')

# --- Разделы: CRUD ---
@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def section_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name and description:
            Section.objects.create(name=name, description=description)
            messages.success(request, 'Раздел создан')
            return redirect('sections_manage')
        messages.error(request, 'Имя и описание обязательны')
    return render(request, 'section_form.html')

@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        section.name = request.POST.get('name')
        section.description = request.POST.get('description')
        section.save()
        messages.success(request, 'Раздел обновлён')
        return redirect('sections_manage')
    return render(request, 'section_form.html', {'section': section})

@login_required
@user_passes_test(lambda u: is_curator(u) or is_admin(u))
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    section.delete()
    messages.success(request, 'Раздел удалён')
    return redirect('sections_manage')


@login_required
def my_programs(request):
    query = request.GET.get('q', '')
    section_id = request.GET.get('section')
    filters = Q()

    if is_participant(request.user):
        my_enrollments = Enrollment.objects.filter(user=request.user, is_approved=True).values_list('program_id', flat=True)
        filters &= Q(id__in=my_enrollments)

    if query:
        filters &= Q(name__icontains=query)
    if section_id:
        filters &= Q(section_id=section_id)

    programs = Program.objects.filter(filters).select_related('section')
    sections = Section.objects.all()

    context = {
        'programs': programs,
        'sections': sections,
        'query': query,
        'selected_section': int(section_id) if section_id else None,
        'is_curator': is_curator(request.user),
        'is_admin': is_admin(request.user)
    }
    return render(request, 'my_programs.html', context)
