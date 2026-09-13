import uuid
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from finance.models import Account, JournalEntry, JournalEntryLine, Invoice
from finance.accounting_utils import seed_default_accounts, post_journal_entry


def make_user_with_tenant():
    from django.contrib.auth.models import User
    user = User.objects.create_user(username=f'finuser_{uuid.uuid4().hex[:6]}', password='pass123')
    user.tenant_id = uuid.uuid4()
    return user, user.tenant_id


class AccountingUtilsTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def test_seed_default_accounts_creates_six_accounts(self):
        accounts = seed_default_accounts(self.tenant_id)
        self.assertEqual(len(accounts), 7)
        self.assertIn('1010', accounts)
        self.assertIn('4000', accounts)

    def test_seed_default_accounts_idempotent(self):
        seed_default_accounts(self.tenant_id)
        seed_default_accounts(self.tenant_id)
        self.assertEqual(Account.objects.filter(tenant_id=self.tenant_id).count(), 7)

    def test_post_journal_entry_balanced(self):
        accounts = seed_default_accounts(self.tenant_id)
        lines = [
            {'account': accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('100.00')},
            {'account': accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('100.00')},
        ]
        entry = post_journal_entry(self.tenant_id, 'Test Entry', lines)
        self.assertEqual(entry.status, 'POSTED')
        self.assertEqual(JournalEntryLine.objects.filter(journal_entry=entry).count(), 2)

    def test_post_journal_entry_unbalanced_raises(self):
        from django.core.exceptions import ValidationError
        accounts = seed_default_accounts(self.tenant_id)
        lines = [
            {'account': accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('100.00')},
            {'account': accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('90.00')},
        ]
        with self.assertRaises(ValidationError):
            post_journal_entry(self.tenant_id, 'Unbalanced', lines)


class AccountViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)

    def test_list_accounts_seeds_and_returns_for_tenant(self):
        response = self.client.get('/api/finance/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', response.data)
        self.assertEqual(len(results), 7)

    def test_list_accounts_no_tenant_returns_empty(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant_fin', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        response = self.client.get('/api/finance/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', response.data)
        self.assertEqual(len(results), 0)

    def test_unauthenticated_account_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/finance/accounts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JournalEntryViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)
        self.accounts = seed_default_accounts(self.tenant_id)

    def test_create_journal_entry_balanced(self):
        data = {
            'description': 'Sale',
            'reference_id': 'order-1',
            'lines': [
                {'account_id': str(self.accounts['1010'].id), 'entry_type': 'DEBIT', 'amount': '50.00'},
                {'account_id': str(self.accounts['4000'].id), 'entry_type': 'CREDIT', 'amount': '50.00'},
            ]
        }
        response = self.client.post('/api/finance/journal-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JournalEntry.objects.filter(tenant_id=self.tenant_id).count(), 1)

    def test_create_journal_entry_unbalanced_fails(self):
        data = {
            'description': 'Bad Entry',
            'lines': [
                {'account_id': str(self.accounts['1010'].id), 'entry_type': 'DEBIT', 'amount': '100.00'},
                {'account_id': str(self.accounts['4000'].id), 'entry_type': 'CREDIT', 'amount': '80.00'},
            ]
        }
        response = self.client.post('/api/finance/journal-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_journal_entries_scoped_to_tenant(self):
        lines = [
            {'account': self.accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('10.00')},
            {'account': self.accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('10.00')},
        ]
        post_journal_entry(self.tenant_id, 'Entry 1', lines)
        other_tenant = uuid.uuid4()
        other_accounts = seed_default_accounts(other_tenant)
        other_lines = [
            {'account': other_accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('20.00')},
            {'account': other_accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('20.00')},
        ]
        post_journal_entry(other_tenant, 'Entry 2', other_lines)
        response = self.client.get('/api/finance/journal-entries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_create_journal_entry_no_tenant_fails(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant_je', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        response = self.client.post('/api/finance/journal-entries/', {'description': 'X', 'lines': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TenantLedgerSummaryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)

    def test_ledger_summary_returns_correct_structure(self):
        response = self.client.get('/api/finance/ledger/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sales_revenue', response.data)
        self.assertIn('platform_commission_fees', response.data)
        self.assertIn('available_payout_balance', response.data)

    def test_ledger_summary_no_tenant_fails(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant_ledger', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        response = self.client.get('/api/finance/ledger/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ledger_summary_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/finance/ledger/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ledger_summary_reflects_journal_entries(self):
        accounts = seed_default_accounts(self.tenant_id)
        lines = [
            {'account': accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('100.00')},
            {'account': accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('95.00')},
            {'account': accounts['2000'], 'entry_type': 'CREDIT', 'amount': Decimal('5.00')},
        ]
        post_journal_entry(self.tenant_id, 'Payment', lines)
        response = self.client.get('/api/finance/ledger/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sales_revenue'], '95.00')


class RequestPayoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)
        self.accounts = seed_default_accounts(self.tenant_id)

    def test_payout_success(self):
        lines = [
            {'account': self.accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('200.00')},
            {'account': self.accounts['2000'], 'entry_type': 'CREDIT', 'amount': Decimal('200.00')},
        ]
        post_journal_entry(self.tenant_id, 'Fund payable', lines)
        response = self.client.post('/api/finance/payout/', {'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('journal_entry_id', response.data)

    def test_payout_zero_amount_fails(self):
        response = self.client.post('/api/finance/payout/', {'amount': '0.00'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payout_no_tenant_fails(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant_payout', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        response = self.client.post('/api/finance/payout/', {'amount': '10.00'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TrialBalanceViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)

    def test_trial_balance_balanced_after_entry(self):
        accounts = seed_default_accounts(self.tenant_id)
        lines = [
            {'account': accounts['1010'], 'entry_type': 'DEBIT', 'amount': Decimal('100.00')},
            {'account': accounts['4000'], 'entry_type': 'CREDIT', 'amount': Decimal('100.00')},
        ]
        post_journal_entry(self.tenant_id, 'Test', lines)
        response = self.client.get('/api/finance/trial-balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_balanced'])

    def test_trial_balance_no_tenant_fails(self):
        from django.contrib.auth.models import User
        user_no_tenant = User.objects.create_user(username='notenant_tb', password='pass123')
        self.client.force_authenticate(user=user_no_tenant)
        response = self.client.get('/api/finance/trial-balance/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trial_balance_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/finance/trial-balance/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InvoiceViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user, self.tenant_id = make_user_with_tenant()
        self.client.force_authenticate(user=self.user)

    def test_list_invoices_scoped_to_tenant(self):
        from datetime import date
        Invoice.objects.create(tenant_id=self.tenant_id, invoice_number='INV-001',
                               billing_period_start=date.today(), billing_period_end=date.today(),
                               total_amount='100.00', status='ISSUED')
        Invoice.objects.create(tenant_id=uuid.uuid4(), invoice_number='INV-002',
                               billing_period_start=date.today(), billing_period_end=date.today(),
                               total_amount='200.00', status='ISSUED')
        response = self.client.get('/api/finance/invoices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_unauthenticated_invoice_access_fails(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/finance/invoices/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
