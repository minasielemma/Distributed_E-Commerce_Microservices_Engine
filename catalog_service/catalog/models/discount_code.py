import uuid 
from decimal import Decimal 
from django .db import models 
from django .utils import timezone 


class DiscountCode (models .Model ):
    DISCOUNT_TYPES =[
    ('PERCENTAGE','Percentage'),
    ('FIXED','Fixed Amount'),
    ('FREE_SHIPPING','Free Shipping'),
    ]

    id =models .UUIDField (primary_key =True ,default =uuid .uuid4 ,editable =False )
    tenant_id =models .UUIDField (null =True ,blank =True ,db_index =True )
    code =models .CharField (max_length =50 ,unique =True ,db_index =True )
    discount_type =models .CharField (
    max_length =20 ,choices =DISCOUNT_TYPES ,default ='PERCENTAGE'
    )
    value =models .DecimalField (max_digits =10 ,decimal_places =2 )
    min_purchase_amount =models .DecimalField (
    max_digits =10 ,decimal_places =2 ,default =Decimal ('0.00')
    )
    max_discount_amount =models .DecimalField (
    max_digits =10 ,decimal_places =2 ,null =True ,blank =True 
    )
    valid_from =models .DateTimeField (default =timezone .now )
    valid_to =models .DateTimeField (null =True ,blank =True )


    usage_limit =models .PositiveIntegerField (
    null =True ,blank =True ,
    help_text ="Maximum total redemptions across all customers. NULL = unlimited."
    )
    times_used =models .PositiveIntegerField (
    default =0 ,
    help_text ="Current confirmed redemption count. Modified only inside "
    "select_for_update transactions."
    )
    per_customer_limit =models .PositiveIntegerField (
    default =1 ,
    help_text ="Max times a single customer may use this code. Default: 1."
    )

    is_active =models .BooleanField (default =True )
    created_at =models .DateTimeField (auto_now_add =True )

    class Meta :
        ordering =['-created_at']


    def is_valid (self ,subtotal =Decimal ('0.00'),customer_id =None ):
        """Return (bool, reason_str).  Checks all business rules."""
        now =timezone .now ()
        if not self .is_active :
            return False ,"Discount code is inactive."
        if self .valid_from and now <self .valid_from :
            return False ,"Discount code is not yet valid."
        if self .valid_to and now >self .valid_to :
            return False ,"Discount code has expired."
        if self .usage_limit is not None and self .times_used >=self .usage_limit :
            return False ,"Discount code usage limit reached."
        if subtotal <self .min_purchase_amount :
            return False ,(
            f"Minimum purchase amount of {self .min_purchase_amount } required."
            )

        if customer_id is not None and self .per_customer_limit :
            from .coupon_redemption import CouponRedemption 
            used_by_customer =CouponRedemption .objects .filter (
            discount_code =self ,
            customer_id =customer_id ,
            status__in =[
            CouponRedemption .STATUS_PENDING ,
            CouponRedemption .STATUS_CONFIRMED ,
            ],
            ).count ()
            if used_by_customer >=self .per_customer_limit :
                return False ,(
                f"You have already used this code "
                f"{used_by_customer } time(s) (limit: {self .per_customer_limit })."
                )
        return True ,"Valid"

    def calculate_discount (self ,subtotal ):
        if self .discount_type =='PERCENTAGE':
            discount =(subtotal *self .value )/Decimal ('100.00')
            if self .max_discount_amount :
                discount =min (discount ,self .max_discount_amount )
            return discount .quantize (Decimal ('0.01'))
        elif self .discount_type =='FIXED':
            discount =min (self .value ,subtotal )
            return discount .quantize (Decimal ('0.01'))
        return Decimal ('0.00')

    def __str__ (self ):
        return f"Coupon {self .code } ({self .discount_type }: {self .value })"
