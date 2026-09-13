from rest_framework import serializers
from .models import Account, JournalEntry, JournalEntryLine, Invoice

class AccountSerializer(serializers.ModelSerializer):
    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['id', 'tenant_id', 'account_code', 'account_name', 'account_type', 'normal_balance', 'is_active', 'current_balance', 'created_at']

    def get_current_balance(self, obj):
        debits = sum(line.amount for line in obj.entry_lines.filter(entry_type='DEBIT'))
        credits = sum(line.amount for line in obj.entry_lines.filter(entry_type='CREDIT'))
        if obj.normal_balance == 'DEBIT':
            return str(debits - credits)
        return str(credits - debits)

class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.account_code', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = ['id', 'account', 'account_code', 'account_name', 'entry_type', 'amount']

class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ['id', 'tenant_id', 'entry_number', 'date', 'description', 'reference_id', 'status', 'lines', 'created_at']

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'tenant_id', 'customer_id', 'order_id', 'invoice_number',
            'billing_period_start', 'billing_period_end', 'due_date',
            'total_amount', 'status', 'items_summary', 'created_at'
        ]
