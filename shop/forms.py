from django import forms
from django.core.exceptions import ValidationError

from shop.models import Order


class SearchForm(forms.Form):
    q = forms.CharField(
        widget=forms.TextInput(
            attrs={'placeholder': 'Поиск'}
        )
    )

class OrderModelForm(forms.ModelForm):
    DELIVERY_CHOICES = (
        (0, 'Выберите пожалуйста'),
        (1, 'Доставка'),
        (2, 'Самовывоз'),
    )
    delivery = forms.TypedChoiceField(label='Доставка', choices=DELIVERY_CHOICES,coerce=int)
    class Meta:
        model = Order
        exclude = ['discount', 'status', 'need_delivery']
        labels = {'address': 'Полный адрес (Страна, город, индекс, улица, дом, квартира)'}
        widgets = {
            'address': forms.Textarea(
                attrs={'rows': 6, 'cols': 80, 'placeholder': 'При самовывозе можно оставить пустым'}
            ),
            'notice': forms.Textarea(
                attrs={'rows': 6, 'cols': 80}
            )
        }

    #проверяем заполнение столбца delivery
    def clean_delivery(self):
        data = self.cleaned_data['delivery']
        if data == 0:
            raise ValidationError('Необходимо выбрать способ доставки')
        return data

    #если поле самовывоз - то поле адрес можно оставить пустым, если указано "Доставка" - то обязательно должно быть заполнено
    def clean(self):
        delivery = self.cleaned_data['delivery']
        address = self.cleaned_data['address']
        if delivery == 1 and address == '':
            raise ValidationError('Укажите адрес доставки')
        return self.cleaned_data