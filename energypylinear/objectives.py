"""Linear programming objective cost functions for price and carbon."""
import numpy as np
import pulp

import energypylinear as epl
from energypylinear.defaults import defaults


def filter_spill_evs(ivars, interval_data):
    spill_evs = ivars.filter_objective_variables(epl.evs.EVOneInterval)
    pkg = []
    for i, assets in enumerate(spill_evs):
        pkg.append([ev for ev in assets if ev.is_spill])
    spill_evs = pkg

    if len(spill_evs) == 0:
        spill_evs = [[epl.assets.asset.AssetOneInterval()] for i in interval_data.idx]
    return spill_evs


def price_objective(
    optimizer: "epl.Optimizer",
    ivars: "epl.interval_data.IntervalVars",
    interval_data: "epl.interval_data.IntervalData",
) -> pulp.LpAffineExpression:
    """
    Linear programming objective for cost minimization.  Equivilant to profit maximization.

    The objective is expressed as a linear combination of the costs for site import/export of power,
    spillage, charge for spillage EVs, gas consumption by generators and boilers.

    Inputs:
        optimizer: an instance of `epl.Optimizer` class.
        vars: a dictionary of linear programming variables in the optimization problem.
        interval_data: interaval data used in the simulation.

    Returns:
        A linear programming objective as an instance of `pulp.LpAffineExpression` class.
    """

    # sites = ivars.filter_all_sites()
    #  cheating here with the site name (the second `site`)
    sites = ivars.asset["site"]["site"]

    # spills = epl.utils.filter_all_assets(vars, "spill")
    spills = ivars.filter_objective_variables(epl.assets.spill.SpillOneInterval)

    spill_evs = filter_spill_evs(ivars, interval_data)
    generators = ivars.filter_objective_variables(epl.assets.chp.GeneratorOneInterval)
    boilers = ivars.filter_objective_variables(epl.assets.boiler.BoilerOneInterval)

    assert isinstance(interval_data.gas_prices, np.ndarray)
    assert isinstance(interval_data.electricity_prices, np.ndarray)

    obj = [
        sites[i].import_power_mwh * interval_data.electricity_prices[i]
        - sites[i].export_power_mwh * interval_data.electricity_prices[i]
        + [
            spill.electric_generation_mwh * defaults.spill_objective_penalty
            + spill.high_temperature_generation_mwh * defaults.spill_objective_penalty
            + spill.electric_load_mwh * defaults.spill_objective_penalty
            #  don't think I need this - this is dumping of HT heat - was in here - TODO test
            # + spill.high_temperature_load_mwh
            for spill in spills[i]
        ]
        + [
            spill_ev.electric_charge_mwh * defaults.spill_objective_penalty
            + spill_ev.electric_discharge_mwh * defaults.spill_objective_penalty
            for spill_ev in spill_evs[i]
        ]
        + [
            generator.gas_consumption_mwh * interval_data.gas_prices[i]
            for generator in generators[i]
        ]
        + [
            boiler.gas_consumption_mwh * interval_data.gas_prices[i]
            for boiler in boilers[i]
        ]
        for i in interval_data.idx
    ]
    return optimizer.sum(obj)


def carbon_objective(
    optimizer: "epl.Optimizer",
    ivars: "epl.interval_data.IntervalVars",
    interval_data: "epl.interval_data.IntervalData",
) -> pulp.LpAffineExpression:
    """
    Linear programming objective for carbon emission minimization.

    The objective is expressed as a linear combination of the costs for site import/export of power,
    spillage, charge for spillage EVs, gas consumption by generators and boilers.

    Inputs:
        optimizer: an instance of `epl.Optimizer` class.
        vars: a dictionary of linear programming variables in the optimization problem.
        interval_data: interaval data used in the simulation.

    Returns:
        A linear programming objective as an instance of `pulp.LpAffineExpression` class.
    """

    #  cheating here with the site name (the second `site`)
    sites = ivars.asset["site"]["site"]
    spills = ivars.filter_objective_variables(epl.assets.spill.SpillOneInterval)

    spill_evs = filter_spill_evs(ivars, interval_data)
    generators = ivars.filter_objective_variables(epl.assets.chp.GeneratorOneInterval)
    boilers = ivars.filter_objective_variables(epl.assets.boiler.BoilerOneInterval)

    assert isinstance(interval_data.electricity_carbon_intensities, np.ndarray)
    obj = [
        sites[i].import_power_mwh * interval_data.electricity_carbon_intensities[i]
        - sites[i].export_power_mwh * interval_data.electricity_carbon_intensities[i]
        + [
            spill.electric_generation_mwh * defaults.spill_objective_penalty
            + spill.high_temperature_generation_mwh * defaults.spill_objective_penalty
            + spill.electric_load_mwh * defaults.spill_objective_penalty
            + spill.electric_charge_mwh * defaults.spill_objective_penalty
            + spill.electric_discharge_mwh * defaults.spill_objective_penalty
            #  dumping heat has no penalty
            #  so high_temperature_load_mwh and low_temperature_load_mwh
            #  are not included here
            for spill in spills[i]
        ]
        + [
            spill.electric_generation_mwh * defaults.spill_objective_penalty
            + spill.high_temperature_generation_mwh * defaults.spill_objective_penalty
            + spill.electric_load_mwh * defaults.spill_objective_penalty
            + spill.electric_charge_mwh * defaults.spill_objective_penalty
            + spill.electric_discharge_mwh * defaults.spill_objective_penalty
            for spill in spill_evs[i]
        ]
        + [
            generator.gas_consumption_mwh * defaults.gas_carbon_intensity
            for generator in generators[i]
        ]
        + [
            boiler.gas_consumption_mwh * defaults.gas_carbon_intensity
            for boiler in boilers[i]
        ]
        for i in interval_data.idx
    ]
    return optimizer.sum(obj)


objectives = {"price": price_objective, "carbon": carbon_objective}
