import math

from django import template

register = template.Library()


@register.filter(name='convert_play')
def convert_play(value):
    hours = math.floor(value / 3600)
    minutes = math.floor((value - hours * 3600) / 60)
    seconds = value - hours * 3600 - minutes * 60
    return f'{hours: 02d}:{minutes:02d}:{seconds:02d}'


# создаем фильтр, чтобы в зависимости от кол-ва товаров писалось товар / товара/ товаров
@register.filter(name='declension_of_products')
def declension_of_products(count):
    suffix = ('товар', 'товара', 'товаров')
    keys = (2, 0, 1, 1, 1, 2)
    mod = count % 100
    if 7 < mod < 20:
        suffix_key = 2
    else:
        suffix_key = keys[min(mod % 10, 5)]
    return suffix[suffix_key]