from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy

from .models import Recipient, Message, Mailing


class StyleFormMixin:
    """Миксин для стилизации полей формы"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control-file'
            else:
                field.widget.attrs['class'] = 'form-control'


class RecipientForm(StyleFormMixin, forms.ModelForm):
    """Форма для получателей рассылки"""

    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class MessageForm(StyleFormMixin, forms.ModelForm):
    """Форма для сообщений"""

    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class MailingForm(StyleFormMixin, forms.ModelForm):
    """Форма для рассылок"""

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recipients': forms.SelectMultiple(attrs={'size': 10, 'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Если пользователь авторизован
        if self.user:
            # Показываем только сообщения и получателей этого пользователя
            self.fields['message'].queryset = Message.objects.filter(owner=self.user)
            self.fields['recipients'].queryset = Recipient.objects.filter(owner=self.user)

            # Добавляем подсказки, если списки пусты
            if not self.fields['message'].queryset.exists():
                self.fields['message'].empty_label = "Сначала создайте сообщение"
                self.fields[
                    'message'].help_text = 'У вас пока нет сообщений. <a href="{}">Создать сообщение</a>'.format(
                    reverse_lazy('mailing:message_create')
                )

            if not self.fields['recipients'].queryset.exists():
                self.fields[
                    'recipients'].help_text = 'У вас пока нет получателей. <a href="{}">Добавить получателя</a>'.format(
                    reverse_lazy('mailing:recipient_create')
                )

    def clean(self):
        """Валидация дат"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Дата начала должна быть раньше даты окончания')

        # Проверяем, есть ли сообщения и получатели
        if self.user:
            if not Message.objects.filter(owner=self.user).exists():
                raise ValidationError('Сначала нужно создать хотя бы одно сообщение')

            if not Recipient.objects.filter(owner=self.user).exists():
                raise ValidationError('Сначала нужно добавить хотя бы одного получателя')

        return cleaned_data
