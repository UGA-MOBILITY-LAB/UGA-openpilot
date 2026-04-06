from collections.abc import Callable

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem


class ManageToggleAction(base_list_view.ItemAction):
  def __init__(self, text: str | Callable[[], str], initial_state: bool = False,
               state_getter: Callable[[], bool] | None = None,
               enabled: bool | Callable[[], bool] = True,
               callback: Callable[[bool], None] | None = None):

    super().__init__(enabled=enabled)

    self._state_getter = state_getter
    self._button_action = base_list_view.ButtonAction(
      text=text,
      enabled=lambda: self.enabled and self._toggle_action.get_state(),
    )
    self._toggle_action = base_list_view.ToggleAction(
      initial_state=initial_state,
      enabled=enabled,
      callback=callback,
    )
    self._button_width = 0.0
    self._toggle_width = 0.0
    self._width_hint = 0.0
    self._refresh_layout_cache()

  def _refresh_layout_cache(self) -> None:
    self._button_width = self._button_action.get_width_hint()
    self._toggle_width = self._toggle_action.get_width_hint()
    self._width_hint = self._button_width + base_list_view.RIGHT_ITEM_PADDING + self._toggle_width

  def _render(self, rect: base_list_view.rl.Rectangle) -> bool:
    spacing = base_list_view.RIGHT_ITEM_PADDING

    button_rect = base_list_view.rl.Rectangle(rect.x, rect.y, self._button_width, rect.height)
    toggle_rect = base_list_view.rl.Rectangle(rect.x + self._button_width + spacing, rect.y, self._toggle_width, rect.height)

    pressed = bool(self._button_action.render(button_rect))
    self._toggle_action.render(toggle_rect)
    return pressed

  def get_state(self) -> bool:
    return self._toggle_action.get_state()

  def get_width_hint(self) -> float:
    return self._width_hint

  def set_state(self, state: bool) -> None:
    self._toggle_action.set_state(state)

  def set_touch_valid_callback(self, touch_callback: Callable[[], bool]) -> None:
    super().set_touch_valid_callback(touch_callback)
    self._button_action.set_touch_valid_callback(touch_callback)
    self._toggle_action.set_touch_valid_callback(touch_callback)

  def show_event(self) -> None:
    super().show_event()
    if self._state_getter is not None:
      self.set_state(self._state_getter())
    self._refresh_layout_cache()

def manage_toggle_item(title: str | Callable[[], str], button_text: str | Callable[[], str], description: str | Callable[[], str] | None = None,
                       initial_state: bool = False, state_getter: Callable[[], bool] | None = None,
                       toggle_callback: Callable[[bool], None] | None = None,
                       callback: Callable | None = None, icon: str = "", enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = ManageToggleAction(text=button_text, initial_state=initial_state, state_getter=state_getter, enabled=enabled, callback=toggle_callback)
  return FrogPilotListItem(title=title, description=description, action_item=action, callback=callback, icon=icon)
