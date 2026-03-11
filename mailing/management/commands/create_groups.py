from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from mailing.models import Mailing, Message, Recipient


class Command(BaseCommand):
    help = 'Создает группы и назначает разрешения'

    def handle(self, *args, **options):
        # Создаем группу менеджеров
        managers_group, created = Group.objects.get_or_create(name='Менеджеры')

        # Получаем все кастомные разрешения
        content_types = {
            'recipient': ContentType.objects.get_for_model(Recipient),
            'message': ContentType.objects.get_for_model(Message),
            'mailing': ContentType.objects.get_for_model(Mailing),
        }

        permissions = Permission.objects.filter(
            content_type__in=content_types.values(),
            codename__in=[
                'view_all_recipients',
                'view_all_messages',
                'view_all_mailings',
                'disable_mailings',
            ]
        )

        managers_group.permissions.set(permissions)

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" создана'))
        else:
            self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" обновлена'))
