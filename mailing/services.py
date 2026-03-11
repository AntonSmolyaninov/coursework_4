from django.core.mail import send_mail
from django.utils import timezone
from .models import Mailing, MailingAttempt


def send_mailing(mailing_id):
    """Отправка рассылки по ID"""
    try:
        mailing = Mailing.objects.get(id=mailing_id)

        # Проверяем статус
        if mailing.get_status() != 'running':
            return False, "Рассылка не активна в данный момент"

        # Получаем всех получателей
        recipients = mailing.recipients.all()
        if not recipients:
            return False, "Нет получателей"

        # Отправляем каждому
        success_count = 0
        for recipient in recipients:
            try:
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=None,  # из settings.DEFAULT_FROM_EMAIL
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='success',
                    server_response='OK'
                )
                success_count += 1

            except Exception as e:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    status='failed',
                    server_response=str(e)
                )

        return True, f"Отправлено {success_count} из {len(recipients)} писем"

    except Mailing.DoesNotExist:
        return False, "Рассылка не найдена"
    except Exception as e:
        return False, str(e)
