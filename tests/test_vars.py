"""Interval variable testing."""
from rich import print

import energypylinear as epl
from energypylinear.interval_data import IntervalVars


def test_var() -> None:
    """
    for interval
        make some lp vars
        add them to vars

    get the evs objects for spill and non-spill
    """

    ds = epl.data_generation.generate_random_ev_input_data(
        48, n_chargers=3, charge_length=3, n_charge_events=12, seed=42
    )
    asset = epl.EVs(**ds)

    optimizer = epl.Optimizer()

    evs, evs_array, spill_evs, spill_evs_array = asset.one_interval(
        optimizer, i=0, freq=epl.Freq(60)
    )

    ivars = IntervalVars()

    #  this is how vars are used in the EVs asset

    #  in optimize method
    site = asset.site.one_interval(
        optimizer, asset.site.cfg, i=0, freq=epl.freq.Freq(60)
    )
    ivars.append(site)
    ivars.append(evs)
    ivars.append(evs_array)
    ivars.append(spill_evs_array)

    #  in constraints
    ivars.filter_site(0, asset.site.cfg.name)

    ivars.filter_objective_variables(epl.assets.evs.EVOneInterval, 0, asset.cfg.name)

    print("[red]assets[/red]")
    print(ivars.asset.keys())
    print(ivars.asset["evs"].keys())
    print(ivars.asset["evs"]["spill_evs_array"])
    ivars.filter_evs_array(True, 0, asset.cfg.name)
    ivars.filter_evs_array(False, 0, asset.cfg.name)

    ivars.filter_all_evs_array(True, asset.cfg.name)
    ivars.filter_all_evs_array(False, asset.cfg.name)
