from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.models import Program, Assignment, Material, Users

class Command(BaseCommand):
    help = "Создаёт роли (группы) и назначает соответствующие права"

    def handle(self, *args, **options):
        roles = {
            "Пользователь": [],
            "Куратор": [
                "add_program", "change_program",
                "add_assignment", "change_assignment",
                "add_material", "change_material",
                "view_enrollment", "change_enrollment",
                "view_assignmentsubmission", "change_assignmentsubmission",
                "add_certificate", "change_certificate"
            ],
            "Администратор": [
                "add_program", "change_program", "delete_program",
                "add_users", "change_users", "delete_users",
                "add_enrollment", "change_enrollment", "delete_enrollment",
                "add_certificate", "change_certificate", "delete_certificate"
            ]
        }

        for role_name, perms in roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Создана группа: {role_name}"))
            else:
                self.stdout.write(f"Группа уже существует: {role_name}")

            for codename in perms:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                    self.stdout.write(f" → Права добавлены: {codename}")
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f" × Не найдено: {codename}"))

        self.stdout.write(self.style.SUCCESS("Группы и права успешно обновлены."))
