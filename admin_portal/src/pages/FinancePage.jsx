import React, { useState, useEffect, useCallback, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { financeService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, Modal, EmptyState, LoadingSkeleton, Pagination } from '../components/common/UIComponents';
import { Wallet, ArrowUpRight, FileText, BookOpen, Layers, CheckCircle2, AlertCircle, Plus, Trash2 } from 'lucide-react';

export const FinancePage = () => {
  const { activeTenant } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('summary');
  const [ledger, setLedger] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [trialBalance, setTrialBalance] = useState(null);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [loading, setLoading] = useState(true);

  const accPagination = usePagination({ initialPageSize: 10 });
  const jePagination = usePagination({ initialPageSize: 10 });

  // Account Modal
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [accountForm, setAccountForm] = useState({
    account_code: '1010',
    account_name: 'Bank Cash',
    account_type: 'ASSET',
    normal_balance: 'DEBIT',
  });

  // Journal Entry Modal
  const [showJournalModal, setShowJournalModal] = useState(false);
  const [journalForm, setJournalForm] = useState({
    description: 'Manual adjustment entry',
    lines: [
      { account_code: '1010', entry_type: 'DEBIT', amount: 100 },
      { account_code: '4010', entry_type: 'CREDIT', amount: 100 },
    ],
  });

  const { showSuccess, showError } = useToast();

  const fetchFinanceData = useCallback(async () => {
    setLoading(true);
    try {
      const [ledgerRes, accRes, jeRes, tbRes] = await Promise.all([
        financeService.getLedgerSummary().catch(() => null),
        financeService.getAccounts({ page: accPagination.page, page_size: accPagination.pageSize }).catch(() => null),
        financeService.getJournalEntries({ page: jePagination.page, page_size: jePagination.pageSize }).catch(() => null),
        financeService.getTrialBalance().catch(() => null),
      ]);

      if (ledgerRes) setLedger(ledgerRes.data);
      if (accRes) {
        const accList = Array.isArray(accRes.data) ? accRes.data : accRes.data?.results || [];
        setAccounts(accList);
        accPagination.updatePaginationState(accRes.data);
      }
      if (jeRes) {
        const jeList = Array.isArray(jeRes.data) ? jeRes.data : jeRes.data?.results || [];
        setJournalEntries(jeList);
        jePagination.updatePaginationState(jeRes.data);
      }
      if (tbRes) setTrialBalance(tbRes.data);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [activeTenant, accPagination.page, accPagination.pageSize, jePagination.page, jePagination.pageSize]);

  useEffect(() => {
    fetchFinanceData();
  }, [fetchFinanceData]);

  const handleRequestPayout = async (e) => {
    e.preventDefault();
    try {
      await financeService.requestPayout({
        amount: payoutAmount,
        payout_method: 'POLAR_PAYOUT',
      });
      showSuccess('Payout journal entry posted & payout request submitted!');
      setPayoutAmount('');
      fetchFinanceData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    try {
      await financeService.createAccount(accountForm);
      showSuccess('Account created in Chart of Accounts!');
      setShowAccountModal(false);
      fetchFinanceData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleCreateJournalEntry = async (e) => {
    e.preventDefault();
    try {
      await financeService.createJournalEntry(journalForm);
      showSuccess('General Journal Entry posted successfully!');
      setShowJournalModal(false);
      fetchFinanceData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const addJournalLine = () => {
    setJournalForm({
      ...journalForm,
      lines: [...journalForm.lines, { account_code: '1010', entry_type: 'DEBIT', amount: 0 }],
    });
  };

  const removeJournalLine = (index) => {
    setJournalForm({
      ...journalForm,
      lines: journalForm.lines.filter((_, i) => i !== index),
    });
  };

  if (loading && activeTab === 'summary') {
    return (
      <div className="w-full p-6 md:p-8 space-y-6">
        <h1 className="text-3xl font-extrabold text-white">General Ledger & Accounting</h1>
        <LoadingSkeleton count={3} type="table" />
      </div>
    );
  }

  return (
    <div className="w-full pb-12">
      <ControlPanel
        title="Double-Entry General Ledger & Finance"
        subtitle="IAS/IFRS Accounting Standard"
        primaryAction={
          activeTab === 'accounts' ? {
            label: 'Add Account',
            icon: Plus,
            onClick: () => setShowAccountModal(true)
          } : activeTab === 'journal' ? {
            label: 'New Journal Entry',
            icon: Plus,
            onClick: () => setShowJournalModal(true)
          } : null
        }
        filterOptions={[
          { label: 'Financial Overview', value: 'summary' },
          { label: 'Chart of Accounts (COA)', value: 'accounts' },
          { label: 'General Journal Entries', value: 'journal' },
          { label: 'Trial Balance Ledger', value: 'trial' },
        ]}
        activeFilter={activeTab}
        onFilterChange={setActiveTab}
        onRefresh={fetchFinanceData}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Accounting Stage Navigation Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {[
            { key: 'summary', label: 'Financial Overview' },
            { key: 'accounts', label: 'Chart of Accounts' },
            { key: 'journal', label: 'General Journal' },
            { key: 'trial', label: 'Trial Balance' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === t.key ? 'bg-purple-600 text-white shadow' : 'bg-slate-900 text-slate-400 border border-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="app-card p-5 border-emerald-500/30">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Sales Revenue</div>
                <div className="text-2xl font-black text-emerald-400 mt-2">${ledger?.total_sales_revenue || '0.00'}</div>
              </div>

              <div className="app-card p-5 border-amber-500/30">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Platform Commission (5%)</div>
                <div className="text-2xl font-black text-amber-400 mt-2">${ledger?.platform_commission_fees || '0.00'}</div>
              </div>

              <div className="app-card p-5 border-cyan-500/30">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Available Payout Balance</div>
                <div className="text-2xl font-black text-cyan-400 mt-2">${ledger?.available_payout_balance || '0.00'}</div>
              </div>
            </div>

            <div className="app-card p-6 max-w-lg border-slate-800">
              <h3 className="text-sm font-extrabold text-white mb-3 uppercase tracking-wider flex items-center gap-2">
                <Wallet size={16} className="text-purple-400" /> Request Polar.sh Shop Payout
              </h3>
              <form onSubmit={handleRequestPayout} className="flex gap-3">
                <input
                  type="number"
                  step="0.01"
                  className="flex-1 app-input"
                  placeholder="Payout amount ($)"
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  required
                />
                <button type="submit" className="app-btn-primary">
                  Request Payout <ArrowUpRight size={14} />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Chart of Accounts Tab */}
        {activeTab === 'accounts' && (
          <div>
            {accounts.length === 0 ? (
              <EmptyState
                icon={Layers}
                title="No Accounts Found"
                description="No accounts exist for this tenant. Click 'Add Account' to create one."
              />
            ) : (
              <DataTable
                columns={[
                  { header: 'Code', accessor: 'account_code', render: (r) => <span className="font-mono font-bold text-[#00a09d]">{r.account_code}</span> },
                  { header: 'Account Name', accessor: 'account_name', render: (r) => <span className="font-bold text-white">{r.account_name}</span> },
                  { header: 'Category Type', accessor: 'account_type', render: (r) => <span className="px-2 py-0.5 rounded text-xs font-bold bg-[#7c7bad]/20 text-[#7c7bad] border border-[#7c7bad]/30 font-mono">{r.account_type}</span> },
                  { header: 'Normal Balance', accessor: 'normal_balance', render: (r) => <span className="text-xs font-semibold text-[#94a3b8]">{r.normal_balance}</span> },
                  { header: 'Current Ledger Balance', accessor: 'current_balance', render: (r) => <span className="font-extrabold text-[#48bb78] font-mono">${r.current_balance}</span> },
                ]}
                data={accounts}
                keyField="id"
                pagination={accPagination}
              />
            )}
          </div>
        )}


      {/* General Journal Tab */}
      {activeTab === 'journal' && (
        <div className="glass-panel p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">General Journal Transactions</h3>
            <button onClick={() => setShowJournalModal(true)} className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1">
              <Plus size={14} /> Post Journal Entry
            </button>
          </div>

          {journalEntries.length === 0 ? (
            <EmptyState icon={FileText} title="No Journal Entries" description="No general journal entries have been posted yet. Click 'Post Journal Entry' to record a transaction." />
          ) : (
            <>
              <div className="space-y-4">
                {journalEntries.map((entry) => (
                  <div key={entry.id} className="bg-slate-900/60 border border-white/10 rounded-xl p-5 space-y-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-mono text-xs text-indigo-400 font-bold">{entry.entry_number || `#${entry.id}`}</span>
                        <h4 className="font-bold text-white text-sm mt-0.5">{entry.description}</h4>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
                        {entry.status || 'POSTED'}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 rounded-lg p-3 border border-white/5">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="text-slate-500 border-b border-white/5 pb-2">
                            <th className="py-1 px-2">Account</th>
                            <th className="py-1 px-2">Entry Type</th>
                            <th className="py-1 px-2 text-right">Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(entry.lines || []).map((line, idx) => (
                            <tr key={idx} className="border-b border-white/[0.02] last:border-b-0">
                              <td className="py-1.5 px-2 font-semibold text-slate-200">
                                {line.account_code} - {line.account_name}
                              </td>
                              <td className="py-1.5 px-2">
                                <span className={`font-extrabold ${line.entry_type === 'DEBIT' ? 'text-cyan-400' : 'text-pink-400'}`}>
                                  {line.entry_type}
                                </span>
                              </td>
                              <td className="py-1.5 px-2 text-right font-mono font-bold text-white">${line.amount}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>

              <Pagination
                currentPage={jePagination.page}
                totalPages={jePagination.totalPages}
                totalItems={jePagination.totalItems}
                pageSize={jePagination.pageSize}
                onPageChange={jePagination.handlePageChange}
                onPageSizeChange={jePagination.handlePageSizeChange}
              />
            </>
          )}
        </div>
      )}

      {/* Trial Balance Tab */}
      {activeTab === 'trial' && (
        <div className="glass-panel p-6 space-y-6">
          <div className="flex justify-between items-center border-b border-white/10 pb-4">
            <h3 className="text-lg font-bold text-white">Trial Balance Verification</h3>
            {trialBalance && (
              <div className="flex items-center gap-2">
                {trialBalance.is_balanced ? (
                  <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    <CheckCircle2 size={16} /> Balanced (Total Debits = Total Credits)
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    <AlertCircle size={16} /> Unbalanced
                  </span>
                )}
              </div>
            )}
          </div>

          {!trialBalance || !trialBalance.accounts || trialBalance.accounts.length === 0 ? (
            <EmptyState icon={BookOpen} title="No Trial Balance Data" description="No financial account activity recorded for this tenant yet." />
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-xs font-bold text-slate-400 uppercase bg-white/5">
                  <th className="py-3 px-4">Account Code</th>
                  <th className="py-3 px-4">Account Name</th>
                  <th className="py-3 px-4 text-right">Total Debit ($)</th>
                  <th className="py-3 px-4 text-right">Total Credit ($)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {trialBalance.accounts.map((row, idx) => (
                  <tr key={idx}>
                    <td className="py-3 px-4 font-mono font-bold text-cyan-400">{row.account_code}</td>
                    <td className="py-3 px-4 text-slate-200">{row.account_name}</td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-100">${row.debit}</td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-100">${row.credit}</td>
                  </tr>
                ))}
                <tr className="bg-indigo-950/30 font-extrabold text-white">
                  <td colSpan="2" className="py-4 px-4 text-right">TOTALS</td>
                  <td className="py-4 px-4 text-right font-mono text-cyan-300">${trialBalance.total_debits}</td>
                  <td className="py-4 px-4 text-right font-mono text-pink-300">${trialBalance.total_credits}</td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      )}
      </div>

      {/* Account Modal */}
      <Modal isOpen={showAccountModal} onClose={() => setShowAccountModal(false)} title="Create Chart of Account">
        <form onSubmit={handleCreateAccount} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Account Code</label>
            <input type="text" value={accountForm.account_code} onChange={(e) => setAccountForm({ ...accountForm, account_code: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Account Name</label>
            <input type="text" value={accountForm.account_name} onChange={(e) => setAccountForm({ ...accountForm, account_name: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Category Type</label>
              <select value={accountForm.account_type} onChange={(e) => setAccountForm({ ...accountForm, account_type: e.target.value })} className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                <option value="ASSET">ASSET</option>
                <option value="LIABILITY">LIABILITY</option>
                <option value="EQUITY">EQUITY</option>
                <option value="REVENUE">REVENUE</option>
                <option value="EXPENSE">EXPENSE</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Normal Balance</label>
              <select value={accountForm.normal_balance} onChange={(e) => setAccountForm({ ...accountForm, normal_balance: e.target.value })} className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
                <option value="DEBIT">DEBIT</option>
                <option value="CREDIT">CREDIT</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setShowAccountModal(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">Cancel</button>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl">Save Account</button>
          </div>
        </form>
      </Modal>

      {/* Journal Entry Modal */}
      <Modal isOpen={showJournalModal} onClose={() => setShowJournalModal(false)} title="Post General Journal Entry">
        <form onSubmit={handleCreateJournalEntry} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Description / Memo</label>
            <input type="text" value={journalForm.description} onChange={(e) => setJournalForm({ ...journalForm, description: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-indigo-300 uppercase">Journal Lines</label>
              <button type="button" onClick={addJournalLine} className="text-xs text-indigo-400 hover:underline flex items-center gap-1">
                <Plus size={12} /> Add Line
              </button>
            </div>

            {journalForm.lines.map((line, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <select value={line.account_code} onChange={(e) => { const lines = [...journalForm.lines]; lines[idx].account_code = e.target.value; setJournalForm({ ...journalForm, lines }); }} className="flex-1 bg-slate-900/80 border border-white/10 rounded-xl px-3 py-2 text-xs text-white">
                  {accounts.map((a) => (
                    <option key={a.id} value={a.account_code}>{a.account_code} - {a.account_name}</option>
                  ))}
                </select>
                <select value={line.entry_type} onChange={(e) => { const lines = [...journalForm.lines]; lines[idx].entry_type = e.target.value; setJournalForm({ ...journalForm, lines }); }} className="w-28 bg-slate-900/80 border border-white/10 rounded-xl px-3 py-2 text-xs text-white">
                  <option value="DEBIT">DEBIT</option>
                  <option value="CREDIT">CREDIT</option>
                </select>
                <input type="number" step="0.01" value={line.amount} onChange={(e) => { const lines = [...journalForm.lines]; lines[idx].amount = parseFloat(e.target.value) || 0; setJournalForm({ ...journalForm, lines }); }} className="w-28 bg-slate-900/80 border border-white/10 rounded-xl px-3 py-2 text-xs text-white" />
                {journalForm.lines.length > 2 && (
                  <button type="button" onClick={() => removeJournalLine(idx)} className="text-rose-400 p-1"><Trash2 size={16} /></button>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setShowJournalModal(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">Cancel</button>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl">Post Entry</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
