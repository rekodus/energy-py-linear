A natural response when you get access to something someone else built is to wonder - does this work correctly?

This section will give you confidence in the implementation of the heat pump asset.

## Price Dispatch Behaviour

Let's optimize the heat pump in two intervals - the first with a high electricity price of `100` and the second with a low  electricity price of `-100`.

Our expectation is that the heat pump will not operate in the first interval, but will operate in the second interval:

```python
import pandas as pd
import energypylinear as epl

pd.set_option("display.max_columns", 4)
pd.set_option('display.width', 1000)

asset = epl.HeatPump(
    electric_power_mw=1.0,
    cop=2,
    gas_prices=20,
    electricity_prices=[100, -100],
    high_temperature_load_mwh=3.0,
    low_temperature_generation_mwh=4.0,
)
simulation = asset.optimize(verbose=False)
print(simulation.results[
    [
        "site-electricity_prices",
        "heat-pump-electric_load_mwh",
        "boiler-high_temperature_generation_mwh"
    ]
])
```

```
   site-electricity_prices  heat-pump-electric_load_mwh  boiler-high_temperature_generation_mwh
0                      100                          0.0                                     3.0
1                     -100                          1.0                                     1.0
```

For the first interval, with an electricity price of `100`, we see that:

- our heat pump has not operated (`heat-pump-electric_load_mwh=0`),
- our `3.0 MWh` of high temperature heat demand has been generated by the gas boiler.

For the second interval, with an electricity price of `-100`, we see that:

- our heat pump is operating at `1.0 MWe`, which means we expect `2.0 MWh` of high temperature heat,
- only `1.0 MWh` of high temperature heat demand has been generated by the gas boiler.

## Heat Balance Behaviour

### Without a Valve

Let's first optimize a heat pump without a high temperature to low temperature valve, which stops heat from flowing from high to low temperature.

We use a negative electricity price of `-100` for each interval, to force the heat pump to operate.

```python
import energypylinear as epl

asset = epl.HeatPump(
    electric_power_mw=1.0,
    cop=2,
    gas_prices=20,
    electricity_prices=[-100, -100, -100],
    high_temperature_load_mwh=[3.0, 0.5, 3.0],
    low_temperature_generation_mwh=[4.0, 4.0, 0.5],
    include_valve=False
)
simulation = asset.optimize(
    verbose=False,
)
print(simulation.results[
    [
        "site-high_temperature_load_mwh",
        "site-low_temperature_generation_mwh",
        "spill-low_temperature_load_mwh",
        "heat-pump-electric_load_mwh",
        "heat-pump-high_temperature_generation_mwh",
        "boiler-high_temperature_generation_mwh"
    ]
])
```

```
   site-high_temperature_load_mwh  site-low_temperature_generation_mwh  spill-low_temperature_load_mwh  heat-pump-electric_load_mwh  heat-pump-high_temperature_generation_mwh  boiler-high_temperature_generation_mwh
0                             3.0                                  4.0                            3.00                         1.00                                        2.0                                     1.0
1                             0.5                                  4.0                            3.75                         0.25                                        0.5                                     0.0
2                             3.0                                  0.5                            0.00                         0.50                                        1.0                                     2.0
```

In the first interval we are unconstrained in terms of heat - our heat pump runs at the full `1.0 MWe` load.

In the second interval we have a limited amount of high temperature heat load in the site, which constrains the heat pump.

In the third interval we have a limited amount of low temperature heat generation in the site, which again constrains how much the heat pump can run.

### With a Valve

Lets now optimize a heat pump with a high temperature to low temperature valve.

This allows heat to flow from high to low temperature, which means our boiler can generate high temperature heat that ends up as low temperature heat input into the heat pump.

This is a pretty bizarre situation, that is optimal because of our negative electricity price.

```python
import energypylinear as epl

asset = epl.HeatPump(
    electric_power_mw=1.0,
    cop=2,
    gas_prices=20,
    electricity_prices=[-100, -100, -100],
    high_temperature_load_mwh=[3.0, 0.5, 3.0],
    low_temperature_generation_mwh=[4.0, 4.0, 0.0],
    include_valve=True
)
simulation = asset.optimize(
    verbose=False,
)
print(simulation.results[
    [
        "site-high_temperature_load_mwh",
        "site-low_temperature_generation_mwh",
        "spill-low_temperature_load_mwh",
        "heat-pump-electric_load_mwh",
        "heat-pump-high_temperature_generation_mwh",
        "boiler-high_temperature_generation_mwh"
    ]
])
```

```
   site-high_temperature_load_mwh  site-low_temperature_generation_mwh  spill-low_temperature_load_mwh  heat-pump-electric_load_mwh  heat-pump-high_temperature_generation_mwh  boiler-high_temperature_generation_mwh
0                             3.0                                  4.0                             3.0                          1.0                                        2.0                                     1.0
1                             0.5                                  4.0                             4.5                          1.0                                        2.0                                     0.0
2                             3.0                                  0.0                             0.0                          1.0                                        2.0                                     2.0
```

We now see that our heat pump operates for all three intervals.  It is no longer starved for low temperature heat input, as the boiler can generate this heat.
