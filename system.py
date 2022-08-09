from data import AccountingSystemData

class AccountingSystem:
    def __init__(self, data_dir="./data"):
        self.data: AccountingSystemData = AccountingSystemData(data_dir)
