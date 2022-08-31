from datetime import datetime

import pandas as pd

from data import AccountingSystemData, Envelope
from utils import df_append


class AccountingSystem:
    def __init__(self, data_dir: str = "./data"):
        self.data: AccountingSystemData = AccountingSystemData(data_dir)

    def load(self):
        self.data.load()
        self.check_internal_envelopes()

    def check_internal_envelopes(self):
        if not self._check_for_envelope_category("Internal/Unaccounted"):
            self.add_envelope(name="Unaccounted", category="Internal/Unaccounted")
        if not self._check_for_envelope_category("Internal/Expense Queue"):
            self.add_envelope(name="Expense Queue", category="Internal/Expense Queue")
        if not self._check_for_envelope_category("Internal/Staged Expense"):
            self.add_envelope(name="Staged Expense", category="Internal/Staged Expense")

    def add_envelope(self, name: str, category: str, notes: str = "") -> Envelope:
        env = Envelope(id=self.data.max_envelope_id() + 1,
                       name=name, category=category, notes=notes)
        self.data.envelopes.append(env)
        return env

    def get_distribution_plan(self, name: str) -> pd.DataFrame:
        dist_data = self.data.distribution_plans[name]

        # TODO: check rows to ensure there's one for every envelope 

        df = pd.DataFrame(dist_data)
        df["name"] = df.apply(lambda x:
                self.data.get_envelope_by_id(x.env_id).name, axis=1)
        df["goal"] = df.apply(lambda x:
                self.data.get_envelope_by_id(x.env_id).goal, axis=1)
        df.amount = df.amount.astype("float")
        df.percent = df.percent.astype("float")
        df["expected_increase"] = None

        df = df.reindex(columns=["env_id", "type", "name", "goal", "amount",
            "percent", "expected_increase"])

        return df

    def create_distribution_plan(self, name: str) -> pd.DataFrame:
        rows = []
        for envelope in self.data.envelopes:
            row = dict(
                env_id=envelope.id,
                type=envelope.category,
                amount=None,
                percent=None,
            )
            rows.append(row)

        self.data.distribution_plans[name] = rows
        return self.get_distribution_plan(name)

    def update_distribution_plan(self, name: str, df: pd.DataFrame):
        actual_df = df[["env_id", "type", "amount", "percent"]]
        json_str = actual_df.to_dict(orient="records")
        self.data.distribution_plans[name] = json_str

    def grab_accounts(self) -> float:
        """Do we assume that expenses are already accounted for? I say yes. Should be reminder in frontend for this.

        returns the diff added
        """
        accounts_total = self.data.accounts[self.data.accounts.track].amount.sum()
        envs = pd.DataFrame(self.data.envelopes)
        envelopes_total = envs[envs.category != "Internal/Expense Queue"].amount.sum()
        diff = accounts_total - envelopes_total

        if diff != 0.0:
            self.create_transfer(diff, "Income", None, self.data.get_envelope_by_name(
                "Unaccounted").id, tags=["accounts_grab"])
            self.data.update_envelope_amounts()  # TODO: should this always be done in create_transfer?
        return diff

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
        new_row["date"] = datetime.now()
        self.data.envelope_history = df_append(self.data.envelope_history, new_row)

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
        self.data.account_history = df_append(self.data.account_history, new_row)

    def create_transfer(self, amount: float = 0.0, type: str = "Transfer", envelope_from: int = None, envelope_to: int = None, description="", tags=None) -> int:
        """Returns id."""
        if tags is not None:
            for tag in tags:
                if self.data.transfer_tags is None:
                    self.data.transfer_tags = []
                if tag not in self.data.transfer_tags:
                    self.data.transfer_tags.append(tag)
        row = dict(amount=amount, type=type, envelope_from=envelope_from,
                   envelope_to=envelope_to, tags=tags, date_entered=datetime.now(), description=description)
        self.data.transfers = df_append(self.data.transfers, row)
        return self.data.transfers.iloc[-1].index

    def _check_for_envelope_category(self, category):
        """See if an envelope category exists, this is literally just to check for the internal envelopes."""
        for envelope in self.data.envelopes:
            if envelope.category == category:
                return True
        return False
