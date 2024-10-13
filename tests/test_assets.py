import numpy as np


class TestAsset:
    def test_initialization_with_cap_and_allocation(self, sample_cash):
        assert sample_cash.cap_value == 1_500

    def test_deposit_less_than_cap(self, sample_cash):
        to_deposit = np.array([500])
        deposited = sample_cash.deposit(2024, to_deposit)
        assert deposited == 500
        assert sample_cash.get_base_values(2024) == 1500

    def test_deposit_more_than_cap(self, sample_cash):
        to_deposit = np.array([1_000])
        deposited = sample_cash.deposit(2024, to_deposit)
        assert deposited == 500
        assert sample_cash.get_base_values(2024) == 1_500

    def test_deposit_with_cap_deposit(self, sample_stock_with_cap_deposit):
        to_deposit = np.array([1_000])
        deposited = sample_stock_with_cap_deposit.deposit(2024, to_deposit)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_values(2024) == 2_000

    def test_deposit_more_than_cap_deposit(self, sample_stock_with_cap_deposit):
        to_deposit = np.array([2_000])
        deposited = sample_stock_with_cap_deposit.deposit(2024, to_deposit)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_values(2024) == 2_000
