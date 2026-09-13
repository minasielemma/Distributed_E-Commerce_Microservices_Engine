"""FinancialRiskEvent model — records detected risk signals for audit and alerting."""
import uuid 
from django .db import models 


class FinancialRiskEvent (models .Model ):
    SEVERITY_LOW ='LOW'
    SEVERITY_MEDIUM ='MEDIUM'
    SEVERITY_HIGH ='HIGH'

    SEVERITY_CHOICES =[
    (SEVERITY_LOW ,'Low'),
    (SEVERITY_MEDIUM ,'Medium'),
    (SEVERITY_HIGH ,'High'),
    ]

    id =models .UUIDField (primary_key =True ,default =uuid .uuid4 ,editable =False )
    order_id =models .UUIDField (db_index =True ,null =True ,blank =True )
    customer_id =models .UUIDField (db_index =True ,null =True ,blank =True )
    tenant_id =models .UUIDField (db_index =True ,null =True ,blank =True )
    rule_name =models .CharField (max_length =100 ,db_index =True ,
    help_text ="Identifier of the risk rule that fired.")
    severity =models .CharField (max_length =10 ,choices =SEVERITY_CHOICES ,
    default =SEVERITY_MEDIUM ,db_index =True )
    description =models .TextField ()
    payload =models .JSONField (default =dict ,
    help_text ="Raw event data that triggered this risk event.")
    created_at =models .DateTimeField (auto_now_add =True )
    resolved =models .BooleanField (default =False ,db_index =True )

    class Meta :
        ordering =['-created_at']
        indexes =[
        models .Index (fields =['severity','resolved']),
        models .Index (fields =['tenant_id','severity']),
        models .Index (fields =['order_id']),
        ]

    def __str__ (self ):
        return f"RiskEvent[{self .rule_name }|{self .severity }] order={self .order_id }"
