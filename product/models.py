import os
import json
import re
from urllib.request import urlopen

from django import conf
from django.db import models
from django.apps import apps
from django.db import transaction
from django.utils.text import slugify
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


#  helper functions
#  (could be rearranged to separate file if
#  there will be too much)
def to_float(input):
    return float(re.sub('[^\d.]', '', input))


PRODUCT_DATA = os.path.join(conf.settings.BASE_DIR,
                            'product_data.json')


class Criterion(models.Model):

    name = models.CharField(unique=True, max_length=50)
    display_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    compute = models.CharField(blank=True, max_length=250)

    def compute_data(self):
        if not self.compute:
            return []
        res = [self.compute.split()[0]]
        for pk in self.compute.split()[1:]:
            res.append(apps.get_model('product', 'Criterion')
                       .objects.filter(pk=pk)[0])
        return res

    class Meta:
        verbose_name = "Criterion"
        verbose_name_plural = "Criteria"

    def __str__(self):
        return self.display_name

    @property
    def slug(self):
        return slugify(self.name)

    # TODO: do this bettery with db query!
    # (it shouldnt matter much with very few records though)
    @classmethod
    def find_by_slug(cls, slug):
        all = cls.objects.filter(active=True)
        return next(iter(filter(lambda x: x.slug == slug, all)))


class Attribute(models.Model):

    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50, choices=(
        ('screen-size', 'Screen Size'),
    ))
    external_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    format = models.CharField(max_length=50, default="{}")

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"

    def __str__(self):
        return self.name

    def convertfunc(self):
        if self.type == 'screen-size':
            def inner(input):
                return to_float(input.split(',')[0])
        # type (IPS amoled etc.)
        elif self.type == 'first-word':
            def inner(input):
                return input.split()[0]
        # resolution
        elif self.type == 'resolution':
            def inner(input):
                return 'x'.join(re.findall('\d+', input)[:2])
        elif self.type == 'battery_mah':
            def inner(input):
                return re.findall('\d+', input)[0]
        elif self.type == 'str':
            def inner(input):
                return str(input)
        else:
            raise TypeError(f"Not supported type {self.type}")
        return inner


class Product(models.Model):

    name = models.CharField(max_length=250, unique=True)
    slug = models.CharField(max_length=250, unique=True)
    price = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # from external source
    price_last_refreshed = models.DateField()

    class Meta:
        ordering = ('name',)
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def point(self, crit_weights):
        """
        params:
        crit_weights -- dictionary
            format: {criterion.slug:
            criterion.weight (obtained from website form)}
        """
        res = 0
        for key in crit_weights:
            weight = crit_weights[key]
            criterion = Criterion.objects.filter(pk=key)[0]
            product_rating = self.productrating_set.filter(
                criterion=criterion)[0].rating
            res += weight*float(product_rating)
        return res

    def get_attribute(self, attr_id):
        attr = Attribute.objects.filter(pk=attr_id)[0]
        product_attr = apps.get_model(
            'product', 'ProductAttribute').objects.filter(
                product=self, attribute=attr
            )[0]
        return product_attr.value_display

    def get_attribute_value(self, attr_id):
        attr = Attribute.objects.filter(pk=attr_id)[0]
        product_attr = apps.get_model(
            'product', 'ProductAttribute').objects.filter(
                product=self, attribute=attr
            )[0]
        return product_attr.value

    @property
    def ratings(self):
        return self.productrating_set.all()\
            .order_by('criterion__name')

    @property
    def active_ratings(self):
        return self.productrating_set.filter(
            criterion__active=True).order_by('criterion__name')

    @property
    def description_lines(self):
        res = []
        res.append(
            f"{self.get_attribute(10001)} {self.get_attribute(10003)}\
            {self.get_attribute(10002)} kapacitív érintőkijelző\n")
        res.append(f"{self.get_attribute(10004)} akkumulátor")
        return res

