from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_cart_coupon_code_cart_discount_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemrequest',
            name='admin_response',
            field=models.TextField(blank=True, default=''),
        ),
    ]
