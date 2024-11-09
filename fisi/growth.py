from enum import Enum

import numpy as np
import pandas as pd

from .constants import HISTORIC_GROWTH_RATES_PATH


class GrowthType(Enum):
    STOCKS = "S&P 500"
    BONDS = "US T. Bond (10-year)"
    INFLATION = "Inflation Rate"
    PORTFOLIO = "Stocks and Bonds Portfolio"


def get_growth_values(growth_type: GrowthType) -> np.ndarray:
    """
    Get historical growth rates for a given growth type.
    """
    historical_data = pd.read_csv(HISTORIC_GROWTH_RATES_PATH)
    return historical_data[growth_type.value].values


def sample_growth_rates(
    growth_type: GrowthType,
    number_of_simulations: int = 1_000,
    duration: int = 10,
    seed: int = 42,
):
    """
    Sample growth rates from a normal distribution, using the mean and standard deviation
    of historical data from the given growth type.
    """
    historical_growth_rates = get_growth_values(growth_type)
    mean_growth_rate = np.mean(historical_growth_rates)
    std_growth_rate = np.std(historical_growth_rates)
    rng = np.random.default_rng(seed=seed)
    return rng.normal(
        loc=mean_growth_rate,
        scale=std_growth_rate,
        size=(number_of_simulations, duration),
    )


def sample_from_historical_growth_rates(
    growth_type: GrowthType,
    number_of_simulations: int = 1_000,
    duration: int = 10,
    seed: int = 42,
):
    """
    Sample growth rates with replacement from historical data.
    """
    historical_growth_rates = get_growth_values(growth_type)
    rng = np.random.default_rng(seed=seed)
    return rng.choice(historical_growth_rates, size=(number_of_simulations, duration), replace=True)


def get_rebalancing_stock_allocations(age: int, duration: int) -> np.ndarray:
    """
    Get the stock allocation for rebalancing a portfolio every year,
    according to: stocks_allocation = (120 - age) / 100
    """
    years = np.arange(duration)
    ages = age + years
    return np.maximum(0, (120 - ages) / 100)
