class TestAsset:
    def test_initialization_with_cap_and_allocation(self, sample_cash):
        assert sample_cash.cap_value == 1_500

    def test_withdraw_less_than_available(self, sample_cash):
        withdrawn = sample_cash.withdraw(2024, 300)
        assert withdrawn == 300
        assert sample_cash.get_base_value(2024) == 700

    def test_withdraw_more_than_available(self, sample_cash):
        withdrawn = sample_cash.withdraw(2024, 2_000)
        assert withdrawn == 1_000
        assert sample_cash.get_base_value(2024) == 0

    def test_withdraw_from_year_with_zero_balance(self, sample_cash):
        sample_cash.update_base_value(2024, 0)
        withdrawn = sample_cash.withdraw(2024, 1_000)
        assert withdrawn == 0
        assert sample_cash.get_base_value(2024) == 0

    def test_deposit_less_than_cap(self, sample_cash):
        deposited = sample_cash.deposit(2024, 500)
        assert deposited == 500
        assert sample_cash.get_base_value(2024) == 1500

    def test_deposit_more_than_cap(self, sample_cash):
        deposited = sample_cash.deposit(2024, 1_000)
        assert deposited == 500
        assert sample_cash.get_base_value(2024) == 1_500

    def test_deposit_with_cap_deposit(self, sample_stock_with_cap_deposit):
        deposited = sample_stock_with_cap_deposit.deposit(2024, 1_000)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_value(2024) == 2_000

    def test_deposit_more_than_cap_deposit(self, sample_stock_with_cap_deposit):
        deposited = sample_stock_with_cap_deposit.deposit(2024, 2_000)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_value(2024) == 2_000
