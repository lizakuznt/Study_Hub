# app/context_processors.py

def user_roles(request):
    if not request.user.is_authenticated:
        return {
            'is_admin': False,
            'is_curator': False,
            'is_user': False,
        }

    is_admin_user = request.user.is_superuser or request.user.groups.filter(name='Администратор').exists()
    is_curator_user = False
    is_participant_user = False

    if not is_admin_user:
        is_curator_user = request.user.groups.filter(name='Куратор').exists()

        if not is_curator_user:
            is_participant_user = request.user.groups.filter(name='Пользователь').exists()

    return {
        'is_admin': is_admin_user,
        'is_curator': is_curator_user,
        'is_user': is_participant_user,
    }
