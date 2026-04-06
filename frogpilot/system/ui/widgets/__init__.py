from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import DialogResult, Widget
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.frogpilot.common import frogpilot_variables
from openpilot.frogpilot.system.ui.widgets.metadata_builder import MetadataWidgetBuilderMixin
from openpilot.frogpilot.ui.frogpilot_ui_state import frogpilot_ui_state
from openpilot.frogpilot.ui.layouts.settings.toggle_metadata import TOGGLE_METADATA


class FrogPilotWidget(MetadataWidgetBuilderMixin, Widget):
  def __init__(self):
    super().__init__()
    self.params = Params(return_defaults=True)

    self._current_view: Widget | None = None
    self._root_view: Widget | None = None

    self._multiple_button_items: dict[str, Widget] = {}

    self._view_stack: list[Widget] = []
    self._views: list[Widget] = []

    self._visibility_updaters: list[Callable[[], None]] = []

    self._toggles = frogpilot_ui_state.frogpilot_toggles
    self._tuning_levels = {key.decode(): self.params.get_tuning_level(key) for key in self.params.all_keys()}

    self._is_metric = self._toggles.is_metric
    self._tuning_level = frogpilot_variables.TUNING_LEVELS["ADVANCED"]

    self._refresh_state()

  VISIBILITY_STATES = {
    "_advanced_lateral_tune_visible": lambda self: any((
      self.VISIBILITY_STATES["_steer_delay_visible"](self),
      self.VISIBILITY_STATES["_steer_friction_visible"](self),
      self.VISIBILITY_STATES["_steer_kp_visible"](self),
      self.VISIBILITY_STATES["_steer_lat_accel_visible"](self),
      self.VISIBILITY_STATES["_steer_ratio_visible"](self),
      self.VISIBILITY_STATES["_force_auto_tune_visible"](self),
      self.VISIBILITY_STATES["_has_auto_tune"](self),
      self.VISIBILITY_STATES["_force_torque_visible"](self),
    )),
    "_ce_stop_lights_visible": lambda self: self._tuning_level < self._tuning_levels.get("CEModelStopTime", 0),
    "_force_auto_tune_visible": lambda self: not self._toggles.has_auto_tune and not self._toggles.is_angle_car and (self._toggles.is_torque_car or self._toggles.force_torque_controller or (self._toggles.has_nnff_log and self._toggles.nnff)),
    "_force_torque_visible": lambda self: not self._toggles.is_angle_car and not self._toggles.is_torque_car,
    "_has_auto_tune": lambda self: self._toggles.has_auto_tune,
    "_has_bsm_enabled": lambda self: self._toggles.has_bsm,
    "_has_dash_speed_limits": lambda self: self._toggles.has_dash_speed_limits,
    "_has_mapbox_key": lambda self: self._toggles.has_mapbox_key,
    "_has_model_randomizer": lambda self: self._toggles.model_randomizer,
    "_has_nnff_log": lambda self: self._toggles.has_nnff_log,
    "_has_openpilot_longitudinal": lambda self: self._toggles.openpilot_longitudinal,
    "_has_radar": lambda self: self._toggles.has_radar,
    "_has_sng": lambda self: self._toggles.has_sng,
    "_hide_speed_limit_visible": lambda self: self._toggles.openpilot_longitudinal and self._toggles.speed_limit_controller,
    "_higher_bitrate_visible": lambda self: self._toggles.no_uploads and not self._toggles.no_onroad_uploads,
    "_is_angle_car": lambda self: self._toggles.is_angle_car,
    "_is_gm": lambda self: self._toggles.car_make == "gm",
    "_is_hkg": lambda self: self._toggles.car_make == "hyundai",
    "_is_subaru": lambda self: self._toggles.car_make == "subaru",
    "_is_torque_car": lambda self: self._toggles.is_torque_car,
    "_is_toyota": lambda self: self._toggles.car_make == "toyota",
    "_is_toyota_non_tsk": lambda self: self._toggles.car_make == "toyota" and not self._toggles.is_tsk,
    "_lkas_allowed_for_aol": lambda self: self._toggles.lkas_allowed_for_aol,
    "_nnff_visible": lambda self: self._toggles.has_nnff_log and not self._toggles.is_angle_car,
    "_nnff_lite_visible": lambda self: not self._toggles.is_angle_car and not (self._toggles.has_nnff_log and self._toggles.nnff),
    "_no_model_randomizer": lambda self: not self._toggles.model_randomizer,
    "_no_pcm_cruise": lambda self: not self._toggles.pcm_cruise,
    "_no_sng": lambda self: not self._toggles.has_sng,
    "_nudgeless_visible": lambda self: self._toggles.lane_changes and self._toggles.nudgeless,
    "_show_speed_limits_visible": lambda self: not self._toggles.speed_limit_controller or not self._toggles.openpilot_longitudinal,
    "_slc_mapbox_visible": lambda self: self._toggles.show_speed_limits and (not self._toggles.speed_limit_controller or not self._toggles.openpilot_longitudinal) and self._toggles.has_mapbox_key,
    "_sng_hack_visible": lambda self: self._toggles.car_make == "toyota" and self._toggles.openpilot_longitudinal and not self._toggles.has_sng,
    "_start_accel_visible": lambda self: not self._toggles.human_acceleration,
    "_steer_delay_visible": lambda self: self._toggles.steer_actuator_delay != 0,
    "_steer_friction_visible": lambda self: self._toggles.default_friction != 0 and (self._toggles.force_auto_tune_off if self._toggles.has_auto_tune else not self._toggles.force_auto_tune) and (self._toggles.is_torque_car or self._toggles.force_torque_controller or (self._toggles.has_nnff_log and self._toggles.nnff)) and not (self._toggles.has_nnff_log and self._toggles.nnff),
    "_steer_kp_visible": lambda self: self._toggles.steer_kp != 0 and not self._toggles.is_angle_car and (self._toggles.is_torque_car or self._toggles.force_torque_controller or (self._toggles.has_nnff_log and self._toggles.nnff)),
    "_steer_lat_accel_visible": lambda self: self._toggles.lat_accel_factor != 0 and (self._toggles.force_auto_tune_off if self._toggles.has_auto_tune else not self._toggles.force_auto_tune) and (self._toggles.is_torque_car or self._toggles.force_torque_controller or (self._toggles.has_nnff_log and self._toggles.nnff)) and not (self._toggles.has_nnff_log and self._toggles.nnff),
    "_steer_ratio_visible": lambda self: self._toggles.steer_ratio != 0 and (self._toggles.force_auto_tune_off if self._toggles.has_auto_tune else not self._toggles.force_auto_tune),
    "_stopping_params_visible": lambda self: not self._toggles.frogsgomoo_tweak,
  }

  def _build_section_scroller(self, panel_key: str, section_key: str, subviews: dict) -> Scroller:
    panel = TOGGLE_METADATA[panel_key]
    return Scroller(
      [
        self._build_metadata_item(
          item_key,
          panel.items[item_key],
          subviews=subviews,
        )
        for item_key in panel.sections[section_key]
      ],
      line_separator=True,
      spacing=0,
    )

  def _bool_param_callback(self, key: str, reboot: bool = False, refreshes_visibility: bool = False) -> Callable[[bool], None]:
    def callback(state: bool) -> None:
      self.params.put_bool(key, state)
      if refreshes_visibility:
        frogpilot_ui_state.update_toggles()
        self.refresh_frogpilot_state()
      if reboot:
        self._reboot_prompt()

    return callback

  def _initialize_views(self, root_view: Widget, *nested_views: Widget) -> None:
    self._current_view = root_view
    self._root_view = root_view
    self._views = [root_view, *nested_views]

  def _perform_reboot(self, result: int) -> None:
    if not ui_state.engaged and result == DialogResult.CONFIRM:
      self.params.put_bool_nonblocking("DoReboot", True)

  def _reboot_prompt(self) -> None:
    if ui_state.engaged:
      gui_app.set_modal_overlay(alert_dialog(tr("Disengage to Reboot")))
      return

    dialog = ConfirmDialog(tr("Are you sure you want to reboot?"), tr("Reboot"))
    gui_app.set_modal_overlay(dialog, callback=self._perform_reboot)

  def _refresh_state(self) -> None:
    self._toggles = frogpilot_ui_state.frogpilot_toggles
    self._tuning_level = self._toggles.tuning_level

    new_is_metric = self._toggles.is_metric
    if self._is_metric != new_is_metric:
      self._is_metric = new_is_metric
      if self._current_view is not None:
        self._current_view.show_event()

  def _render(self, rect: rl.Rectangle) -> None:
    if self._current_view is not None:
      self._current_view.render(rect)

  def _set_multiple_button_selected(self, item_key: str, index: int) -> None:
    item = self._multiple_button_items.get(item_key)
    if item is not None:
      item.action_item.set_selected_button(index)

  def _set_tuning_level_visible(self, widget: Widget, key: str | None, visible=True) -> None:
    tuning_level = 0 if not key else self._tuning_levels.get(key, 0)

    def refresh() -> None:
      visible_value = visible() if callable(visible) else visible if visible is not None else True
      widget.set_visible(self._tuning_level >= tuning_level and visible_value)

    self._visibility_updaters.append(refresh)
    refresh()

  def _set_view(self, view: Widget) -> None:
    if view is self._current_view:
      return

    if self._current_view is not None:
      self._view_stack.append(self._current_view)
      self._current_view.hide_event()

    self._current_view = view
    self._current_view.show_event()

  def current_tuning_level(self) -> int:
    return self._tuning_level

  def handle_back(self) -> bool:
    if self._current_view is None or self._root_view is None or self._current_view is self._root_view:
      return False

    if isinstance(self._current_view, FrogPilotWidget) and self._current_view.handle_back():
      return True

    if self._view_stack:
      self._current_view.hide_event()
      self._current_view = self._view_stack.pop()
      self._current_view.show_event()

    return True

  def hide_event(self) -> None:
    super().hide_event()
    for view in self._views:
      view.hide_event()
    self.reset_navigation()

    # FrogPilot variables
    frogpilot_ui_state.update_toggles()

  def navigation_depth(self) -> int:
    depth = len(self._view_stack)
    if isinstance(self._current_view, FrogPilotWidget):
      depth += self._current_view.navigation_depth()
    return depth

  def refresh_frogpilot_state(self) -> None:
    self._refresh_state()
    for refresh in self._visibility_updaters:
      refresh()
    for view in self._views:
      if isinstance(view, FrogPilotWidget):
        view.refresh_frogpilot_state()

  def reset_navigation(self) -> None:
    if self._root_view is None:
      return

    for view in self._views:
      if isinstance(view, FrogPilotWidget):
        view.reset_navigation()

    self._view_stack.clear()
    self._current_view = self._root_view

  def show_event(self) -> None:
    super().show_event()
    self.refresh_frogpilot_state()
    if self._current_view is not None:
      self._current_view.show_event()
