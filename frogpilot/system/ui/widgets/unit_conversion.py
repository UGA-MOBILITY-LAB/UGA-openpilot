from enum import Enum

from openpilot.common.constants import CV
from openpilot.common.params import Params


class UnitType(str, Enum):
  DISTANCE = "distance"
  LANE_WIDTH = "lane_width"
  SPEED = "speed"


UNIT_CONFIG = {
  UnitType.DISTANCE: {
    "imperial": {"unit": " feet", "max_scale": 10, "si_to_display": CV.METER_TO_FOOT, "value_map": {0: "Off", 1: "1 foot"}},
    "metric": {"unit": " meters", "max_scale": 3, "si_to_display": 1.0, "value_map": {0: "Off", 1: "1 meter"}},
  },
  UnitType.LANE_WIDTH: {
    "imperial": {"unit": " feet", "max_scale": 15, "si_to_display": CV.METER_TO_FOOT, "value_map": {0: "Off", 1: "1 foot"}},
    "metric": {"unit": " meters", "max_scale": 5, "si_to_display": 1.0, "value_map": {0: "Off", 1: "1 meter"}},
  },
  UnitType.SPEED: {
    "imperial": {"unit": " mph", "max_scale": 99, "si_to_display": CV.MS_TO_MPH},
    "metric": {"unit": " km/h", "max_scale": 150, "si_to_display": CV.MS_TO_KPH},
  },
}


def display_to_si(unit_type: UnitType, value: int | float) -> float:
  cfg = UNIT_CONFIG[unit_type]
  factor = cfg["metric"]["si_to_display"] if is_metric() else cfg["imperial"]["si_to_display"]
  return value / factor


def get_maximum(unit_type: UnitType) -> int:
  cfg = UNIT_CONFIG[unit_type]
  return cfg["metric"]["max_scale"] if is_metric() else cfg["imperial"]["max_scale"]


def get_minimum(unit_type: UnitType, base_min: int | float) -> int | float:
  if base_min < 0:
    return -get_maximum(unit_type)
  return base_min


def get_unit(unit_type: UnitType) -> str:
  cfg = UNIT_CONFIG[unit_type]
  return cfg["metric"]["unit"] if is_metric() else cfg["imperial"]["unit"]


def get_value_map(unit_type: UnitType, base_value_map: dict | None) -> dict | None:
  if base_value_map is None:
    return None
  cfg = UNIT_CONFIG[unit_type]
  system = "metric" if is_metric() else "imperial"
  return cfg[system].get("value_map", base_value_map)


def is_metric() -> bool:
  return Params(return_defaults=True).get_bool("IsMetric")


def si_to_display(unit_type: UnitType, value: int | float) -> float:
  cfg = UNIT_CONFIG[unit_type]
  factor = cfg["metric"]["si_to_display"] if is_metric() else cfg["imperial"]["si_to_display"]
  return value * factor
