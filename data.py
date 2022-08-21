from dataclasses import dataclass, asdict
import json
import pandas as pd
import os
from typing import List


@dataclass
class Envelope:
    id: int = None
    name: str = ""

    category: str = ""
    """Either 'Cost', 'Emergency', 'Save', 'Spend', or 'Internal'."""
    notes: str = ""
    """Description or various goals to keep track of for the envelope."""

    amount: float = 0.0
    """Amount of money in this envelope."""
    goal: float = None
    """The target, ideal amount, or required cost, depending on category."""
    capped: bool = False
    """Whether the goal is the maximum of this envelope or if it's okay to add more."""

    # fmt: "%Y-%m-%d"
    created: str = None
    """When the envelope was created."""
    removed: str = None
    """When the envelope was retired, None for if it's still active."""
    active: bool = True
    """Whether this envelope has been "deleted" or not."""


# @dataclass
# class Account:
#     name: str = ""
#     amount: float = 0.0
#     external: bool = True
#     """Allow recording accounts but that don't go into envelopes in any way (e.g. HSA, 401K etc)"""


class AccountingSystemData:
    def __init__(self, data_dir: str, sync_repo: str = None):
        self.data_dir: str = data_dir
        self.sync_repo: str = sync_repo

        self.expected_income: float = 0.0
        """How much per month I expect I will make"""

        self.target_max_spend: float = 0.0

        self.transfer_tags: List[str] = None

        self.path_system_data = os.path.join(data_dir, "system.json")
        self.path_envelopes = os.path.join(data_dir, "envelopes.json")
        self.path_accounts = os.path.join(data_dir, "accounts.csv")
        self.path_transfers = os.path.join(data_dir, "transfers.csv")
        self.path_envelope_history = os.path.join(data_dir, "envelope_history.csv")
        self.path_account_history = os.path.join(data_dir, "account_history.csv")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.envelopes: List[Envelope] = []
        self.accounts: pd.DataFrame = pd.DataFrame(columns=["name", "amount", "track"])
        self.envelope_history: pd.DataFrame = pd.DataFrame()
        self.account_history: pd.DataFrame = pd.DataFrame()
        self.transfers: pd.DataFrame = pd.DataFrame(
            columns=["envelope_from", "envelope_to", "amount", "type", "description", "date_entered", "date_processed", "accounted", "tags"])

    def get_envelope_by_name(self, name):
        for envelope in self.envelopes:
            if envelope.name == name:
                return envelope
        return None
    
    def max_envelope_id(self):
        max_id = -1
        for envelope in self.envelopes:
            if envelope.id > max_id:
                max_id = envelope.id

        return max_id

    def update_envelope_amounts(self):
        for envelope in self.envelopes:
            baseline = self.envelope_history.iloc[-1][envelope.name]
            baseline_date = self.envelope_history.iloc[-1].date
            
            froms = self.transfers[(self.transfers.envelope_from == envelope.id)
                    & ((self.transfers.date_entered > baseline_date) |
                        (self.transfers.date_processed > baseline_date))]
            tos = self.transfers[(self.transfers.envelope_to == envelope.id)
                    & ((self.transfers.date_entered > baseline_date) |
                        (self.transfers.date_processed > baseline_date))]
        

            computed_amount = baseline - froms.amount.sum() + tos.amount.sum()
            envelope.amount = computed_amount


    def load(self):
        self.load_system_data()
        self.load_account_history()
        self.load_accounts()
        self.load_envelope_history()
        self.load_envelopes()
        self.load_transfers()

    def save(self):
        self.save_system_data()
        self.save_account_history()
        self.save_accounts()
        self.save_envelope_history()
        self.save_envelopes()
        self.save_transfers()

    def load_system_data(self):
        if os.path.exists(self.path_system_data):
            with open(self.path_system_data, 'r') as infile:
                system_data = json.load(infile)
            self.sync_repo = system_data["sync_repo"]
            self.expected_income = system_data["expected_income"]
            self.target_max_spend = system_data["target_max_spend"]
            self.transfer_tags = system_data["transfer_tags"]

    def save_system_data(self):
        with open(self.path_system_data, 'w') as outfile:
            json.dump(dict(
                sync_repo=self.sync_repo,
                expected_income=self.expected_income,
                target_max_spend=self.target_max_spend,
                transfer_tags=self.transfer_tags
            ), outfile)

    def load_envelopes(self):
        if os.path.exists(self.path_envelopes):
            with open(self.path_envelopes, 'r') as infile:
                all_envelopes = json.load(infile)
                for envelope in all_envelopes:
                    self.envelopes.append(Envelope(**envelope))

    def load_accounts(self):
        if os.path.exists(self.path_transfers):
            self.accounts = pd.read_csv(self.path_accounts)

    def load_transfers(self):
        if os.path.exists(self.path_transfers):
            self.transfers = pd.read_csv(self.path_transfers)

    def load_envelope_history(self):
        if os.path.exists(self.path_envelope_history):
            self.envelope_history = pd.read_csv(self.path_envelope_history)

    def load_account_history(self):
        if os.path.exists(self.path_account_history):
            self.account_history = pd.read_csv(self.path_account_history)

    def save_envelopes(self):
        all_envelopes = [asdict(envelope) for envelope in self.envelopes]
        with open(self.path_envelopes, 'w') as outfile:
            json.dump(all_envelopes, outfile)

    def save_accounts(self):
        self.accounts.to_csv(self.path_accounts)

    def save_transfers(self):
        self.transfers.to_csv(self.path_transfers)

    def save_envelope_history(self):
        self.envelope_history.to_csv(self.path_envelope_history)

    def save_account_history(self):
        self.account_history.to_csv(self.path_account_history)
