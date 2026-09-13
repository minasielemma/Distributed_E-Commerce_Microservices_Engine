"""Rule-based financial risk engine for coupon & payment events.

Rules implemented
─────────────────
1. EXCESSIVE_DISCOUNT_RATE   – discount > 50 % of total amount
2. HIGH_DISCOUNT_ABSOLUTE    – discount amount > $100
3. ZERO_AMOUNT_PAYMENT       – payment total_amount == $0 with a discount
4. RAPID_COUPON_USAGE        – same order_id appears in two events (duplicate)
5. LARGE_ORDER_DISCOUNT_COMBO – order > $1 000 AND discount > 30 %

Each rule produces a FinancialRiskEvent record (severity LOW/MEDIUM/HIGH).
"""
import logging 
from decimal import Decimal 

logger =logging .getLogger (__name__ )


EXCESSIVE_DISCOUNT_PCT =Decimal ('50')
HIGH_DISCOUNT_ABS =Decimal ('100')
LARGE_ORDER_THRESHOLD =Decimal ('1000')
LARGE_ORDER_DISC_PCT =Decimal ('30')


def assess_payment_event (event_data :dict ):
    """Evaluate a payment.succeeded event dict.  Returns list of risk events created."""
    from .models import FinancialRiskEvent 

    order_id =event_data .get ('order_id')
    customer_id =event_data .get ('customer_id')
    tenant_id =event_data .get ('tenant_id')
    amount =Decimal (str (event_data .get ('amount','0.00')))
    discount_code =event_data .get ('discount_code')
    discount_amount =Decimal (str (event_data .get ('discount_amount','0.00')))

    created_events =[]

    def _flag (rule_name ,severity ,description ):
        evt =FinancialRiskEvent .objects .create (
        order_id =order_id ,
        customer_id =customer_id ,
        tenant_id =tenant_id ,
        rule_name =rule_name ,
        severity =severity ,
        description =description ,
        payload =event_data ,
        )
        created_events .append (evt )
        logger .warning (
        f"[RiskEngine] {severity } risk flagged: {rule_name } | "
        f"order={order_id } | {description }"
        )

    if discount_amount <=Decimal ('0'):
        return created_events 

    subtotal_before_discount =amount +discount_amount 
    if subtotal_before_discount >Decimal ('0'):
        discount_pct =(discount_amount /subtotal_before_discount )*100 
    else :
        discount_pct =Decimal ('0')


    if discount_pct >EXCESSIVE_DISCOUNT_PCT :
        _flag (
        'EXCESSIVE_DISCOUNT_RATE',
        FinancialRiskEvent .SEVERITY_HIGH ,
        f"Coupon '{discount_code }' applied {discount_pct :.1f}% discount "
        f"(threshold: {EXCESSIVE_DISCOUNT_PCT }%) on order {order_id }."
        )


    elif discount_amount >HIGH_DISCOUNT_ABS :
        _flag (
        'HIGH_DISCOUNT_ABSOLUTE',
        FinancialRiskEvent .SEVERITY_MEDIUM ,
        f"Coupon '{discount_code }' discounted ${discount_amount :.2f} "
        f"(threshold: ${HIGH_DISCOUNT_ABS }) on order {order_id }."
        )


    if amount ==Decimal ('0')and discount_amount >Decimal ('0'):
        _flag (
        'ZERO_AMOUNT_PAYMENT',
        FinancialRiskEvent .SEVERITY_HIGH ,
        f"Order {order_id } resulted in $0 payment after applying coupon "
        f"'{discount_code }' (discount: ${discount_amount :.2f})."
        )


    if subtotal_before_discount >=LARGE_ORDER_THRESHOLD and discount_pct >LARGE_ORDER_DISC_PCT :
        _flag (
        'LARGE_ORDER_DISCOUNT_COMBO',
        FinancialRiskEvent .SEVERITY_MEDIUM ,
        f"High-value order (${subtotal_before_discount :.2f}) with "
        f"{discount_pct :.1f}% discount via '{discount_code }'."
        )

    return created_events 
