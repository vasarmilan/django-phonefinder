import os
from django.template.defaultfilters import slugify
from django.db import models
from django import conf
from django.apps import apps
from django.db import transaction
from django.utils.text import slugify
import json
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.request import urlopen

PRODUCT_DATA = os.path.join(conf.settings.BASE_DIR,
                            'product_data.json')


class Criterion(models.Model):

    name = models.CharField(unique=True, max_length=50)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Criterion"
        verbose_name_plural = "Criteria"

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)

    # TODO: do this bettery with db query!
    # (it shouldnt matter much with very few records though)
    @classmethod
    def find_by_slug(cls, slug):
        all = cls.objects.filter(active=True)
        return next(iter(filter(lambda x: x.slug == slug, all)))


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
            res += weight*product_rating
        return res

    @property
    def ratings(self):
        return self.productrating_set.all()\
            .order_by('criterion__name')

    image = models.ImageField(upload_to='product', blank=True)
    image_url = models.CharField(max_length=500)

    @classmethod
    def get_product_data(cls):
        with open(PRODUCT_DATA) as data:
            return json.load(data)

    def _update_product_image(self):
        url = self.image_url
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urlopen(url).read())
        img_temp.flush()
        self.image.save(f"image_{self.slug}", File(img_temp))

    @classmethod
    @transaction.atomic
    def sync_product_data(cls):
        ProductRating = apps.get_model('product', 'ProductRating')
        data = cls.get_product_data()
        products = data.values()
        for product in products:
            if not cls.objects.filter(id=product['id']):
                prod_obj = cls.objects.create(
                    id=product['id'],
                    name=product['name'],
                    price=product['price']['árukereső'],
                    price_last_refreshed=product['price']['last_modified'],
                    image_url=product['image_url'])
                prod_obj._update_product_image()
                ratings = product['ratings']
                for criterion_name in ratings.keys():
                    criterion = Criterion.objects.filter(name=criterion_name)
                    if criterion:
                        ProductRating.objects.create(
                            product=prod_obj,
                            criterion=criterion[0],
                            rating=ratings[criterion_name]
                        )


class ProductRating(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    rating = models.IntegerField()

    class Meta:
        verbose_name = "ProductRating"
        verbose_name_plural = "ProductRatings"

    def __str__(self):
        return f"{self.product.name} - {self.criterion.name}: {self.rating}"
