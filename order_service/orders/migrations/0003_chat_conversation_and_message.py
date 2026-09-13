from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_shipment_enhancements_and_status_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('customer_id', models.UUIDField(db_index=True)),
                ('customer_name', models.CharField(blank=True, default='', max_length=150)),
                ('order_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('subject', models.CharField(default='Order Inquiry', max_length=255)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('CLOSED', 'Closed')], default='OPEN', max_length=20)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sender_id', models.UUIDField()),
                ('sender_type', models.CharField(choices=[('CUSTOMER', 'Customer'), ('SHOP_OWNER', 'Shop Owner'), ('SYSTEM', 'System')], max_length=20)),
                ('sender_name', models.CharField(blank=True, default='', max_length=150)),
                ('content', models.TextField()),
                ('is_read_by_customer', models.BooleanField(default=False)),
                ('is_read_by_owner', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='orders.conversation')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['tenant_id', 'customer_id'], name='orders_conv_tenant_cust_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['tenant_id', 'status'], name='orders_conv_tenant_stat_idx'),
        ),
    ]
