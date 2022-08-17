from data import AccountingSystemData, Envelope
from datetime import datetime


class AccountingSystem:
    def __init__(self, data_dir="./data"):
        self.data: AccountingSystemData = AccountingSystemData(data_dir)
        
    def load(self):
        self.data.load()
        self.check_internal_envelopes()
        
    def check_internal_envelopes(self):
        if not self._check_for_envelope_category("Internal/Unaccounted"):
            self.data.envelopes.append(Envelope(name="Unaccounted", category="Internal/Unaccounted"))
        if not self._check_for_envelope_category("Internal/Expense Queue"):
            self.data.envelopes.append(Envelope(name="Expense Queue", category="Internal/Expense Queue"))
        if not self._check_for_envelope_category("Internal/Staged Expense"):
            self.data.envelopes.append(Envelope(name="Staged Expense", category="Internal/Staged Expense"))
            
    def grab_amounts(self):
        """Do we assume that expenses are already accounted for? I say yes. Should be reminder in frontend for this."""
        total = sys.data.accounts[sys.data.accounts.track].amount.sum()
        # TODO: determine how much "difference" to add to 
        
    def take_envelopes_snapshot(self):
        """Record a row of the current envelope amounts in the envelope_history."""
        # NOTE: that this is assuming we're keeping the column names up to date.
        for envelope in self.data.envelopes:
            if envelope.name not in self.data.envelope_history.columns:
                self.data.envelope_history[envelope.name] = None
        
        # Construct new row
        new_row = {}
        for envelope in self.data.envelopes:
            new_row[envelope.name] = envelope.amount
        # for column in self.data.envelope_history.columns:
        #     if column != "date":
        #         new_row[column] = self.data.get_envelope_by_name(column).amount
        new_row["date"] = datetime.now()
        print(new_row)
        self.data.envelope_history = self.data.envelope_history.append(new_row, ignore_index=True)
        
    def take_accounts_snapshot(self):
        """Record a row of the current envelope accounts in the envelope_history."""
        # NOTE: that this is assuming we're keeping the column names up to date.
        for index, row in self.data.accounts.iterrows():
            # NOTE: apparently "name" is a reserved name in pandas, row.name does not work.
            if row["name"] not in self.data.account_history.columns:
                self.data.account_history[row["name"]] = None
        
        # Construct new row
        new_row = {}
        for index, row in self.data.accounts.iterrows():
            new_row[row["name"]] = row.amount
        new_row["date"] = datetime.now()
        print(new_row)
        self.data.account_history = self.data.account_history.append(new_row, ignore_index=True)
        
    def _check_for_envelope_category(self, category):
        for envelope in self.data.envelopes:
            if envelope.category == category:
                return True
        return False

