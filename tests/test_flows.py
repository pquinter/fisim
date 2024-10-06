import pytest

from spear.flows import InOrOutPerYear


class TestInOrOutPerYear:
    def test_initialization(self, sample_flow):
        assert len(sample_flow.base_value) == 10
        assert len(sample_flow.multiplier) == 10

    def test_get_base_value(self, sample_flow):
        assert sample_flow.get_base_value(2024) == 1_000
        assert sample_flow.get_base_value(2027) == 1_000

    def test_get_multiplier(self, sample_flow):
        assert sample_flow.get_multiplier(2024) == 1.05
        assert sample_flow.get_multiplier(2027) == 1.05

    def test_mutate_multiplier(self, sample_flow):
        sample_flow.mutate_multiplier(2025, 1.1)
        assert sample_flow.get_multiplier(2025) == 1.1
        assert sample_flow.get_multiplier(2024) == 1.05

    def test_mutate_base_value(self, sample_flow):
        sample_flow.mutate_base_value(2025, 100)
        assert sample_flow.get_base_value(2025) == 100
        assert sample_flow.get_base_value(2024) == 1_000

    def test_add_to_base_value(self, sample_flow):
        sample_flow.add_to_base_value(2024, 500)
        assert sample_flow.get_base_value(2024) == 1_500
        assert sample_flow.get_base_value(2025) == 1_000

    def test_getitem(self, sample_flow):
        assert sample_flow[2024] == 1_000
        assert sample_flow[2027] == 1000

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
    def test_convert_year_to_index(self, sample_flow, year, expected_index):
        assert sample_flow._convert_year_to_index(year) == expected_index

    def test_plot_with_custom_duration(self, sample_flow):
        ax = sample_flow.plot(duration=5)
        assert len(ax.get_lines()[0].get_xdata()) == 5

    def test_grow_one_year(self, sample_flow):
        initial_value = sample_flow.get_base_value(2024)
        sample_flow.grow(2024)

        # Check that the value for 2024 hasn't changed
        assert sample_flow.get_base_value(2024) == initial_value

        # Check that the value for 2025 has grown by the multiplier
        expected_value = int(initial_value * sample_flow.get_multiplier(2024))
        assert sample_flow.get_base_value(2025) == expected_value

        # Check that subsequent years haven't changed
        assert sample_flow.get_base_value(2026) == initial_value

    def test_grow_over_multiple_years(self, sample_flow):
        initial_value = sample_flow.get_base_value(2024)
        expected_value = initial_value

        for year in range(2024, 2027):
            assert sample_flow.get_base_value(year) == expected_value
            sample_flow.grow(year)
            expected_value = int(expected_value * sample_flow.get_multiplier(year))

        # Check the final year after growth
        assert sample_flow.get_base_value(2027) == expected_value

    def test_grow_at_end_of_duration(self, sample_flow):
        last_year = sample_flow.start_year + sample_flow.duration - 1
        initial_value = sample_flow.get_base_value(last_year)

        # Growing at the last year should not raise an error
        sample_flow.grow(last_year)

        # The value for the last year should remain unchanged
        assert sample_flow.get_base_value(last_year) == initial_value
