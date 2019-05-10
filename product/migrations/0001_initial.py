# Generated by Django 2.0.10 on 2019-04-12 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('screen-size', 'Screen Size')], max_length=50)),
                ('external_name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('format', models.CharField(default='{}', max_length=50)),
            ],
            options={
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
            },
        ),
        migrations.CreateModel(
            name='Criterion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('compute', models.CharField(blank=True, max_length=250)),
            ],
            options={
                'verbose_name': 'Criterion',
                'verbose_name_plural': 'Criteria',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250, unique=True)),
                ('slug', models.CharField(max_length=250, unique=True)),
                ('price', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('price_last_refreshed', models.DateField()),
                ('image', models.ImageField(blank=True, upload_to='product')),
                ('image_url', models.CharField(max_length=500)),
            ],
            options={
                'verbose_name': 'product',
                'verbose_name_plural': 'products',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ProductAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_value_json', models.TextField()),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Attribute')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product')),
            ],
            options={
                'verbose_name': 'ProductAttribute',
                'verbose_name_plural': 'ProductAttributes',
            },
        ),
        migrations.CreateModel(
            name='ProductRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.DecimalField(decimal_places=2, max_digits=4)),
                ('criterion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Criterion')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product')),
            ],
            options={
                'verbose_name': 'ProductRating',
                'verbose_name_plural': 'ProductRatings',
            },
        ),
    ]
