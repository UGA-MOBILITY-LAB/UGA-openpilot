import threading

import requests

from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog
from openpilot.system.ui.widgets.keyboard import Keyboard
from openpilot.system.ui.widgets.option_dialog import MultiOptionDialog

from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget

PANEL_KEY = "gas_brake"

PRIMARY_PRIORITIES = ["Dashboard", "Map Data", "Highest", "Lowest"]
SECONDARY_PRIORITIES = ["None", "Dashboard", "Map Data"]

WEATHER_KEY_LENGTH = 32
WEATHER_TEST_LAT = 42.4293
WEATHER_TEST_LON = -83.9850


class FrogPilotGasAndBrakePanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()

    self._keyboard = Keyboard(max_text_size=WEATHER_KEY_LENGTH)

    subviews = {}

    subviews["advanced_longitudinal_tune"] = self._build_section_scroller(PANEL_KEY, "advanced_longitudinal_tune", subviews)

    subviews["conditional_experimental"] = self._build_section_scroller(PANEL_KEY, "conditional_experimental", subviews)

    subviews["curve_speed_controller"] = self._build_section_scroller(PANEL_KEY, "curve_speed_controller", subviews)

    subviews["custom_personalities"] = self._build_section_scroller(PANEL_KEY, "custom_personalities", subviews)
    subviews["traffic_personality_profile"] = self._build_section_scroller(PANEL_KEY, "traffic_personality", subviews)
    subviews["aggressive_personality_profile"] = self._build_section_scroller(PANEL_KEY, "aggressive_personality", subviews)
    subviews["standard_personality_profile"] = self._build_section_scroller(PANEL_KEY, "standard_personality", subviews)
    subviews["relaxed_personality_profile"] = self._build_section_scroller(PANEL_KEY, "relaxed_personality", subviews)

    subviews["longitudinal_tune"] = self._build_section_scroller(PANEL_KEY, "longitudinal_tune", subviews)

    subviews["quality_of_life"] = self._build_section_scroller(PANEL_KEY, "quality_of_life", subviews)
    subviews["weather_presets"] = self._build_section_scroller(PANEL_KEY, "weather_presets", subviews)
    subviews["low_visibility_offsets"] = self._build_section_scroller(PANEL_KEY, "weather_low_visibility", subviews)
    subviews["rain_offsets"] = self._build_section_scroller(PANEL_KEY, "weather_rain", subviews)
    subviews["rain_storm_offsets"] = self._build_section_scroller(PANEL_KEY, "weather_rain_storm", subviews)
    subviews["snow_offsets"] = self._build_section_scroller(PANEL_KEY, "weather_snow", subviews)

    subviews["speed_limit_controller"] = self._build_section_scroller(PANEL_KEY, "speed_limit_controller", subviews)
    subviews["slc_offsets"] = self._build_section_scroller(PANEL_KEY, "slc_offsets", subviews)
    subviews["slc_qol"] = self._build_section_scroller(PANEL_KEY, "slc_qol", subviews)
    subviews["slc_visuals"] = self._build_section_scroller(PANEL_KEY, "slc_visuals", subviews)

    root_scroller = self._build_section_scroller(PANEL_KEY, "root", subviews)

    self._initialize_views(root_scroller, *subviews.values())

  def _format_stock_title(self, title: str, stock_value: float) -> str:
    translated_title = tr(title)
    if stock_value == 0:
      return translated_title
    return f"{translated_title} ({tr('Default')}: {stock_value:.2f})"

  def _longitudinal_actuator_delay_title(self) -> str:
    return self._format_stock_title("Actuator Delay", self._toggles.longitudinal_actuator_delay)

  def _start_accel_title(self) -> str:
    return self._format_stock_title("Start Acceleration", self._toggles.start_accel)

  def _v_ego_starting_title(self) -> str:
    return self._format_stock_title("Start Speed", self._toggles.vEgoStarting)

  def _stop_accel_title(self) -> str:
    return self._format_stock_title("Stop Acceleration", self._toggles.stop_accel)

  def _stopping_decel_rate_title(self) -> str:
    return self._format_stock_title("Stopping Rate", self._toggles.stoppingDecelRate)

  def _v_ego_stopping_title(self) -> str:
    return self._format_stock_title("Stop Speed", self._toggles.vEgoStopping)

  def _handle_add_key(self, result: int) -> None:
    if result != 1:
      return

    new_key = self._keyboard.text.strip()
    if new_key:
      self.params.put("WeatherToken", new_key)

  def _handle_remove_key(self, result: int) -> None:
    if result != 1:
      return

    self.params.remove("WeatherToken")

  def _on_reset_curve_data(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to completely reset your curvature data?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._reset_curve_data(result))

  def _on_reset_traffic_personality(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to completely reset your settings for \"Traffic Mode\"?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._reset_params(result, (
      "TrafficFollow", "TrafficJerkAcceleration", "TrafficJerkDeceleration",
      "TrafficJerkDanger", "TrafficJerkSpeed", "TrafficJerkSpeedDecrease",
    )))

  def _on_reset_aggressive_personality(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to completely reset your settings for the \"Aggressive\" personality?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._reset_params(result, (
      "AggressiveFollow", "AggressiveJerkAcceleration", "AggressiveJerkDeceleration",
      "AggressiveJerkDanger", "AggressiveJerkSpeed", "AggressiveJerkSpeedDecrease",
    )))

  def _on_reset_standard_personality(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to completely reset your settings for the \"Standard\" personality?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._reset_params(result, (
      "StandardFollow", "StandardJerkAcceleration", "StandardJerkDeceleration",
      "StandardJerkDanger", "StandardJerkSpeed", "StandardJerkSpeedDecrease",
    )))

  def _on_reset_relaxed_personality(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to completely reset your settings for the \"Relaxed\" personality?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._reset_params(result, (
      "RelaxedFollow", "RelaxedJerkAcceleration", "RelaxedJerkDeceleration",
      "RelaxedJerkDanger", "RelaxedJerkSpeed", "RelaxedJerkSpeedDecrease",
    )))

  def _on_add(self) -> None:
    current_key = self.params.get("WeatherToken") or ""

    if current_key:
      dialog = ConfirmDialog(tr("Are you sure you want to remove your key?"), tr("Remove"))
      gui_app.set_modal_overlay(dialog, callback=lambda result: self._handle_remove_key(result))
    else:
      self._keyboard.reset(min_text_size=1)
      self._keyboard.set_title(tr("Enter your \"OpenWeatherMap\" key"), tr(f"Characters: 0/{WEATHER_KEY_LENGTH}"))
      self._keyboard.set_text(current_key)
      gui_app.set_modal_overlay(self._keyboard, callback=lambda result: self._handle_add_key(result))

  def _on_slc_priority(self) -> None:
    available = list(PRIMARY_PRIORITIES)
    if not self._toggles.has_dash_speed_limits:
      available = [p for p in available if p != "Dashboard"]

    dialog = MultiOptionDialog(tr("Select your primary priority"), available)
    gui_app.set_modal_overlay(dialog, callback=lambda result: self._handle_primary_priority(result, dialog))

  def _handle_primary_priority(self, result: int, dialog: MultiOptionDialog) -> None:
    if result != 1:
      return

    primary = dialog.selection
    self.params.put("SLCPriority1", primary)

    if primary in ("Highest", "Lowest"):
      self.params.put("SLCPriority2", "None")
      self.params.put("SLCPriority3", "None")
      return

    available = [p for p in SECONDARY_PRIORITIES if p != primary]
    if not self._toggles.has_dash_speed_limits:
      available = [p for p in available if p != "Dashboard"]

    if len(available) == 1 and available[0] == "None":
      self.params.put("SLCPriority2", "None")
      self.params.put("SLCPriority3", "None")
      return

    dialog2 = MultiOptionDialog(tr("Select your secondary priority"), available)
    gui_app.set_modal_overlay(dialog2, callback=lambda result: self._handle_secondary_priority(result, dialog2))

  def _handle_secondary_priority(self, result: int, dialog: MultiOptionDialog) -> None:
    if result != 1:
      return

    secondary = dialog.selection
    self.params.put("SLCPriority2", secondary)

    if secondary == "None":
      self.params.put("SLCPriority3", "None")

  def _on_test(self) -> None:
    key = (self.params.get("WeatherToken") or "").strip()
    if not key:
      gui_app.set_modal_overlay(alert_dialog(tr("No key set. Add a key first.")))
      return

    threading.Thread(target=self._test_weather_key, args=(key,), daemon=True).start()

  def _test_weather_key(self, key: str) -> None:
    url_3_0 = f"https://api.openweathermap.org/data/3.0/onecall?lat={WEATHER_TEST_LAT}&lon={WEATHER_TEST_LON}&exclude=current,minutely,hourly,daily,alerts&appid={key}"
    try:
      response = requests.get(url_3_0, timeout=10)
      if response.ok:
        gui_app.set_modal_overlay(alert_dialog(tr("Key is valid!")))
        return

      if response.status_code in (401, 403):
        url_2_5 = f"https://api.openweathermap.org/data/2.5/weather?lat={WEATHER_TEST_LAT}&lon={WEATHER_TEST_LON}&appid={key}"
        response_2_5 = requests.get(url_2_5, timeout=10)
        if response_2_5.ok:
          gui_app.set_modal_overlay(alert_dialog(tr("Your key is valid for version 2.5, but version 3.0 is highly recommended! Please subscribe to the \"One Call API 3.0\" plan!")))
        else:
          gui_app.set_modal_overlay(alert_dialog(tr(f"Invalid key! (Error: {response_2_5.status_code})")))
      else:
        gui_app.set_modal_overlay(alert_dialog(tr(f"An error occurred: {response.status_code}")))
    except requests.RequestException as e:
      gui_app.set_modal_overlay(alert_dialog(tr(f"Connection error: {e}")))

  def _reset_curve_data(self, result: int) -> None:
    if result != 1:
      return

    self.params.put("CalibratedLateralAcceleration", 2.00)
    self.params.remove("CalibrationProgress")
    self.params.remove("CurvatureData")

    if self._current_view is not None:
      self._current_view.show_event()

  def _reset_params(self, result: int, keys: tuple[str, ...]) -> None:
    if result != 1:
      return

    for key in keys:
      default = self.params.get_default_value(key)
      if default is not None:
        self.params.put(key, float(default))

    if self._current_view is not None:
      self._current_view.show_event()

  def _value_slc_priority(self) -> str:
    priorities = []
    for i in range(1, 3):
      priority = self.params.get(f"SLCPriority{i}") or ""
      if priority and priority != "None":
        priorities.append(priority)
    return ", ".join(priorities) if priorities else ""
