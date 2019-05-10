import django
import itertools
from django.http import JsonResponse
from django.shortcuts import render
from .models import Product, Criterion
from .illsm import illsm
import numpy as np
from random import shuffle
import logging

_logger = logging.getLogger(__name__)


def _comparison_matrix(get_data):
    """
    get_data: dict; with the comp_id-s as keys (as defined
        inside this function)
        and ratings are the values (as percent)
    returns a PCM (pairwise comparison) "matrix" in [[...], [...]] form
    indexed (ordered) by the id of the criteria
    """
    criteria = Criterion.objects.filter(active=True).order_by('pk')
    n = len(criteria)
    PCM = np.eye(n)
    for i, j in itertools.product(range(n), range(n)):
        crit1 = criteria[i]
        crit2 = criteria[j]
        comp_id = f"comp__{str(crit1.pk)}_{str(crit2.pk)}"
        if comp_id in get_data.keys() and get_data[comp_id]:
            elem = int(get_data[comp_id])/100
            PCM[i, j] = elem/(1-elem)
            PCM[j, i] = (1-elem)/elem
    return PCM


def _weight_vector(get_data):
    PCM = _comparison_matrix(get_data)
    weights = illsm.weights(PCM)
    res = np.asarray(weights).squeeze()
    return res


def complete_pcm_validate_ajax(request: django.http.request.HttpRequest):
    get_data = request.GET
    try:
        _weight_vector(get_data)
        success = True
    except illsm.IllsmError:
        success = False
    return JsonResponse(dict(success=success))


def _minimal_combinations(combinations):
    """
    combinations:
        subset of the (set) product of all active criteria
        itself; that is enough for the illsm method to work (connected matrix)
        represented as a list of tuples
    """
    # in data format to be passed to _weight_wector

    # adds combinations gradually;
    # tests if the matrix is connected
    # using the illsm module; and if it is, returns
    combinations_added = []
    get_data = dict()
    for combination in combinations:
        id = f"comp__{combination[0].pk}_{combination[1].pk}"
        # could be any value
        get_data[id] = 50
        combinations_added.append(combination)
        try:
            _weight_vector(get_data)
            break
        except illsm.IllsmError:
            _logger.warn(f'error with combinations {list(get_data.keys())}')
    _logger.warn(f'SUCCESS with combinations {list(get_data.keys())}')
    _logger.warn(f'{len(list(combinations_added))}/{len(list(combinations))} added')
    return combinations_added


def _apply_custom_filters(products, get_data):
    cats = []
    res = []
    for key in get_data.keys():
        if key.startswith('screensize') and get_data[key] == '1':
            cats.append(int(key[10:]))
    _logger.warning(10*'-')
    _logger.warning(cats)
    _logger.warning(10*'-')
    for product in products:
        screensize = product.get_attribute_value(10001)
        if any([screensize <= 5 and 0 in cats,
                screensize <= 5.5 and 1 in cats,
                screensize <= 6 and 2 in cats,
                screensize >= 6 and 3 in cats]):
            res.append(product)
    return Product.objects.filter(pk__in=[pr.pk for pr in res])


def _product_list_ajax(request: django.http.request.HttpRequest,
                       all_products=False):
    filters = dict()
    filter_map = {'minprice': 'price__gte',
                  'maxprice': 'price__lte'}
    get_data = request.GET
    # removing the maxprice attr if it is zero; assuming that
    # means that there is no maxprice filter
    if get_data.get('maxprice') == "0":
        del(filter_map['maxprice'])
    for filter_str in filter_map.keys():
        if filter_str in get_data:
            filters[filter_map[filter_str]] = get_data[filter_str]
    if filters:
        products = Product.objects.filter(**filters)
    else:
        products = Product.objects.all()
    products = _apply_custom_filters(products, get_data)
    jsvars = dict()
    if products:
        jsvars = {
            'default_slider_price_from': min(products.values_list("price"))[0],
            'default_slider_price_to': max(products.values_list("price"))[0],
            'default_minprice': min(products.values_list("price"))[0],
            'default_maxprice': max(products.values_list("price"))[0],
        }
    # TODO: remove later; this is just temporary, crits should be computed
    # using the comparison data obtained
    criteria = Criterion.objects.filter(active=True).order_by('pk')
    try:
        weights = _weight_vector(get_data)
        weight_dict = {
            criteria[i].pk: weights[i]
            for i in range(len(criteria))
        }
        products = sorted(products, key=lambda product:
                          product.point(weight_dict), reverse=True)
        # TODO: optimization (point function is called twice for no reason)
        product_list = [[i+1, products[i], products[i].point(weight_dict)]
                        for i in range(len(products))]
    except illsm.IllsmError:
        if not all_products:
            products = []
            product_list = []
        else:
            product_list = [[i + 1, products[i], 0]
                            for i in range(len(products))]
    if product_list:
        reference = product_list[0][2]
        for product in product_list:
            product[2] = int(product[2] / reference * 100)
    return(render(request,
                  'product/product_list.html',
                  dict(products=product_list[:30], jsvars=jsvars)))


def product_list(request: django.http.request.HttpRequest):
    active_criteria = Criterion.objects.filter(active=True)
    combinations = list(itertools.combinations(active_criteria, 2))
    shuffle(combinations)
    combinations = _minimal_combinations(combinations)
    comparisons = [
        {'name0': combination[0].display_name,
         'name1': combination[1].display_name,
         'description0': combination[0].description,
         'description1': combination[1].description,
         'id': 'comp__' + str(combination[0].pk) + '_' +
         str(combination[1].pk)}
        for combination in combinations
    ]
    # randomize the order
    shuffle(comparisons)
    return(render(request,
                  'product/products.html',
                  dict(get_dict=repr(request.GET),
                       criterions=active_criteria,
                       comparisons=comparisons
                       )))


def product_list_ajax(request):
    return _product_list_ajax(request, False)


def all_product_list_ajax(request):
    return _product_list_ajax(request, True)
