from django .urls import path ,include 
from rest_framework .routers import DefaultRouter 
from .views import (
AccountViewSet ,
JournalEntryViewSet ,
TenantLedgerSummaryView ,
RequestPayoutView ,
TrialBalanceView ,
InvoiceViewSet ,
RecordPaymentLedgerView ,
RiskDashboardView ,
CouponImpactReportView ,
)

router =DefaultRouter ()
router .register (r'accounts',AccountViewSet ,basename ='account')
router .register (r'journal-entries',JournalEntryViewSet ,basename ='journal-entry')
router .register (r'invoices',InvoiceViewSet ,basename ='invoice')

urlpatterns =[
path ('ledger/',TenantLedgerSummaryView .as_view (),name ='tenant_ledger_summary'),
path ('ledger/record-payment/',RecordPaymentLedgerView .as_view (),name ='record_payment_ledger'),
path ('payout/',RequestPayoutView .as_view (),name ='request_payout'),
path ('trial-balance/',TrialBalanceView .as_view (),name ='trial_balance'),

path ('risk/',RiskDashboardView .as_view (),name ='risk_dashboard'),
path ('risk/resolve/',RiskDashboardView .as_view (),name ='risk_resolve'),
path ('reports/coupon-impact/',CouponImpactReportView .as_view (),name ='coupon_impact_report'),
path ('',include (router .urls )),
]
