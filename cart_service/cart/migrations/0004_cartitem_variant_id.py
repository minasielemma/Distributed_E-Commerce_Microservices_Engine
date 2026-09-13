from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_itemrequest_admin_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='variant_id',
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='variant_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='image_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
    ]
