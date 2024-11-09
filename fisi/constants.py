from enum import Enum
from importlib import resources

# Federal income tax rates for 2023
FEDERAL_TAX_RATES = {
    10: 11000,
    12: 44725,
    22: 95375,
    24: 182100,
    32: 231250,
    35: 578125,
    37: float("inf"),
}

# State income tax rates for 2023
STATE_TAX_RATES = {
    "MA": {5: float("inf")},  # Massachusetts flat tax rate
    "CA": {
        1: 9325,
        2: 22107,
        4: 34892,
        6: 48435,
        8: 61214,
        9.3: 312686,
        10.3: 375221,
        11.3: 625369,
        12.3: float("inf"),
    },
    "PA": {3.07: float("inf")},  # Pennsylvania flat tax rate
    "MI": {4.25: float("inf")},  # Michigan flat tax rate
    "OH": {0: 25000, 2.765: 44250, 3.226: 88450, 3.688: 110650, 3.990: float("inf")},
}


# Tax brackets from 2024 for married filing jointly
LONG_TERM_CAPITAL_GAINS_TAX_BRACKETS = [(0, 0.0), (94_051, 0.15), (583_751, 0.20)]


class EarlyWithdrawal(Enum):
    AGE = 59.5
    PENALTY = 0.10


HISTORIC_GROWTH_RATES_PATH = resources.files("fisi.data").joinpath(
    "historic_annual_growth_rates.csv"
)
