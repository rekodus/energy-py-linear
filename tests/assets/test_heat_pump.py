"""Tests for the Heat Pump asset."""
import hypothesis
import numpy as np
import pytest

import energypylinear as epl
from energypylinear.debug import debug_asset


def test_heat_pump_optimization_price() -> None:
    """Test optimization for price."""

    gas_price = 20.0
    #  TODO pass this into model
    blr_effy = 0.8
    cop = 3.0

    """
    cost to supply 1 MWh of high temp heat

    BAU = gas_prices / blr_effy

    heat pump = electricity_price / COP

    breakeven_electricity_price = gas_prices / blr_effy * COP
    """
    breakeven_electricity_price = gas_price / blr_effy * cop

    tolerance = 1
    asset = epl.HeatPump(
        electric_power_mw=1.0,
        cop=cop,
        electricity_prices=[
            -100,
            -50,
            50,
            100,
            breakeven_electricity_price + tolerance,
            breakeven_electricity_price - tolerance,
        ],
        gas_prices=gas_price,
        #  these are a bit hacky - will be expanded on in later tests
        #  the low temperature generation is a free source of low temperature heat
        #  which can be dumped or used by the heat pump to make high temperature heat
        high_temperature_load_mwh=100.0,
        low_temperature_generation_mwh=100.0,
    )
    simulation = asset.optimize()
    results = simulation.results

    #  when prices are low, the heat pump works
    #  when prices are high, the heat pump doesn't work
    np.testing.assert_array_equal(
        results["site-import_power_mwh"], [1.0, 1.0, 1.0, 0.0, 0.0, 1.0]
    )

    #  test COP using simulation totals
    np.testing.assert_equal(
        sum(results["heat-pump-high_temperature_generation_mwh"])
        / sum(results["heat-pump-electric_load_mwh"]),
        cop,
    )

    #  test COP by interval
    subset = results[results["heat-pump-high_temperature_generation_mwh"] > 0]
    np.testing.assert_equal(
        subset["heat-pump-high_temperature_generation_mwh"]
        / subset["heat-pump-electric_load_mwh"],
        np.full_like(subset.iloc[:, 0].values, cop),
    )

    #  test we don't consume more electricity than the heat pump size
    tol = 1e-7
    np.testing.assert_array_less(results["heat-pump-electric_load_mwh"], 1.0 + tol)

    #  test max sizes
    #  test we don't consume more electricity than the heat pump size
    np.testing.assert_array_less(
        results["heat-pump-high_temperature_generation_mwh"], 1.0 * cop + tol
    )

    #  test the energy balance across the heat pump
    #  the high temperature heat generated by the heat pump is the sum of the electricity and low temp energy
    np.testing.assert_array_equal(
        results["heat-pump-high_temperature_generation_mwh"]
        - results["heat-pump-electric_load_mwh"]
        - results["heat-pump-low_temperature_load_mwh"],
        0.0,
    )