#     6,3" FHD+ (2340x1080) IPS FullView kijelző
# 24/2+20/2MP kamera
# Kirin710 8mag 2.2GHz

    @property
    def active_attributes(self):
        return self.productattribute_set.all().order_by('attribute__name')

    image = models.ImageField(upload_to='product', blank=True)
    image_url = models.CharField(max_length=500)

    @classmethod
    def get_product_data(cls):
        with open(PRODUCT_DATA) as data:
            return json.load(data)

    def _update_product_image(self):
        if self.image:
            return
        fpath = os.path.join(
            conf.settings.MEDIA_ROOT,
            'product', 'image_' + self.slug
        )
        if os.path.isfile(fpath):
            # TODO: set this file as product iamge!!!!
            self.image.name = os.path.join(
                'product', 'image_' + self.slug)
            self.save()
        else:
            url = self.image_url
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(url).read())
            img_temp.flush()
            self.image.save(f"image_{self.slug}", File(img_temp))

    @classmethod
    @transaction.atomic
    def sync_product_data(cls):
        ProductRating = apps.get_model('product',
                                       'ProductRating')
        ProductAttribute = apps.get_model('product',
                                          'ProductAttribute')
        attributes = Attribute.objects.all()
        data = cls.get_product_data()
        products = data.values()
        for product in products:
            prod_obj = cls.objects.filter(id=product['id'])
            if not prod_obj:
                prod_obj = cls.objects.create(
                    id=product['id'],
                    name=product['name'],
                    price=product['price']['árukereső'],
                    price_last_refreshed=product['price']['last_modified'],
                    image_url=product['image_url'])
            else:
                prod_obj = prod_obj[0]
            prod_obj._update_product_image()
            ratings = product['ratings']
            for criterion_name in ratings.keys():
                criterion = Criterion.objects.filter(name=criterion_name)
                if criterion:
                    if not ProductRating.objects.filter(
                            product=prod_obj,
                            criterion=criterion[0]):
                        ProductRating.objects.create(
                            product=prod_obj,
                            criterion=criterion[0],
                            rating=ratings[criterion_name]
                        )
            specs = product['specs']
            for attribute in attributes:
                if not ProductAttribute.objects.filter(
                        product=prod_obj, attribute=attribute):
                    value = specs[attribute.external_name]
                    product_attribute = ProductAttribute(
                        product=prod_obj,
                        attribute=attribute
                    )
                    # to use setter; probably wouldnt work as
                    # argument
                    product_attribute.value = value
                    product_attribute.save()
            #  existing comp ratings are handled by the method
            prod_obj.fill_computed_ratings()

    @transaction.atomic
    def fill_computed_ratings(self):
        computed_criteria = Criterion.objects.all().exclude(compute='')
        ProductRating = apps.get_model(
            'product', 'ProductRating')
        ratings = self.productrating_set.all()
        for computed_criterion in computed_criteria:
            if not ProductRating.objects.filter(
                    criterion=computed_criterion,
                    product=self
            ):
                compute_data = computed_criterion.compute_data()
                if compute_data[0] == 'avg':
                    num = 0
                    length = len(compute_data) - 1
                    for criterion in compute_data[1:]:
                        num += ratings.filter(
                            criterion=criterion)[0].rating
                    ProductRating.objects.create(
                        product=self,
                        criterion=computed_criterion,
                        rating=num/length
                    )
        return None


class ProductAttribute(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    # should not be set directly, only through setter
    _value_json = models.TextField()

    @property
    def value(self):
        return json.loads(self._value_json)

    @value.setter
    def value(self, val):
        convertfunc = self.attribute.convertfunc()
        self._value_json = json.dumps(convertfunc(val))

    #  readonly
    @property
    def value_display(self):
        if not self._value_json:
            return ''
        elif type(self.value) in (list, tuple):
            return self.attribute.format.format(*self.value)
        else:
            return self.attribute.format.format(self.value)

    class Meta:
        verbose_name = "ProductAttribute"
        verbose_name_plural = "ProductAttributes"

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: "


class ProductRating(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    rating = models.DecimalField(decimal_places=2, max_digits=4)

    class Meta:
        verbose_name = "ProductRating"
        verbose_name_plural = "ProductRatings"

    def __str__(self):
        return f"{self.product.name} - {self.criterion.name}: {self.rating}"

    @property
    def rating_bar(self):
        # TODO cleanme
        rating_effective = min(int(2*(max(self.rating-5, 0))), 10)
        return rating_effective*'o'
