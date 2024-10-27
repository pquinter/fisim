[![Tests](https://github.com/pquinter/financial-planning/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/pquinter/financial-planning/actions/workflows/ci.yml)

# Strategic Planning for Early Retirement (SPEAR)

Spear is a Python library for financial planning and modeling. It provides tools to simulate and analyze various financial scenarios over time.

## Installation

Clone the repository and install with pip:

```bash
git clone https://github.com/pquinter/financial-planning.git
cd financial-planning
pip install -e .
```

## Usage

View a quick demo in this [Jupyter notebook](notebooks/explore-financial-planning.ipynb).

### Specify revenues and expenses initial values and inflation rates

Revenues have a fixed value, and expenses grow with a fixed inflation rate.
The state is used to calculate taxes.

```python
from spear.flows import Expense, TaxableIncome

salary = TaxableIncome(name="Salary", initial_value=100_000, state="MA")

housing = Expense(name="Housing", initial_value=25_000, inflation_rate=0.02)
cost_of_living = Expense(name="Cost of Living", initial_value=20_000, inflation_rate=0.03)
```

### Specify your assets' initial values, growth rates, and caps

Assets can be specified with a fixed growth rate, and a cap on the total value, after which surplus money goes into assets without a cap; you can also specify a `cap_deposit` to limit how much money goes into a particular asset each year.

```python
from spear.assets import Asset, TaxableAsset
# Assets
cash = Asset(name="Cash", initial_value=50_000, growth_rate=0.01, cap_value=50_000)
```

Assets with growth type will grow with a rate sampled from historical data; the allocations must collectively equal 1.

```python
from spear.growth import GrowthType

bonds = TaxableAsset(
    name="Bonds",
    initial_value=50_000,
    allocation=0.1,
    growth_type=GrowthType.BONDS,
    seed=42
)
stocks = TaxableAsset(
    name="Stocks",
    initial_value=380_000,
    allocation=0.9,
    growth_type=GrowthType.STOCKS,
    seed=42
)
```

### Specify events acting on any of your revenues, expenses, or assets

Events include actions on methods of any of your financial objects; say you want to quit your job, after which your salary goes to 0, and you now have to pay for health insurance.

```python
health_insurance = Expense(name="Health Insurance", initial_value=0, inflation_rate=0.03)
quit_job = Event(
    name="Quit Job",
    year=2040,
    actions=[
        Action(
            target=salary,
            action="update_base_values",
            params={"new_base_values": 0, "duration": 100},
        ),
        Action(
            target=health_insurance,
            action="update_base_values",
            params={"new_base_values": 2_000, "duration": 100},
        ),
    ],
)
```

### Simulate your finances over a number of years

```python
from spear.model import FinancialModel

model = FinancialModel(
    revenues=[salary],
    expenses=[housing, cost_of_living, health_insurance],
    assets=[cash, bonds, stocks],
    events=[quit_job],
    duration=60, # years
    number_of_simulations=1_000,
)
model.run()
```

And plot the results

```python
ax = model.plot_all();
```
