"""Valve asset for allowing heat to flow from high to low temperature.

This allows high temperature heat generated by either gas boilers or
CHP generators to be used for low temperature heat consumption.
"""
import typing

import pulp
import pydantic

import energypylinear as epl
from energypylinear.assets.asset import AssetOneInterval


class ValveConfig(pydantic.BaseModel):
    """Valve configuration."""

    name: str

    @pydantic.validator("name")
    def check_name(cls, name: str) -> str:
        """Ensure we can identify this asset correctly."""
        assert "valve" in name
        return name


class ValveOneInterval(AssetOneInterval):
    """Valve asset data for a single interval."""

    cfg: ValveConfig
    high_temperature_load_mwh: pulp.LpVariable
    low_temperature_generation_mwh: pulp.LpVariable


class Valve:
    def __init__(self, name: str = "valve"):
        self.cfg = ValveConfig(name=name)

    def __repr__(self) -> str:
        return f"<energypylinear.Valve>"

    def one_interval(
        self,
        optimizer: "epl.optimizer.Optimizer",
        i: int,
        freq: "epl.freq.Freq",
        flags: epl.flags.Flags = epl.flags.Flags(),
    ) -> ValveOneInterval:
        """Create Valve asset data for a single interval."""
        return ValveOneInterval(
            cfg=self.cfg,
            high_temperature_load_mwh=optimizer.continuous(
                f"{self.cfg.name}-high_temperature_load_mwh-{i}", low=0
            ),
            low_temperature_generation_mwh=optimizer.continuous(
                f"{self.cfg.name}-low_temperature_generation_mwh-{i}", low=0
            ),
        )

    def constrain_within_interval(
        self,
        optimizer: "epl.optimizer.Optimizer",
        vars: dict,
        freq: "epl.freq.Freq",
        flags: epl.flags.Flags = epl.flags.Flags(),
    ) -> None:
        """Constrain thermal balance across the valve."""
        valve = epl.utils.filter_assets(vars, "valve")[-1]
        optimizer.constrain(
            valve.high_temperature_load_mwh == valve.low_temperature_generation_mwh
        )

    def constrain_after_intervals(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        return
