"""Extract results from a solved linear program to pd.DataFrame's."""
import collections

import numpy as np
import pandas as pd
import pandera as pa
import pydantic
from rich import print

import energypylinear as epl
from energypylinear.defaults import defaults
from energypylinear.flags import Flags
from energypylinear.interval_data import IntervalData
from energypylinear.optimizer import Optimizer

optimizer = Optimizer()


def check_electricity_balance(simulation: pd.DataFrame) -> pd.DataFrame:
    """Checks the electricity balance."""
    inp = (
        simulation["site-import_power_mwh"]
        + simulation["total-electric_generation_mwh"]
    )
    out = simulation["site-export_power_mwh"] + simulation["total-electric_load_mwh"]
    accumulation = (
        simulation["total-electric_discharge_mwh"]
        - simulation["total-electric_charge_mwh"]
    )
    balance = abs(inp + accumulation - out) < 1e-4
    data = pd.DataFrame(
        {
            "import": simulation["site-import_power_mwh"],
            "generation": simulation["total-electric_generation_mwh"],
            "export": simulation["site-export_power_mwh"],
            "load": simulation["total-electric_load_mwh"],
            "charge": simulation["total-electric_charge_mwh"],
            "discharge": simulation["total-electric_discharge_mwh"],
            "balance": balance,
            "loss": simulation["total-losses_mwh"],
            "spills": simulation["total-spills_mwh"],
        }
    )
    print("Electricity Balance")
    print(data)
    """
    debug = [
        "charger-0-electric_charge_mwh",
        "charger-1-electric_charge_mwh",
        "charger-spill-electric_charge_mwh",
    ]
    print(simulation[debug])
    """
    assert balance.all()
    return data


def check_high_temperature_heat_balance(simulation: pd.DataFrame) -> None:
    """Checks the high temperature heat balance."""
    inp = simulation[["total-high_temperature_generation_mwh"]].sum(axis=1)
    out = simulation[
        [
            "total-high_temperature_load_mwh",
            "load-high_temperature_load_mwh",
            #  valve naming - hmmmmmmmmmmmmmmmmmmmmmm
        ]
    ].sum(axis=1)
    balance = abs(inp - out) < 1e-4
    data = pd.DataFrame(
        {
            "in": inp,
            "out": out,
            "balance": balance,
        }
    )
    col = "valve-high_temperature_load_mwh"
    if col in simulation.columns:
        data["valve"] = simulation[col]
    print("High Temperature Heat Balance")
    print(data)
    assert balance.all()


def check_low_temperature_heat_balance(simulation: pd.DataFrame) -> None:
    """Checks the low temperature heat balance."""
    inp = simulation[
        [
            "total-low_temperature_generation_mwh",
        ]
    ].sum(axis=1)
    out = simulation[
        [
            "total-low_temperature_load_mwh",
            "load-low_temperature_load_mwh",
        ]
    ].sum(axis=1)
    balance = abs(inp - out) < 1e-4
    #  used for debug
    data = pd.DataFrame(
        {
            "in": inp,
            "out": out,
            "balance": balance,
        }
    )

    for name, col in [
        ("valve", "valve-low_temperature_generation_mwh"),
        ("load", "load-low_temperature_load_mwh"),
        ("assets-load", "total-low_temperature_load_mwh"),
        ("generator-load", "generator-low_temperature_load_mwh"),
        ("generator-generation", "generator-low_temperature_generation_mwh"),
    ]:
        if col in simulation.columns:
            data[name] = simulation[col]

    print("Low Temperature Heat Balance")
    print(data)
    # print(simulation[[c for c in simulation.columns if "low_temperature" in c]])
    assert balance.all()


def validate_results(interval_data: IntervalData, simulation: pd.DataFrame) -> None:
    """Check that our simulation results make sense.

    Args:
        interval_data: input interval data to the simulation.
        simulation: simulation results.
    """
    #  TODO
    check_electricity_balance(simulation)

    #  hmmmmmmmmmmmmmmmmmmm TODO move into above
    simulation[
        "load-high_temperature_load_mwh"
    ] = interval_data.high_temperature_load_mwh
    simulation["load-low_temperature_load_mwh"] = interval_data.low_temperature_load_mwh

    check_high_temperature_heat_balance(simulation)
    check_low_temperature_heat_balance(simulation)

    if interval_data.evs:

        #  TODO replace with a check on SOC

        # for charge_event_idx, charge_event_mwh in enumerate(
        #     interval_data.evs.charge_event_mwh
        # ):
        #     np.testing.assert_almost_equal(
        #         simulation[f"charge-event-{charge_event_idx}-total-charge_mwh"].sum(),
        #         charge_event_mwh,
        #         decimal=defaults.decimal_tolerance,
        #     )
        """
        want to check
        - only one charger -> one charge event each interval
        """
        cols = [
            c
            for c in simulation.columns
            if c.startswith("charger-")
            and c.endswith("-charge_binary")
            and "spill" not in c
        ]
        subset = simulation[cols]
        assert (subset <= 1).all().all()
