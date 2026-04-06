from collections.abc import Callable

from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets.confirm_dialog import alert_dialog
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.frogpilot.common import frogpilot_variables
from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget
from openpilot.frogpilot.ui.frogpilot_ui_state import frogpilot_ui_state
from openpilot.frogpilot.ui.layouts.settings.alerts_and_sounds import FrogPilotSoundsPanel
from openpilot.frogpilot.ui.layouts.settings.driving_model import FrogPilotDrivingModelPanel
from openpilot.frogpilot.ui.layouts.settings.gas_and_brake import FrogPilotGasAndBrakePanel
from openpilot.frogpilot.ui.layouts.settings.map_data import FrogPilotMapDataPanel
from openpilot.frogpilot.ui.layouts.settings.steering import FrogPilotSteeringPanel
from openpilot.frogpilot.ui.layouts.settings.toggle_metadata import TOGGLE_METADATA, MetadataItem

DEVELOPER_WARNING = tr_noop(
  "WARNING: These settings are risky and can drastically change how openpilot drives. "
  "Only change if you fully understand what they do!"
)


class FrogPilotPanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()

    alerts_and_sounds_panel = FrogPilotSoundsPanel()
    driving_model_panel = FrogPilotDrivingModelPanel()
    gas_and_brake_panel = FrogPilotGasAndBrakePanel()
    map_data_panel = FrogPilotMapDataPanel()
    steering_panel = FrogPilotSteeringPanel()

    subviews = {
      "alerts_and_sounds": alerts_and_sounds_panel,
      "driving_model": driving_model_panel,
      "gas_brake": gas_and_brake_panel,
      "map_data": map_data_panel,
      "steering": steering_panel,
    }

    root_scroller = Scroller(
      [
        self._build_metadata_item(
          item_key,
          TOGGLE_METADATA["frogpilot_panel"].items[item_key],
          subviews=subviews,
        )
        for item_key in TOGGLE_METADATA["frogpilot_panel"].sections["root"]
      ],
      line_separator=True,
      spacing=0,
    )
    self._initialize_views(root_scroller, alerts_and_sounds_panel, driving_model_panel, gas_and_brake_panel, map_data_panel, steering_panel)

  def _button_visible(self, action: str):
    if action == "device_controls":
      return lambda: (self._tuning_level >= self._tuning_levels.get("DeviceManagement", 0) or self._tuning_level >= self._tuning_levels.get("ScreenManagement", 0))
    if action == "driving_model":
      return False
    if action == "gas_brake":
      return lambda: self._toggles.openpilot_longitudinal
    if action == "wheel_controls":
      return lambda: self._tuning_level >= self._tuning_levels.get("WheelControls", 0)
    return True

  def _multi_button_index(self, item_key: str, spec: MetadataItem) -> int:
    if item_key == "tuning_level":
      return self.current_tuning_level()
    return super()._multi_button_index(item_key, spec)

  def _multi_button_callback(self, item_key: str, spec: MetadataItem) -> Callable[[int], None]:
    if item_key == "tuning_level":
      return self._set_tuning_level
    return super()._multi_button_callback(item_key, spec)

  def _set_tuning_level(self, selected_index: int) -> None:
    self.params.put("TuningLevel", selected_index)
    self.params.put_bool("TuningLevelConfirmed", True)

    frogpilot_ui_state.update_toggles()

    self.refresh_frogpilot_state()

    if selected_index == frogpilot_variables.TUNING_LEVELS["DEVELOPER"]:
      gui_app.set_modal_overlay(alert_dialog(tr(DEVELOPER_WARNING)))

  def developer_panel_visible(self) -> bool:
    return self.current_tuning_level() >= frogpilot_variables.TUNING_LEVELS["DEVELOPER"]

  def show_event(self) -> None:
    super().show_event()
    self._set_multiple_button_selected("tuning_level", self.current_tuning_level())
