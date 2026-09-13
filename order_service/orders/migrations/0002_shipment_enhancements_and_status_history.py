from django.db import migrations, models
import django.db.models.deletion
import uuid


import secrets

def default_tracking_code():
    return f"TRK-{secrets.token_hex(6).upper()}"

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        # Alter order & suborder OneToOne -> ForeignKey
        migrations.AlterField(
            model_name='shipping',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to='orders.order'),
        ),
        migrations.AlterField(
            model_name='shipping',
            name='suborder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to='orders.suborder'),
        ),

        # Add shipment new fields
        migrations.AddField(
            model_name='shipping',
            name='status',
            field=models.CharField(choices=[('PREPARING', 'Preparing'), ('LABEL_CREATED', 'Label Created'), ('SHIPPED', 'Shipped'), ('IN_TRANSIT', 'In Transit'), ('OUT_FOR_DELIVERY', 'Out for Delivery'), ('DELIVERED', 'Delivered'), ('FAILED_ATTEMPT', 'Failed Delivery Attempt'), ('RETURNED', 'Returned'), ('CANCELLED', 'Cancelled')], db_index=True, default='PREPARING', max_length=30),
        ),
        migrations.AddField(
            model_name='shipping',
            name='estimated_delivery_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shipping',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shipping',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='shipping',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='shipping',
            name='tracking_code',
            field=models.CharField(db_index=True, default=default_tracking_code, max_length=100, unique=True),
        ),

        # Create StatusHistory model
        migrations.CreateModel(
            name='StatusHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entity_type', models.CharField(db_index=True, max_length=50)),
                ('entity_id', models.UUIDField(db_index=True)),
                ('from_status', models.CharField(blank=True, default='', max_length=50)),
                ('to_status', models.CharField(max_length=50)),
                ('changed_by', models.UUIDField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['entity_type', 'entity_id'], name='orders_stat_entity__idx'),
                    models.Index(fields=['created_at'], name='orders_stat_created_idx'),
                ],
            },
        ),
    ]
