from urllib import request

from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views import generic

from shop.forms import SearchForm, OrderModelForm
from shop.models import Section, Product, Discount, Order, OrderLine


# функция котороая выводит на хомашнюю страницу в div с id=right 8 продуктов:
def index(request):
    result = prerender(request)
    if result:
        return result
    products = Product.objects.all().order_by(get_order_by_products(request))[:8]
    context = {'products': products}
    return render(
        request,
        'index.html',
        context=context
    )


# функция добавления товара в корзину
def prerender(request):
    if request.GET.get('add_cart'):
        product_id = request.GET.get('add_cart')
        get_object_or_404(Product, pk=product_id)
        cart_info = request.session.get('cart_info', {})
        count = cart_info.get(product_id, 0)
        count += 1
        cart_info.update({product_id: count})
        request.session['cart_info'] = cart_info
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# функция, которая сортирует продукты по запросу
def get_order_by_products(request):
    order_by = ''
    if request.GET.__contains__('sort') and request.GET.__contains__('up'):
        sort = request.GET['sort']
        up = request.GET['up']
        if sort == 'price' or sort == 'title':
            if up == 0:
                order_by = '-'
            order_by += sort
    if not order_by:
        order_by = '-date'
    return order_by


# функция которая выводит страницу "Оплата и доставка"
def delivery(request):
    return render(
        request,
        'delivery.html'
    )


# функция которая выводит страницу "Контакты"
def contacts(request):
    return render(
        request,
        'contacts.html'
    )


# функция которая выводит продукты по разделам
def section(request, id):
    result = prerender(request)
    if result:
        return result
    obj = get_object_or_404(Section, pk=id)
    products = Product.objects.filter(section__exact=obj).order_by(get_order_by_products(request))
    context = {'context': obj, 'products': products}
    return render(
        request,
        'section.html',
        context=context
    )


# функция которая выводит детали продукта
class ProductDetailView(generic.DetailView):
    model = Product

    # переопределим фунцию гет, чтобы при нажатии на корзину на этой страницу был редирект на главную
    def get(self, request, *args, **kwargs):
        result = prerender(request)
        if result:
            return result
        return super(ProductDetailView, self).get(request, *args, **kwargs)

    # функция, которая выводит 4 случайных продукта этой же категории
    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['products'] = Product.objects.filter(section__exact=self.get_object().section).exclude(
            id=self.get_object().id).order_by('?')[:4]
        return context


# функция которая выводит страницу 404 с оформлением в стиле сайта
def handler404(request, exception):
    return render(request, '404.html', status=404)


# функция которая выводит страницу при обработки формы поиска
def search(request):
    result = prerender(request)
    if result:
        return result
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        q = search_form.cleaned_data['q']
        products = Product.objects.filter(
            Q(title__icontains=q) | Q(country__icontains=q) | Q(director__icontains=q) |
            Q(cast__icontains=q) | Q(description__icontains=q)
        )
        # создаем пагинатор - чтобы результаты посика выводились по страницам
        page = request.GET.get('page', 1)
        paginator = Paginator(products, 4)
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        context = {'products': products, 'q': q}
        return render(
            request,
            'search.html',
            context=context
        )


# функция вывода страницы корзина
def cart(request):
    update_cart_info(request)
    cart_info = request.session.get('cart_info')
    products = []
    if cart_info:
        for product_id in cart_info:
            product = get_object_or_404(Product, pk=product_id)
            products.append(product)
            product.count = cart_info[product_id]
    context = {'products': products, 'discount': request.session.get('discount', '')}
    return render(
        request,
        'cart.html',
        context=context
    )


# фукция которая пересчитывает на странице корзина
def update_cart_info(request):
    if request.POST:
        cart_info = {}
        for param in request.POST:
            value = request.POST.get(param)
            if param.startswith('count_') and value.isnumeric():
                product_id = param.replace('count_', '')
                get_object_or_404(Product, pk=product_id)
                cart_info[product_id] = int(value)
            elif param == 'discount' and value:
                try:
                    discount = Discount.objects.get(code__exact=value)
                    request.session['discount'] = value
                except Discount.DoesNotExist:
                    pass

        request.session['cart_info'] = cart_info

    if request.GET.get('delete_cart'):
        cart_info = request.session.get('cart_info')
        product_id = request.GET.get('delete_cart')
        get_object_or_404(Product, pk=product_id)
        cart_info.pop(product_id)
        request.session['cart_info'] = cart_info
        return HttpResponseRedirect(reverse('cart'))


# выводит страницу order с формой заказа
def order(request):
    cart_info = request.session.get('cart_info')
    if not cart_info:
        raise Http404()
    if request.method == 'POST':
        form = OrderModelForm(request.POST)
        if form.is_valid():
            order_obj = Order()
            print('order_obj=', order_obj)
            order_obj.need_delivery = True if form.cleaned_data['delivery'] == 1 else False
            discount_code = request.session.get('discount', '')
            if discount_code:
                try:
                    discount = Discount.objects.get(code__exact=discount_code)
                    order_obj.discount = discount
                except Discount.DoesNotExist:
                    pass
            order_obj.name = form.cleaned_data['name']
            order_obj.phone = form.cleaned_data['phone']
            order_obj.email = form.cleaned_data['email']
            order_obj.address = form.cleaned_data['address']
            order_obj.notice = form.cleaned_data['notice']
            order_obj.save()
            add_order_lines(request, order_obj)
            add_user(form.cleaned_data['name'], form.cleaned_data['email'])
            return HttpResponseRedirect(reverse('addorder'))

    else:
        form = OrderModelForm()

    context = {'form': form}
    return render(
        request,
        'order.html',
        context=context
    )


# функция которая формирует строку в таблице OrderLine
def add_order_lines(request, order_obj):
    cart_info = request.session.get('cart_info', {})
    print('cart_info = ', cart_info)
    for key in cart_info:
        order_line = OrderLine()
        order_line.order = order_obj
        order_line.product = get_object_or_404(Product, pk=key)
        order_line.price = order_line.product.price
        order_line.count = cart_info[key]
        order_line.save()
    del request.session['cart_info']  # обновляем корзину


# выводим страницу после оплаты заказа

def addorder(request):
    return render(
        request,
        'addorder.html'
    )


# регистрируем пользователя сразу как он заполняет форму
def add_user(name, email):
    if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
        return
    password = get_random_string(10)
    user = User.objects.create_user(email, email, password)
    user.first_name = name
    group = Group.objects.get(name='Клиенты')
    user.groups.add(group)
    user.save()
 # отправляем письмо с данными для регистрации

    text = get_template('registration/registration_email.html')
    html = get_template('registration/registration_email.html')

    context = {'username': email, 'password': password}
    subject = 'Регистрация'
    from_email = 'admin@mysite.ru'
    text_content = text.render(context)
    html_content = html.render(context)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