def test_heat_pump_optimization_carbon() -> None:
    """Test optimization for carbon."""
    gas_price = 20
    #  TODO pass this into model
    blr_effy = 0.8
    cop = 3.0

    """
    carbon cost to supply 1 MWh of high temp heat

    BAU = gas_carbon_intensity / blr_effy
    heat pump = breakeven_carbon_intensity / COP
    breakeven_carbon_intensity = gas_carbon_intensity / blr_effy * COP
    """
    defaults = epl.defaults.Defaults()

    breakeven_carbon_intensity = defaults.gas_carbon_intensity / blr_effy * cop
    tolerance = 0.01

    asset = epl.HeatPump(
        electric_power_mw=1.0,
        cop=cop,
        electricity_prices=6 * [0.0],
        electricity_carbon_intensities=[
            -2.0,
            -0.5,
            1.0,
            2.0,
            breakeven_carbon_intensity + tolerance,
            breakeven_carbon_intensity - tolerance,
        ],
        gas_prices=gas_price,
        high_temperature_load_mwh=100,
        low_temperature_generation_mwh=100,
    )

    simulation = asset.optimize(objective="carbon")
    np.testing.assert_array_equal(
        simulation.results["site-import_power_mwh"], [1.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    )


def test_heat_pump_invalid_cop() -> None:
    """Test invalid COP raises error."""
    with pytest.raises(ValueError, match="COP must be 1 or above"):
        epl.HeatPump(electric_power_mw=2.0, cop=0.5)


def test_heat_pump_heat_balance() -> None:
    """Test heat balance around heat pump."""

    gas_price = 20
    cop = 4.0

    asset = epl.HeatPump(
        electric_power_mw=2.0,
        cop=cop,
        electricity_prices=[-100.0, -100.0, -100.0],
        gas_prices=gas_price,
        high_temperature_load_mwh=[1, 2.0, 4.0],
        low_temperature_generation_mwh=[100, 100, 100],
        include_valve=False,
    )

    #  limited by high temperature load
    simulation = asset.optimize(verbose=False)

    np.testing.assert_array_equal(
        simulation.results["site-import_power_mwh"], [0.25, 0.5, 1.0]
    )

    #  limited by low temperature generation
    asset = epl.HeatPump(
        electric_power_mw=2.0,
        cop=cop,
        electricity_prices=3 * [-100.0],
        gas_prices=gas_price,
        high_temperature_load_mwh=100,
        low_temperature_generation_mwh=[0.25, 0.5, 1.0],
        include_valve=False,
    )
    simulation = asset.optimize(
        verbose=False,
    )

    """
    lt + elect = ht
    ht = cop * elect

    lt + elect = cop * elect
    lt = elect * (cop - 1)
    elect = lt / (cop - 1)

    """
    np.testing.assert_allclose(
        simulation.results["site-import_power_mwh"],
        [0.25 / (cop - 1), 0.5 / (cop - 1), 1.0 / (cop - 1)],
    )


@hypothesis.settings(print_blob=True, deadline=None)
@hypothesis.given(
    cop=hypothesis.strategies.floats(min_value=1.0, max_value=50),
    idx_length=hypothesis.strategies.integers(min_value=10, max_value=24),
    gas_price=hypothesis.strategies.floats(min_value=10, max_value=50),
    prices_mu=hypothesis.strategies.floats(min_value=-1000, max_value=1000),
    prices_std=hypothesis.strategies.floats(min_value=0.1, max_value=1000),
    prices_offset=hypothesis.strategies.floats(min_value=-250, max_value=250),
    include_valve=hypothesis.strategies.booleans(),
)
def test_heat_pump_hypothesis(
    cop: float,
    idx_length: int,
    gas_price: float,
    prices_mu: float,
    prices_std: float,
    prices_offset: float,
    include_valve: bool,
) -> None:
    """Test optimization with hypothesis."""
    electricity_prices = (
        np.random.normal(prices_mu, prices_std, idx_length) + prices_offset
    )
    asset = epl.HeatPump(
        electric_power_mw=2.0,
        cop=cop,
        electricity_prices=electricity_prices,
        gas_prices=gas_price,
        high_temperature_load_mwh=100,
        low_temperature_generation_mwh=100,
        include_valve=include_valve,
    )
    simulation = asset.optimize(
        verbose=False,
    )

    dbg = debug_asset(simulation.results, asset.cfg.name, verbose=False)
    dbg["cop-check"] = (
        simulation.results["heat-pump-high_temperature_generation_mwh"]
        / simulation.results["heat-pump-electric_load_mwh"]
    )

    mask = dbg["heat-pump-electric_load_mwh"] == 0
    dbg.loc[mask, "cop-check"] = 0.0

    cop_check_rhs = np.full_like(dbg.iloc[:, 0].values, cop)
    cop_check_rhs[mask] = 0.0

    np.testing.assert_allclose(dbg["cop-check"], cop_check_rhs)
