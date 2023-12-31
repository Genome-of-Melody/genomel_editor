# Generated by Django 4.1 on 2023-09-05 12:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('GenomelEditor', '0002_delete_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='chant',
            name='position',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='melody',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='chant',
            name='cantus_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='cao_concordances',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='corpus_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='dataset_idx',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='dataset_name',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='differentia',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='drupal_path',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='feast_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='finalis',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='folio',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='full_text',
            field=models.CharField(default=None, max_length=65025, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='full_text_manuscript',
            field=models.CharField(default=None, max_length=65025, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='genre_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='image_link',
            field=models.CharField(default=None, max_length=511, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='incipit',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='marginalia',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='melody_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='mode',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='notes',
            field=models.CharField(default=None, max_length=65025, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='office_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='sequence',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='siglum',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='source_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chant',
            name='volpiano',
            field=models.CharField(default=None, max_length=65025, null=True),
        ),
    ]
