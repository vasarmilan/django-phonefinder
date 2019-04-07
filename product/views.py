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


def product_list(request: django.http.request.HttpRequest):
    active_criteria = Criterion.objects.filter(active=True)
    combinations = itertools.combinations(active_criteria, 2)
    comparisons = [
        {'name0': combination[0].name,
         'name1': combination[1].name,
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


def _comparison_matrix(get_data):
    """
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
    return np.asarray(weights).squeeze()


def complete_pcm_validate_ajax(request: django.http.request.HttpRequest):
    get_data = request.GET
    try:
        _weight_vector(get_data)
        success = True
    except illsm.IllsmError:
        success = False
    return JsonResponse(dict(success=success))


def product_list_ajax(request: django.http.request.HttpRequest):
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
    products = Product.objects.filter(**filters)
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
    except illsm.IllsmError:
        products = []

    return(render(request,
                  'product/product_list.html',
                  dict(products=products, jsvars=jsvars)))
