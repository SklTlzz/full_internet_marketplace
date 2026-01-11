from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Category, Product, Size
from django.db.models import Q


class IndexView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = None

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)

        '''
        Например, если мы хотим c каталога зайти на home страницу (основную)
        Ну и если это получается он, то мы возвращаем request, шаблон home_content и context
        И теперь человеку в html вместо старого content придет home_content c этим context
        
        В ином же случае мы просто вернем человеку base.html и текущий контекст
        '''

        return TemplateResponse(request, self.template_name, context)
    
        
class CatalogView(TemplateView):
    template = 'main/base.html'

    FILTER_MAPPING = {
        'color': lambda queryset, value: queryset.filter(color__iexact=value),
        'min_price': lambda queryset, value: queryset.filter(price_gte=value),
        'max_price': lambda queryset, value: queryset.filter(price_lte=value),
        'size': lambda queryset, value: queryset.filter(product_size__size__name=value),
    }

    '''
    queryset - наш массив c продуктами
    value - то, по чему мы фильтруем
    '''

    '''
    FILTER_MAPPING - словарь параметров (флагов), которые отвечают за сортировку 
    Если было бы if else, то мы бы писали просто if filter=color, фильтруем так и там было бы очень много
        if else if else и это как бы некрасиво и долго, поэтому есть маппинг
    '''

    def get_context_data(self, **kwargs):
        context = self.get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        products = Product.objects.all().order_by('-created_at')
        current_category = None

        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            '''
            пытаемся достать категорию по тому слагу, который указан еще в category_slug
                тобишь по тому слагу, который мы получили от запроса пользователя
            '''
            products = products.filter(Category=current_category) # наши продукты мы фильтруем по категории, которую указал человек

        query = self.request.GET.get('q')
        
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            '''
            человек делает запрос c Q параметром, затем мы либо пытаемся в названии найти слово/словосочетание, которое написал человек, либо
            в описании (description)
            '''

        filter_params = {}

        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)

            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''

            '''
            человек фильтирует, в urlке дает какой-то параметр, мы в цикле проходим, смотрим его параметры,
            сравниваем c FILTER_MAPPING, ну и если мы находим его параметры, то фильтруем:
            products = filter_func(products, value)

            ну а потом если есть фильтрация, то есть фильтрация (filter_params[param] = value), если нет - 
            то нет (filter_params[param] = '')
            '''

        filter_params['q'] = query or ''

        context.update({
            'categories': categories,
            'products': products,
            'current_category': category_slug,
            'filter_params': filter_params,
            'sizes': Size.objects.all(),
            'search_query': query or ''
        })

        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search'] = True
            
        '''
        это разделение поиска от обычного каталога, то есть, если в запросе пользователя
        есть упоминание поиска, то мы показываем ему поиск
        '''

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if request.headers.get('HX-request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            
            template = 'main/filter_modal.html' if request.GET.get('show_filter') == 'true' else 'main/catalog.html'
    
            '''
            то, что раньше - подключается уже при включенном catalog.html если человек, заходя на сайт жмет на поиск, то выдаем ему поиск, нет - нет
            template - Если он нажимает на модалку фильтров, то мы выдаем ему фильтры, если нет - тогда просто наш каталог
            '''

            return TemplateResponse(request, template, context)
        
        return TemplateResponse(request, self.template_name, context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        product = self.get_object()
        context['categories'] = Category.objects.all()
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        context['current_category'] = product.category.slug

        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)

        if request.headers.get('HX-request'):
            return TemplateResponse(request, 'main/product_detail.html', context)

        raise TemplateResponse(request, self.template_name, context)
