"""
Migration: Add FinancialRiskEvent model + seed 5100 Discount account.
"""
import uuid 
from django .db import migrations ,models 


class Migration (migrations .Migration ):

    dependencies =[
    ('finance','0003_tenantledger_ledgerentry'),
    ]

    operations =[
    migrations .CreateModel (
    name ='FinancialRiskEvent',
    fields =[
    ('id',models .UUIDField (
    primary_key =True ,default =uuid .uuid4 ,editable =False ,serialize =False ,
    )),
    ('order_id',models .UUIDField (db_index =True ,null =True ,blank =True )),
    ('customer_id',models .UUIDField (db_index =True ,null =True ,blank =True )),
    ('tenant_id',models .UUIDField (db_index =True ,null =True ,blank =True )),
    ('rule_name',models .CharField (max_length =100 ,db_index =True ,
    help_text ='Identifier of the risk rule that fired.')),
    ('severity',models .CharField (
    max_length =10 ,
    choices =[('LOW','Low'),('MEDIUM','Medium'),('HIGH','High')],
    default ='MEDIUM',db_index =True ,
    )),
    ('description',models .TextField ()),
    ('payload',models .JSONField (default =dict ,
    help_text ='Raw event data that triggered this risk event.')),
    ('created_at',models .DateTimeField (auto_now_add =True )),
    ('resolved',models .BooleanField (default =False ,db_index =True )),
    ],
    options ={'ordering':['-created_at']},
    ),
    migrations .AddIndex (
    model_name ='financialriskevent',
    index =models .Index (fields =['severity','resolved'],name ='risk_evt_severity_resolved_idx'),
    ),
    migrations .AddIndex (
    model_name ='financialriskevent',
    index =models .Index (fields =['tenant_id','severity'],name ='risk_evt_tenant_severity_idx'),
    ),
    migrations .AddIndex (
    model_name ='financialriskevent',
    index =models .Index (fields =['order_id'],name ='risk_evt_order_idx'),
    ),
    ]
