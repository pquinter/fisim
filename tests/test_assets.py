class TestAsset:
    def test_initialization_with_cap_and_allocation(self, sample_capped_asset):
        assert sample_capped_asset.cap_value == 1_500

    def test_withdraw_less_than_available(self, sample_capped_asset):
        withdrawn = sample_capped_asset.withdraw(2024, 300)
        assert withdrawn == 300
        assert sample_capped_asset.get_base_value(2024) == 700

    def test_withdraw_more_than_available(self, sample_capped_asset):
        withdrawn = sample_capped_asset.withdraw(2024, 2_000)
        assert withdrawn == 1_000
        assert sample_capped_asset.get_base_value(2024) == 0

    def test_withdraw_from_year_with_zero_balance(self, sample_capped_asset):
        sample_capped_asset.mutate_base_value(2024, 0)
        withdrawn = sample_capped_asset.withdraw(2024, 1_000)
        assert withdrawn == 0
        assert sample_capped_asset.get_base_value(2024) == 0

    def test_deposit_less_than_cap(self, sample_capped_asset):
        deposited = sample_capped_asset.deposit(2024, 500)
        assert deposited == 500
        assert sample_capped_asset.get_base_value(2024) == 1500

    def test_deposit_more_than_cap(self, sample_capped_asset):
        deposited = sample_capped_asset.deposit(2024, 1_000)
        assert deposited == 500
        assert sample_capped_asset.get_base_value(2024) == 1_500
