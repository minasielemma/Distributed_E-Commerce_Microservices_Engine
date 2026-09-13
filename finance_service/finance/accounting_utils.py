import uuid 
from decimal import Decimal 
from django .core .exceptions import ValidationError 
from .models import Account ,JournalEntry ,JournalEntryLine 

DEFAULT_ACCOUNTS =[
{'code':'1010','name':'Cash & Bank','type':'ASSET','balance':'DEBIT'},
{'code':'1100','name':'Accounts Receivable','type':'ASSET','balance':'DEBIT'},
{'code':'2000','name':'Payout Payable & Liabilities','type':'LIABILITY','balance':'CREDIT'},
{'code':'3000','name':'Owner Equity','type':'EQUITY','balance':'CREDIT'},
{'code':'4000','name':'Sales Revenue','type':'REVENUE','balance':'CREDIT'},
{'code':'5000','name':'Platform Commission Expense','type':'EXPENSE','balance':'DEBIT'},
{'code':'5100','name':'Coupon & Promotional Discounts','type':'EXPENSE','balance':'DEBIT'},
]

def seed_default_accounts (tenant_id ):
    accounts ={}
    for item in DEFAULT_ACCOUNTS :
        acc ,_ =Account .objects .get_or_create (
        tenant_id =tenant_id ,
        account_code =item ['code'],
        defaults ={
        'account_name':item ['name'],
        'account_type':item ['type'],
        'normal_balance':item ['balance']
        }
        )
        accounts [item ['code']]=acc 
    return accounts 

def post_journal_entry (tenant_id ,description ,lines_data ,reference_id =""):
    total_debit =Decimal ('0.00')
    total_credit =Decimal ('0.00')

    for line in lines_data :
        amt =Decimal (str (line ['amount']))
        if line ['entry_type']=='DEBIT':
            total_debit +=amt 
        elif line ['entry_type']=='CREDIT':
            total_credit +=amt 

    if total_debit !=total_credit :
        raise ValidationError (f"Unbalanced Journal Entry: Debits (${total_debit }) must equal Credits (${total_credit })")

    entry_number =f"JE-{uuid .uuid4 ().hex [:8 ].upper ()}"
    entry =JournalEntry .objects .create (
    tenant_id =tenant_id ,
    entry_number =entry_number ,
    description =description ,
    reference_id =reference_id ,
    status ='POSTED'
    )

    for line in lines_data :
        JournalEntryLine .objects .create (
        journal_entry =entry ,
        account =line ['account'],
        entry_type =line ['entry_type'],
        amount =Decimal (str (line ['amount']))
        )

    return entry 

def record_payment_ledger_and_invoice (
order_id ,customer_id ,tenant_id ,total_amount ,
items_summary =None ,discount_code =None ,discount_amount =None 
):
    from django .utils import timezone 
    from .models import TenantLedger ,LedgerEntry ,Invoice 

    amount_val =Decimal (str (total_amount ))
    discount_val =Decimal (str (discount_amount or '0.00'))

    if amount_val <=Decimal ('0.00')and discount_val <=Decimal ('0.00'):
        return None ,None ,None 


    if not tenant_id or str (tenant_id ).lower ()in ['none','null','']:
        existing_ledger =TenantLedger .objects .first ()
        if existing_ledger :
            tenant_id =existing_ledger .tenant_id 
        else :
            tenant_id =uuid .UUID ('00000000-0000-0000-0000-000000000001')


    accounts =seed_default_accounts (tenant_id )
    cash_acc =accounts ['1010']
    rev_acc =accounts ['4000']
    liab_acc =accounts ['2000']
    disc_acc =accounts ['5100']

    gross_amount =amount_val +discount_val 
    net_revenue =round (amount_val *Decimal ('0.95'),2 )
    commission =round (amount_val -net_revenue ,2 )


    lines_data =[
    {'account':cash_acc ,'entry_type':'DEBIT','amount':amount_val },
    {'account':rev_acc ,'entry_type':'CREDIT','amount':net_revenue },
    {'account':liab_acc ,'entry_type':'CREDIT','amount':commission },
    ]
    entry =post_journal_entry (
    tenant_id =tenant_id ,
    description =f"Payment for Order #{order_id }",
    lines_data =lines_data ,
    reference_id =str (order_id )
    )


    if discount_val >Decimal ('0.00'):
        disc_lines =[
        {'account':disc_acc ,'entry_type':'DEBIT','amount':discount_val },
        {'account':rev_acc ,'entry_type':'CREDIT','amount':discount_val },
        ]
        post_journal_entry (
        tenant_id =tenant_id ,
        description =(
        f"Coupon '{discount_code }' discount on Order #{order_id } "
        f"(${discount_val :.2f} off)"
        ),
        lines_data =disc_lines ,
        reference_id =f"DISC-{order_id }"
        )


    t_ledger ,_ =TenantLedger .objects .get_or_create (
    tenant_id =tenant_id ,
    defaults ={
    'total_revenue':Decimal ('0.00'),
    'platform_fees_paid':Decimal ('0.00'),
    'available_payout_balance':Decimal ('0.00'),
    }
    )
    t_ledger .total_revenue +=net_revenue 
    t_ledger .platform_fees_paid +=commission 
    t_ledger .available_payout_balance +=net_revenue 
    t_ledger .save ()

    ledger_entry =LedgerEntry .objects .create (
    tenant_id =tenant_id ,
    ledger =t_ledger ,
    entry_type ='CREDIT_SALE',
    amount =amount_val ,
    description =f"Gross Sale Revenue for Order #{order_id }",
    reference_id =str (order_id )
    )


    inv_number =f"INV-{timezone .now ().strftime ('%Y%m')}-{uuid .uuid4 ().hex [:6 ].upper ()}"
    invoice =Invoice .objects .create (
    tenant_id =tenant_id ,
    customer_id =customer_id ,
    order_id =order_id ,
    invoice_number =inv_number ,
    total_amount =amount_val ,
    status ='PAID',
    items_summary =items_summary or []
    )

    return entry ,invoice ,ledger_entry 

