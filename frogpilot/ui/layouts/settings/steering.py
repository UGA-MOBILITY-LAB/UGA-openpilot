from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog

from openpilot.frogpilot.common.frogpilot_variables import STEERING_TUNE_MAX_FACTOR, STEERING_TUNE_MIN_FACTOR
from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget

PANEL_KEY = "steering"

STEERING_RESET_PROMPTS = {
  "SteerDelay": tr_noop("Are you sure you want to reset the \"Actuator Delay\" to its default value?"),
  "SteerFriction": tr_noop("Are you sure you want to reset the \"Friction\" to its default value?"),
  "SteerKP": tr_noop("Are you sure you want to reset the \"Kp Factor\" to its default value?"),
  "SteerLatAccel": tr_noop("Are you sure you want to reset the \"Lateral Acceleration\" to its default value?"),
  "SteerRatio": tr_noop("Are you sure you want to reset the \"Steer Ratio\" to its default value?"),
}


class FrogPilotSteeringPanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()

    subviews = {}

    subviews["advanced_lateral_tune"] = self._build_section_scroller(PANEL_KEY, "advanced_lateral_tune", subviews)
    subviews["always_on_lateral"] = self._build_section_scroller(PANEL_KEY, "always_on_lateral", subviews)
    subviews["lane_changes"] = self._build_section_scroller(PANEL_KEY, "lane_changes", subviews)
    subviews["lateral_tuning"] = self._build_section_scroller(PANEL_KEY, "lateral_tuning", subviews)
    subviews["quality_of_life"] = self._build_section_scroller(PANEL_KEY, "quality_of_life", subviews)

    root_scroller = self._build_section_scroller(PANEL_KEY, "root", subviews)

    self._initialize_views(root_scroller, *subviews.values())

  def _format_stock_title(self, title: str, stock_value: float) -> str:
    translated_title = tr(title)
    if stock_value == 0:
      return translated_title
    return f"{translated_title} ({tr('Default')}: {stock_value:.2f})"

  def _steer_delay_title(self) -> str:
    return self._format_stock_title("Actuator Delay", self._toggles.steer_actuator_delay)

  def _steer_friction_title(self) -> str:
    return self._format_stock_title("Friction", self._toggles.default_friction)

  def _steer_kp_title(self) -> str:
    return self._format_stock_title("Kp Factor", self._toggles.steer_kp)

  def _steer_lat_accel_title(self) -> str:
    return self._format_stock_title("Lateral Acceleration", self._toggles.lat_accel_factor)

  def _steer_ratio_title(self) -> str:
    return self._format_stock_title("Steer Ratio", self._toggles.steer_ratio)

  def _steer_kp_min(self) -> float:
    return self._toggles.steer_kp * STEERING_TUNE_MIN_FACTOR

  def _steer_kp_max(self) -> float:
    return self._toggles.steer_kp * STEERING_TUNE_MAX_FACTOR

  def _steer_lat_accel_min(self) -> float:
    return self._toggles.lat_accel_factor * STEERING_TUNE_MIN_FACTOR

  def _steer_lat_accel_max(self) -> float:
    return self._toggles.lat_accel_factor * STEERING_TUNE_MAX_FACTOR

  def _steer_ratio_min(self) -> float:
    return self._toggles.steer_ratio * STEERING_TUNE_MIN_FACTOR

  def _steer_ratio_max(self) -> float:
    return self._toggles.steer_ratio * STEERING_TUNE_MAX_FACTOR

  def _reset_steering_param(self, param_key: str) -> None:
    prompt = STEERING_RESET_PROMPTS.get(param_key)
    if prompt is None:
      return

    dialog = ConfirmDialog(tr(prompt), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._apply_steering_param_reset(result, param_key))

  def _apply_steering_param_reset(self, result: int, param_key: str) -> None:
    if result != 1:
      return

    stock_value = {
      "SteerDelay": self._toggles.steer_actuator_delay,
      "SteerFriction": self._toggles.default_friction,
      "SteerKP": self._toggles.steer_kp,
      "SteerLatAccel": self._toggles.lat_accel_factor,
      "SteerRatio": self._toggles.steer_ratio,
    }.get(param_key)
    if stock_value is None:
      return

    self.params.put(param_key, float(stock_value))

    if self._current_view is not None:
      self._current_view.show_event()
