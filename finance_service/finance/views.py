from decimal import Decimal 
from rest_framework import generics ,permissions ,status 
from rest_framework .response import Response 
from common.permissions import IsPlatformAdmin, _is_platform_admin
from rest_framework .views import APIView 
from rest_framework .decorators import action 
from common .viewsets import FullBaseViewSet 
from common .pagination import StandardPageNumberPagination 
from .models import Account ,JournalEntry ,JournalEntryLine ,Invoice ,FinancialRiskEvent 
from .serializers import AccountSerializer ,JournalEntrySerializer ,InvoiceSerializer 
from .accounting_utils import seed_default_accounts ,post_journal_entry ,record_payment_ledger_and_invoice 

def get_tenant_id (request ):
    user =getattr (request ,'user',None )
    if not user or not user .is_authenticated :
        return None
    token_tenant_id =getattr (user ,'tenant_id',None )
    if token_tenant_id and str (token_tenant_id ).lower ()not in ['none','null','']:
        return token_tenant_id 
    if _is_platform_admin (user ):
        header_tenant =request .headers .get ('X-Tenant-ID')or request .headers .get ('HTTP_X_TENANT_ID')or request .META .get ('HTTP_X_TENANT_ID')
        if header_tenant :
            return header_tenant 
    return None 


class AccountViewSet (FullBaseViewSet ):
    permission_classes =(permissions .IsAuthenticated ,)
    serializer_class =AccountSerializer 
    queryset =Account .objects .all ()

    def get_queryset (self ):
        tenant_id =get_tenant_id (self .request )
        if tenant_id :
            seed_default_accounts (tenant_id )
            return Account .objects .filter (tenant_id =tenant_id ).prefetch_related ('entry_lines').order_by('-id')
        return Account .objects .none ()

class JournalEntryViewSet (FullBaseViewSet ):
    permission_classes =(permissions .IsAuthenticated ,)
    serializer_class =JournalEntrySerializer 
    queryset =JournalEntry .objects .prefetch_related ('lines__account').all ()

    def get_queryset (self ):
        tenant_id =get_tenant_id (self .request )
        if tenant_id :
            return JournalEntry .objects .filter (tenant_id =tenant_id ).prefetch_related ('lines__account').order_by('-created_at')
        return JournalEntry .objects .none ()

    def create (self ,request ,*args ,**kwargs ):
        tenant_id =get_tenant_id (request )
        if not tenant_id :
            return Response ({'detail':'Tenant context required'},status =status .HTTP_400_BAD_REQUEST )

        description =request .data .get ('description','')
        reference_id =request .data .get ('reference_id','')
        raw_lines =request .data .get ('lines',[])

        lines_data =[]
        for line in raw_lines :
            account =Account .objects .get (id =line ['account_id'])if 'account_id'in line else Account .objects .get (tenant_id =tenant_id ,account_code =line ['account_code'])
            lines_data .append ({
            'account':account ,
            'entry_type':line ['entry_type'],
            'amount':line ['amount']
            })

        try :
            entry =post_journal_entry (tenant_id ,description ,lines_data ,reference_id )
            serializer =self .get_serializer (entry )
            return Response (serializer .data ,status =status .HTTP_201_CREATED )
        except Exception as e :
            return Response ({'detail':str (e )},status =status .HTTP_400_BAD_REQUEST )

class TenantLedgerSummaryView (APIView ):
    permission_classes =(permissions .IsAuthenticated ,)

    def get (self ,request ):
        tenant_id =get_tenant_id (request )
        if not tenant_id :
            return Response ({'detail':'Tenant context required'},status =status .HTTP_400_BAD_REQUEST )

        seed_default_accounts (tenant_id )
        accounts =Account .objects .filter (tenant_id =tenant_id ).prefetch_related ('entry_lines')

        revenue_acc =accounts .filter (account_code ='4000').first ()
        comm_acc =accounts .filter (account_code ='2000').first ()or accounts .filter (account_code ='5000').first ()
        cash_acc =accounts .filter (account_code ='1010').first ()

        total_sales =Decimal ('0.00')
        if revenue_acc :
            credits =sum (l .amount for l in revenue_acc .entry_lines .filter (entry_type ='CREDIT'))
            debits =sum (l .amount for l in revenue_acc .entry_lines .filter (entry_type ='DEBIT'))
            total_sales =credits -debits 

        total_comm =Decimal ('0.00')
        if comm_acc :
            credits =sum (l .amount for l in comm_acc .entry_lines .filter (entry_type ='CREDIT'))
            debits =sum (l .amount for l in comm_acc .entry_lines .filter (entry_type ='DEBIT'))
            total_comm =credits -debits 

        cash_bal =Decimal ('0.00')
        if cash_acc :
            debits =sum (l .amount for l in cash_acc .entry_lines .filter (entry_type ='DEBIT'))
            credits =sum (l .amount for l in cash_acc .entry_lines .filter (entry_type ='CREDIT'))
            cash_bal =debits -credits 

        return Response ({
        'tenant_id':str (tenant_id ),
        'total_sales_revenue':str (total_sales ),
        'platform_commission_fees':str (total_comm ),
        'available_payout_balance':str (total_sales )
        })

