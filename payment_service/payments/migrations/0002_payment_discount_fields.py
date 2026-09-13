"""
Migration: Add unique constraint on order_id + discount fields to Payment.
"""
from django .db import migrations ,models 


class Migration (migrations .Migration ):

    dependencies =[
    ('payments','0001_initial'),
    ]

    operations =[

    migrations .AddField (
    model_name ='payment',
    name ='discount_code',
    field =models .CharField (
    blank =True ,max_length =50 ,null =True ,
    help_text ='Coupon code applied at checkout (if any).',
    ),
    ),

    migrations .AddField (
    model_name ='payment',
    name ='discount_amount',
    field =models .DecimalField (
    decimal_places =2 ,default =0 ,max_digits =10 ,
    help_text ='Amount discounted from the original subtotal.',
    ),
    ),

    migrations .AlterField (
    model_name ='payment',
    name ='order_id',
    field =models .UUIDField (
    db_index =True ,unique =True ,
    help_text ='Enforces one Payment record per order; prevents double-charge race condition.',
    ),
    ),
    ]
