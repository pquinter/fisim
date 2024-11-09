import numpy as np

from fisi.growth import (
    GrowthType,
    get_rebalancing_stock_allocations,
    sample_from_historical_growth_rates,
    sample_growth_rates,
)


def test_get_rebalancing_stock_allocations():
    age, duration = 30, 100
    allocations = get_rebalancing_stock_allocations(age, duration)
    assert allocations.shape == (duration,)
    assert np.all(allocations >= 0), "Allocations should be non-negative"
    assert np.all(allocations <= 1), "Allocations should be between 0 and 1"
    assert np.all(allocations[-1] == 0), "Allocations should be 0 at the end"
    assert np.all(np.diff(allocations) <= 0), "Allocations should decrease over time"
    assert allocations[0] == 0.9, "Allocations should be 0.9 at the start"


def test_sample_from_historical_growth_rates():
    growth_type = GrowthType.STOCKS
    number_of_simulations, duration, seed = 1000, 100, 42
    growth_rates = sample_from_historical_growth_rates(
        growth_type, number_of_simulations, duration, seed
    )
    assert growth_rates.shape == (number_of_simulations, duration)
    assert np.all(-1 <= growth_rates)
    assert np.isclose(np.mean(growth_rates), 0.12, atol=0.01)
    assert np.isclose(np.std(growth_rates), 0.19, atol=0.01)


def test_sample_growth_rates():
    growth_type = GrowthType.STOCKS
    number_of_simulations, duration, seed = 1000, 100, 42
    growth_rates = sample_growth_rates(growth_type, number_of_simulations, duration, seed)
    assert growth_rates.shape == (number_of_simulations, duration)
    assert np.all(-1 <= growth_rates)
    assert np.isclose(np.mean(growth_rates), 0.12, atol=0.01)
    assert np.isclose(np.std(growth_rates), 0.19, atol=0.01)