class RequestPayoutView (APIView ):
    permission_classes =(permissions .IsAuthenticated ,)

    def post (self ,request ):
        user_tenant_id = getattr(request.user, 'tenant_id', None)
        tenant_id = user_tenant_id or get_tenant_id(request)
        if not tenant_id:
            return Response({'detail': 'Tenant context required'}, status=status.HTTP_400_BAD_REQUEST)
        if not _is_platform_admin(request.user) and str(user_tenant_id) != str(tenant_id):
            return Response({'detail': 'Permission denied: cannot request payout for another tenant'}, status=status.HTTP_403_FORBIDDEN)

        amount =Decimal (str (request .data .get ('amount','0.00')))
        if amount <=Decimal ('0.00'):
            return Response ({'detail':'Invalid payout amount'},status =status .HTTP_400_BAD_REQUEST )

        accounts =seed_default_accounts (tenant_id )
        cash_acc =accounts ['1010']
        payable_acc =accounts ['2000']

        lines_data =[
        {'account':payable_acc ,'entry_type':'DEBIT','amount':amount },
        {'account':cash_acc ,'entry_type':'CREDIT','amount':amount }
        ]

        entry =post_journal_entry (tenant_id ,f"Shop Payout via Polar ({request .data .get ('payout_method','POLAR')})",lines_data )
        return Response ({'status':'Payout processed','journal_entry_id':str (entry .id )},status =status .HTTP_201_CREATED )

class TrialBalanceView (APIView ):
    permission_classes =(permissions .IsAuthenticated ,)

    def get (self ,request ):
        tenant_id =get_tenant_id (request )
        if not tenant_id :
            return Response ({'detail':'Tenant context required'},status =status .HTTP_400_BAD_REQUEST )

        seed_default_accounts (tenant_id )
        accounts =Account .objects .filter (tenant_id =tenant_id ).prefetch_related ('entry_lines')
        report =[]
        total_debits =Decimal ('0.00')
        total_credits =Decimal ('0.00')

        for acc in accounts :
            debit_sum =sum (l .amount for l in acc .entry_lines .filter (entry_type ='DEBIT'))
            credit_sum =sum (l .amount for l in acc .entry_lines .filter (entry_type ='CREDIT'))
            total_debits +=debit_sum 
            total_credits +=credit_sum 
            report .append ({
            'account_code':acc .account_code ,
            'account_name':acc .account_name ,
            'account_type':acc .account_type ,
            'debit':str (debit_sum ),
            'credit':str (credit_sum )
            })

        return Response ({
        'accounts':report ,
        'total_debits':str (total_debits ),
        'total_credits':str (total_credits ),
        'is_balanced':total_debits ==total_credits 
        })

class RecordPaymentLedgerView (APIView ):
    permission_classes =(permissions .IsAuthenticated ,)

    def post (self ,request ):
        order_id =request .data .get ('order_id')
        customer_id =request .data .get ('customer_id')or getattr (request .user ,'id',None )
        service_token = request.META.get('HTTP_X_SERVICE_TOKEN') or request.headers.get('X-Service-Token')
        if service_token:
            tenant_id = request.data.get('tenant_id') or getattr(request.user, 'tenant_id', None)
        else:
            tenant_id = getattr(request.user, 'tenant_id', None) or request.data.get('tenant_id')
        total_amount =request .data .get ('total_amount')or request .data .get ('amount')
        items_summary =request .data .get ('items',[])
        discount_code =request .data .get ('discount_code')
        discount_amount =request .data .get ('discount_amount','0.00')

        if not order_id or not total_amount :
            return Response ({'detail':'order_id and total_amount are required'},status =status .HTTP_400_BAD_REQUEST )

        try :
            entry ,invoice ,ledger_entry =record_payment_ledger_and_invoice (
            order_id =order_id ,
            customer_id =customer_id ,
            tenant_id =tenant_id ,
            total_amount =total_amount ,
            items_summary =items_summary ,
            discount_code =discount_code ,
            discount_amount =discount_amount ,
            )
            return Response ({
            'status':'Payment ledger and invoice recorded',
            'journal_entry_id':str (entry .id )if entry else None ,
            'invoice':InvoiceSerializer (invoice ).data if invoice else None ,
            'ledger_entry_id':str (ledger_entry .id )if ledger_entry else None ,
            },status =status .HTTP_201_CREATED )
        except Exception as e :
            return Response ({'detail':str (e )},status =status .HTTP_400_BAD_REQUEST )


