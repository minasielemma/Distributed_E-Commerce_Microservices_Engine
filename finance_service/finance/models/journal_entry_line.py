import uuid
from django.db import models
from .journal_entry import JournalEntry
from .account import Account

class JournalEntryLine(models.Model):
    ENTRY_TYPE_CHOICES = (
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entry_lines')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['journal_entry', 'account']),
            models.Index(fields=['account', 'entry_type']),
        ]

    def __str__(self):
        return f"{self.entry_type} ${self.amount} -> Account {self.account.account_code}"
