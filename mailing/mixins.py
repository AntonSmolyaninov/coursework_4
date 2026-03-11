from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class OwnerRequiredMixin(UserPassesTestMixin):
    """Проверка, является ли пользователь владельцем"""

    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.owner


class ManagerRequiredMixin(UserPassesTestMixin):
    """Проверка, является ли пользователь менеджером"""

    def test_func(self):
        return self.request.user.groups.filter(name='Менеджеры').exists()

    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав доступа')
        return redirect('mailing:home')