class RiskDashboardView (APIView ):
    """List FinancialRiskEvents for the tenant, filterable by severity/resolved."""
    permission_classes =(permissions .IsAuthenticated ,)

    def get (self ,request ):
        qs =FinancialRiskEvent .objects .all ()

        tenant_id = get_tenant_id(request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        elif not _is_platform_admin(request.user):
            return Response({'detail': 'Tenant context required'}, status=status.HTTP_400_BAD_REQUEST)

        severity =request .query_params .get ('severity')
        if severity :
            qs =qs .filter (severity =severity .upper ())

        resolved =request .query_params .get ('resolved')
        if resolved is not None :
            qs =qs .filter (resolved =resolved .lower ()=='true')

        order_id =request .query_params .get ('order_id')
        if order_id :
            qs =qs .filter (order_id =order_id )

        qs = qs.order_by('-created_at')
        paginator = StandardPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        events = page if page is not None else qs
        data = [{
            'id': str(e.id),
            'order_id': str(e.order_id) if e.order_id else None,
            'rule_name': e.rule_name,
            'severity': e.severity,
            'description': e.description,
            'resolved': e.resolved,
            'created_at': e.created_at.isoformat(),
        } for e in events]
        if page is not None:
            return paginator.get_paginated_response(data)
        return Response({'count': len(data), 'results': data})

    def patch (self ,request ,pk =None ):
        """Mark a risk event as resolved."""
        event_id =request .data .get ('id')or pk 
        if not event_id :
            return Response ({'error':'id required'},status =status .HTTP_400_BAD_REQUEST )
        try :
            evt =FinancialRiskEvent .objects .get (pk =event_id )
        except FinancialRiskEvent .DoesNotExist :
            return Response ({'error':'Not found'},status =status .HTTP_404_NOT_FOUND )
        evt .resolved =True 
        evt .save (update_fields =['resolved'])
        return Response ({'status':'resolved','id':str (evt .id )})


class CouponImpactReportView (APIView ):
    """Aggregated financial impact of coupon usage per tenant."""
    permission_classes =(permissions .IsAuthenticated ,)

    def get (self ,request ):
        from django .db .models import Sum ,Count ,Avg 
        from .models import JournalEntry ,JournalEntryLine 

        tenant_id =get_tenant_id (request )
        if not tenant_id and not _is_platform_admin(request.user):
            return Response({'detail': 'Tenant context required'}, status=status.HTTP_400_BAD_REQUEST)


        disc_entries =JournalEntry .objects .filter (
        reference_id__startswith ='DISC-'
        )
        if tenant_id :
            disc_entries =disc_entries .filter (tenant_id =tenant_id )

        total_entries =disc_entries .count ()
        total_discount =JournalEntryLine .objects .filter (
        journal_entry__in =disc_entries ,
        entry_type ='DEBIT',
        ).aggregate (total =Sum ('amount'))['total']or Decimal ('0.00')


        risk_qs =FinancialRiskEvent .objects .all ()
        if tenant_id :
            risk_qs =risk_qs .filter (tenant_id =tenant_id )
        risk_summary =risk_qs .values ('severity').annotate (count =Count ('id')).order_by ('severity')

        return Response ({
        'tenant_id':str (tenant_id )if tenant_id else 'all',
        'total_coupon_orders':total_entries ,
        'total_discount_given':str (total_discount ),
        'risk_events_by_severity':list (risk_summary ),
        })

class InvoiceViewSet (FullBaseViewSet ):
    permission_classes =(permissions .IsAuthenticated ,)
    serializer_class =InvoiceSerializer 
    queryset =Invoice .objects .all ()

    def get_queryset(self):
        qs = Invoice.objects.all()
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        is_super = _is_platform_admin(user)

        cust_id_param = self.request.query_params.get('customer_id')
        if is_super:
            if cust_id_param:
                return qs.filter(customer_id=cust_id_param).order_by('-created_at')
            return qs.order_by('-created_at')
        elif tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
            if cust_id_param:
                qs = qs.filter(customer_id=cust_id_param)
            return qs.order_by('-created_at')
        else:
            return qs.filter(customer_id=user.id).order_by('-created_at')


