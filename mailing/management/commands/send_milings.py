from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    help = 'Отправляет все активные рассылки'

    def add_arguments(self, parser):
        parser.add_argument('--mailing_id', type=int, help='ID конкретной рассылки для отправки')

    def handle(self, *args, **options):
        mailing_id = options.get('mailing_id')

        if mailing_id:
            # Отправка конкретной рассылки
            try:
                success, message = send_mailing(mailing_id)
                if success:
                    self.stdout.write(self.style.SUCCESS(message))
                else:
                    self.stdout.write(self.style.ERROR(message))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
        else:
            # Отправка всех активных рассылок
            now = timezone.now()
            mailings = Mailing.objects.filter(
                start_time__lte=now,
                end_time__gte=now,
                is_active=True
            )

            for mailing in mailings:
                self.stdout.write(f'Отправка рассылки #{mailing.id}...')
                success, message = send_mailing(mailing.id)
                if success:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {message}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ {message}'))
