import uuid 
from django .db import models 

class Payment (models .Model ):
    STATUS_CHOICES =(
    ('PENDING','Pending Payment'),
    ('PAID','Paid / Succeeded'),
    ('FAILED','Failed'),
    ('REFUNDED','Refunded'),
    )

    id =models .UUIDField (primary_key =True ,default =uuid .uuid4 ,editable =False )
    tenant_id =models .UUIDField (null =True ,blank =True ,db_index =True )
    order_id =models .UUIDField (
    db_index =True ,unique =True ,
    help_text ="Enforces one Payment record per order; prevents double-charge race condition."
    )
    customer_id =models .UUIDField (db_index =True )
    amount =models .DecimalField (max_digits =10 ,decimal_places =2 )

    discount_code =models .CharField (
    max_length =50 ,blank =True ,null =True ,
    help_text ="Coupon code applied at checkout (if any)."
    )
    discount_amount =models .DecimalField (
    max_digits =10 ,decimal_places =2 ,default =0 ,
    help_text ="Amount discounted from the original subtotal."
    )
    provider =models .CharField (max_length =50 ,default ='POLAR')
    status =models .CharField (max_length =20 ,choices =STATUS_CHOICES ,default ='PENDING',db_index =True )
    polar_checkout_id =models .CharField (max_length =255 ,blank =True ,null =True ,db_index =True )
    polar_checkout_url =models .URLField (blank =True ,null =True )
    created_at =models .DateTimeField (auto_now_add =True )
    updated_at =models .DateTimeField (auto_now =True )

    class Meta :
        indexes =[
        models .Index (fields =['tenant_id','status']),
        models .Index (fields =['order_id','status']),
        models .Index (fields =['customer_id','status']),
        models .Index (fields =['polar_checkout_id']),
        ]

    def __str__ (self ):
        return f"Payment {self .id } for Order {self .order_id } - [{self .status }] (${self .amount })"
