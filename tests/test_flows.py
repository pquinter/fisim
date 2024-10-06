import matplotlib.pyplot as plt
import pytest

from spear.flows import InOrOutPerYear


class TestInOrOutPerYear:
    def test_initialization(self, sample_revenue):
        assert len(sample_revenue.base_value) == 10
        assert len(sample_revenue.multiplier) == 10

    def test_get_base_value(self, sample_revenue):
        assert sample_revenue.get_base_value(2024) == 1_000

    def test_get_multiplier(self, sample_revenue):
        assert sample_revenue.get_multiplier(2024) == 1

    def test_mutate_multiplier(self, sample_revenue):
        sample_revenue.mutate_multiplier(2025, 1.1)
        assert sample_revenue.get_multiplier(2025) == 1.1
        assert sample_revenue.get_multiplier(2024) == 1

    def test_mutate_base_value(self, sample_revenue):
        sample_revenue.mutate_base_value(2025, 100)
        assert sample_revenue.get_base_value(2025) == 100
        assert sample_revenue.get_base_value(2024) == 1_000

    def test_add_to_base_value(self, sample_revenue):
        sample_revenue.add_to_base_value(2024, 500)
        assert sample_revenue.get_base_value(2024) == 1_500
        assert sample_revenue.get_base_value(2025) == 1_000

    def test_getitem(self, sample_revenue):
        assert sample_revenue[2024] == 1_000
        assert sample_revenue[2027] == 1_000

    def test_invalid_multiplier(self):
        with pytest.raises(ValueError, match="Multiplier must be zero or positive."):
            InOrOutPerYear(name="Invalid Flow", initial_value=1000, multiplier=-0.5)

    def test_invalid_initial_value(self):
        with pytest.raises(ValueError, match="Base value must be zero or positive."):
            InOrOutPerYear(name="Invalid Flow", initial_value=-1000)

    @pytest.mark.parametrize(
        "year,expected_index",
        [
            (2024, 0),
            (2025, 1),
            (2030, 6),
        ],
    )
    def test_convert_year_to_index(self, sample_revenue, year, expected_index):
        assert sample_revenue._convert_year_to_index(year) == expected_index

    def test_plot(self, sample_revenue):
        ax = sample_revenue.plot()
        assert len(ax.get_lines()[0].get_xdata()) == sample_revenue.duration
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_plot_with_custom_duration(self, sample_revenue):
        ax = sample_revenue.plot(duration=5)
        assert len(ax.get_lines()[0].get_xdata()) == 5
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_grow_one_year(self, sample_revenue):
        initial_value = sample_revenue.get_base_value(2024)
        sample_revenue.grow(2024)

        # Check that the value for 2024 hasn't changed
        assert sample_revenue.get_base_value(2024) == initial_value

        # Check that the value for 2025 has grown by the multiplier
        expected_value = int(initial_value * sample_revenue.get_multiplier(2024))
        assert sample_revenue.get_base_value(2025) == expected_value

        # Check that subsequent years haven't changed
        assert sample_revenue.get_base_value(2026) == initial_value

    def test_grow_over_multiple_years(self, sample_revenue):
        initial_value = sample_revenue.get_base_value(2024)
        expected_value = initial_value

        for year in range(2024, 2027):
            assert sample_revenue.get_base_value(year) == expected_value
            sample_revenue.grow(year)
            expected_value = int(expected_value * sample_revenue.get_multiplier(year))

        # Check the final year after growth
        assert sample_revenue.get_base_value(2027) == expected_value

    def test_grow_at_end_of_duration(self, sample_revenue):
        last_year = sample_revenue.start_year + sample_revenue.duration - 1
        initial_value = sample_revenue.get_base_value(last_year)

        # Growing at the last year should not raise an error
        sample_revenue.grow(last_year)

        # The value for the last year should remain unchanged
        assert sample_revenue.get_base_value(last_year) == initial_value


class TestExpense:
    def test_expense_gets_inflated(self, sample_expense):
        for year in range(2024, 2027):
            sample_expense.grow(year)

        assert sample_expense.get_base_value(2024) == 1_000
        assert sample_expense.get_base_value(2025) == 1_020
        assert abs(sample_expense.get_base_value(2026) - int(1_000 * (1.02**2))) <= 1
        assert abs(sample_expense.get_base_value(2027) - int(1_000 * (1.02**3))) <= 1
