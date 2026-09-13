import uuid 
from django .db import models 


class CouponRedemption (models .Model ):
    """Tracks every coupon redemption with a two-phase commit pattern.

    Lifecycle:
        PENDING   – reserved at checkout (coupon counter incremented)
        CONFIRMED – payment confirmed (permanent; counter stays incremented)
        REVERSED  – order cancelled / payment failed (counter decremented back)
    """

    STATUS_PENDING ='PENDING'
    STATUS_CONFIRMED ='CONFIRMED'
    STATUS_REVERSED ='REVERSED'

    STATUS_CHOICES =[
    (STATUS_PENDING ,'Pending (reserved)'),
    (STATUS_CONFIRMED ,'Confirmed (payment succeeded)'),
    (STATUS_REVERSED ,'Reversed (order cancelled)'),
    ]

    id =models .UUIDField (primary_key =True ,default =uuid .uuid4 ,editable =False )
    discount_code =models .ForeignKey (
    'DiscountCode',
    on_delete =models .PROTECT ,
    related_name ='redemptions',
    )
    order_id =models .UUIDField (db_index =True ,unique =True ,
    help_text ="One redemption record per order")
    customer_id =models .UUIDField (db_index =True )
    discount_amount =models .DecimalField (max_digits =10 ,decimal_places =2 )
    status =models .CharField (
    max_length =20 ,choices =STATUS_CHOICES ,
    default =STATUS_PENDING ,db_index =True ,
    )
    created_at =models .DateTimeField (auto_now_add =True )
    updated_at =models .DateTimeField (auto_now =True )

    class Meta :
        ordering =['-created_at']
        indexes =[
        models .Index (fields =['order_id','status']),
        models .Index (fields =['customer_id','status']),
        models .Index (fields =['discount_code','status']),
        ]

    def __str__ (self ):
        return (
        f"Redemption({self .discount_code .code }, "
        f"order={self .order_id }, status={self .status })"
        )
