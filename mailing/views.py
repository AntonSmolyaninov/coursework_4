from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required

from .models import Recipient, Message, Mailing, MailingAttempt
from .forms import RecipientForm, MessageForm, MailingForm
from .mixins import OwnerRequiredMixin, ManagerRequiredMixin
from .services import send_mailing


class RecipientListView(LoginRequiredMixin, ListView):
    """Список получателей"""
    model = Recipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        # Менеджеры видят всех, обычные пользователи - только своих
        if user.groups.filter(name='Менеджеры').exists():
            return Recipient.objects.all().order_by('full_name')
        else:
            return Recipient.objects.filter(owner=user).order_by('full_name')


class RecipientDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о получателе"""
    model = Recipient
    template_name = 'mailing/recipient_detail.html'
    context_object_name = 'recipient'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return Recipient.objects.all()
        return Recipient.objects.filter(owner=user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Создание получателя"""
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Получатель успешно создан')
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """Редактирование получателя"""
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        messages.success(self.request, 'Получатель успешно обновлен')
        return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    """Удаление получателя"""
    model = Recipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Получатель успешно удален')
        return super().delete(request, *args, **kwargs)

class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений"""
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return Message.objects.all().order_by('-created_at')
        else:
            return Message.objects.filter(owner=user).order_by('-created_at')


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о сообщении"""
    model = Message
    template_name = 'mailing/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return Message.objects.all()
        return Message.objects.filter(owner=user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Сообщение успешно создано')
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """Редактирование сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение успешно обновлено')
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    """Удаление сообщения"""
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Сообщение успешно удалено')
        return super().delete(request, *args, **kwargs)


class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок"""
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return Mailing.objects.all().order_by('-created_at')
        else:
            return Mailing.objects.filter(owner=user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for mailing in context['mailings']:
            mailing.current_status = mailing.get_status()
        return context


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о рассылке"""
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.object.get_status()
        context['attempts'] = self.object.attempts.all()[:10]
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Рассылка успешно создана')
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    """Редактирование рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка успешно обновлена')
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    """Удаление рассылки"""
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка успешно удалена')
        return super().delete(request, *args, **kwargs)


@login_required
def send_mailing_view(request, pk):
    """Ручной запуск рассылки"""
    print(f"\n{'=' * 50}")
    print(f"ВЫЗВАНА send_mailing_view с pk={pk}")
    print(f"Пользователь: {request.user.email}")
    print(f"Метод запроса: {request.method}")
    print(f"{'=' * 50}\n")

    mailing = get_object_or_404(Mailing, pk=pk)
    print(f"Найдена рассылка: ID={mailing.id}")
    print(f"Владелец рассылки: {mailing.owner.email}")
    print(f"Текущий пользователь = владелец: {request.user == mailing.owner}")
    print(f"Пользователь в группе Менеджеры: {request.user.groups.filter(name='Менеджеры').exists()}")

    # Проверка прав
    if not (request.user == mailing.owner or request.user.groups.filter(name='Менеджеры').exists()):
        print("ОШИБКА ПРАВ: пользователь не имеет прав")
        messages.error(request, 'У вас нет прав для запуска этой рассылки')
        return redirect('mailing:mailing_detail', pk=pk)

    print("Права проверены, вызываем send_mailing...")

    try:
        # Передаем pk в функцию send_mailing
        print(f"Вызов send_mailing({pk})")
        success, message = send_mailing(pk)
        print(f"Результат send_mailing: success={success}, message='{message}'")

        if success:
            print("Успешно, добавляем success message")
            messages.success(request, message)
        else:
            print("Ошибка, добавляем error message")
            messages.error(request, message)

    except Exception as e:
        print(f"ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Ошибка при отправке: {e}')

    print("Редирект на страницу рассылки")
    return redirect('mailing:mailing_detail', pk=pk)


@login_required
@permission_required('mailing.disable_mailings', raise_exception=True)
def toggle_mailing(request, pk):
    """Отключение/включение рассылки (для менеджеров)"""
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.is_active = not mailing.is_active
    mailing.save()

    status = 'активирована' if mailing.is_active else 'отключена'
    messages.success(request, f'Рассылка успешно {status}')
    return redirect('mailing:mailing_detail', pk=pk)


class MailingAttemptListView(LoginRequiredMixin, ListView):
    """Список попыток рассылок"""
    model = MailingAttempt
    template_name = 'mailing/attempt_list.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Менеджеры').exists():
            return MailingAttempt.objects.all().select_related('mailing').order_by('-attempt_time')
        else:
            return MailingAttempt.objects.filter(
                mailing__owner=user
            ).select_related('mailing').order_by('-attempt_time')


class HomeView(ListView):
    """Главная страница со статистикой"""
    template_name = 'mailing/home.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.groups.filter(name='Менеджеры').exists():
                return Mailing.objects.all()[:5]
            else:
                return Mailing.objects.filter(owner=self.request.user)[:5]
        return Mailing.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общая статистика
        total_mailings = Mailing.objects.count()
        total_recipients = Recipient.objects.count()

        # Активные рассылки
        now = timezone.now()
        active_mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        ).count()

        context.update({
            'total_mailings': total_mailings,
            'active_mailings': active_mailings,
            'total_recipients': total_recipients,
            'is_authenticated': self.request.user.is_authenticated,
        })

        return context
