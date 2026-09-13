"""
Migration: Add per_customer_limit to DiscountCode + create CouponRedemption model.
"""
import uuid 
import django .db .models .deletion 
from django .db import migrations ,models 


class Migration (migrations .Migration ):

    dependencies =[
    ('catalog','0007_product_polar_product_id'),
    ]

    operations =[

    migrations .AddField (
    model_name ='discountcode',
    name ='per_customer_limit',
    field =models .PositiveIntegerField (
    default =1 ,
    help_text ='Max times a single customer may use this code. Default: 1.',
    ),
    ),


    migrations .CreateModel (
    name ='CouponRedemption',
    fields =[
    ('id',models .UUIDField (
    primary_key =True ,default =uuid .uuid4 ,editable =False ,serialize =False ,
    )),
    ('order_id',models .UUIDField (
    db_index =True ,unique =True ,
    help_text ='One redemption record per order',
    )),
    ('customer_id',models .UUIDField (db_index =True )),
    ('discount_amount',models .DecimalField (decimal_places =2 ,max_digits =10 )),
    ('status',models .CharField (
    choices =[
    ('PENDING','Pending (reserved)'),
    ('CONFIRMED','Confirmed (payment succeeded)'),
    ('REVERSED','Reversed (order cancelled)'),
    ],
    db_index =True ,
    default ='PENDING',
    max_length =20 ,
    )),
    ('created_at',models .DateTimeField (auto_now_add =True )),
    ('updated_at',models .DateTimeField (auto_now =True )),
    ('discount_code',models .ForeignKey (
    on_delete =django .db .models .deletion .PROTECT ,
    related_name ='redemptions',
    to ='catalog.discountcode',
    )),
    ],
    options ={
    'ordering':['-created_at'],
    },
    ),


    migrations .AddIndex (
    model_name ='couponredemption',
    index =models .Index (
    fields =['order_id','status'],
    name ='coupon_redemption_order_status_idx',
    ),
    ),
    migrations .AddIndex (
    model_name ='couponredemption',
    index =models .Index (
    fields =['customer_id','status'],
    name ='coupon_redemption_customer_status_idx',
    ),
    ),
    migrations .AddIndex (
    model_name ='couponredemption',
    index =models .Index (
    fields =['discount_code','status'],
    name ='coupon_redemption_code_status_idx',
    ),
    ),
    ]
