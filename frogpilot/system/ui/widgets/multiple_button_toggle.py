from collections.abc import Callable

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem


class MultipleButtonToggleAction(base_list_view.ItemAction):
  def __init__(self, buttons: list[str | Callable[[], str]], selected_index: int = 0,
               toggle_initial_state: bool = False,
               callback: Callable[[int], None] | None = None,
               toggle_callback: Callable[[bool], None] | None = None,
               button_states_getter: Callable[[], list[bool] | tuple[bool, ...]] | None = None,
               button_toggle_callback: Callable[[int], None] | None = None,
               state_getter: Callable[[], bool] | None = None,
               selected_index_getter: Callable[[], int] | None = None,
               button_width: int = base_list_view.BUTTON_WIDTH,
               enabled: bool | Callable[[], bool] = True):

    super().__init__(enabled=enabled)

    self._state_getter = state_getter
    self._selected_index_getter = selected_index_getter
    self._button_states_getter = button_states_getter
    self._button_toggle_callback = button_toggle_callback
    self._multiple_button_action = base_list_view.MultipleButtonAction(
      buttons=buttons,
      button_width=button_width,
      selected_index=selected_index,
      callback=callback,
    )
    self._multiple_button_action.set_enabled(lambda: self.enabled and self._toggle_action.get_state())
    self._toggle_action = base_list_view.ToggleAction(
      initial_state=toggle_initial_state,
      enabled=enabled,
      callback=toggle_callback,
    )
    self._font = base_list_view.gui_app.font(base_list_view.BUTTON_FONT_WEIGHT)

    padding = 20
    self._button_widths = []
    for btn in buttons:
      text = base_list_view._resolve_value(btn, "")
      text_size = base_list_view.measure_text_cached(self._font, text, 40)
      self._button_widths.append(max(button_width, int(text_size.x + padding * 2)))

    self._buttons_width = 0.0
    self._toggle_width = 0.0
    self._width_hint = 0.0
    self._refresh_layout_cache()

  def _refresh_layout_cache(self) -> None:
    spacing = base_list_view.RIGHT_ITEM_PADDING
    if self._button_states_getter is not None:
      self._buttons_width = sum(self._button_widths) + spacing * (len(self._button_widths) - 1) if self._button_widths else 0
    else:
      self._buttons_width = self._multiple_button_action.get_width_hint()
    self._toggle_width = self._toggle_action.get_width_hint()
    self._width_hint = self._buttons_width + spacing + self._toggle_width

  def _render(self, rect: base_list_view.rl.Rectangle) -> bool:
    spacing = base_list_view.RIGHT_ITEM_PADDING

    buttons_rect = base_list_view.rl.Rectangle(rect.x, rect.y, self._buttons_width, rect.height)
    toggle_rect = base_list_view.rl.Rectangle(rect.x + self._buttons_width + spacing, rect.y, self._toggle_width, rect.height)

    if self._button_states_getter is None:
      self._multiple_button_action.render(buttons_rect)
    else:
      button_y = buttons_rect.y + (buttons_rect.height - base_list_view.BUTTON_HEIGHT) / 2
      button_states = tuple(self._button_states_getter())

      button_x = buttons_rect.x
      toggle_active = self.enabled and self._toggle_action.get_state()

      for i, button_text in enumerate(self._multiple_button_action.buttons):
        bw = self._button_widths[i]
        button_rect = base_list_view.rl.Rectangle(button_x, button_y, bw, base_list_view.BUTTON_HEIGHT)

        mouse_pos = base_list_view.rl.get_mouse_position()
        is_pressed = base_list_view.rl.check_collision_point_rec(mouse_pos, button_rect) and self.enabled and self.is_pressed
        is_selected = i < len(button_states) and button_states[i]

        if is_selected and toggle_active:
          bg_color = base_list_view.rl.Color(51, 171, 76, 255)
        elif is_pressed and toggle_active:
          bg_color = base_list_view.rl.Color(74, 74, 74, 255)
        elif not toggle_active:
          bg_color = base_list_view.rl.Color(57, 57, 57, 150)
        else:
          bg_color = base_list_view.rl.Color(57, 57, 57, 255)

        base_list_view.rl.draw_rectangle_rounded(button_rect, 1.0, 20, bg_color)

        text = base_list_view._resolve_value(button_text, "")
        text_size = base_list_view.measure_text_cached(self._font, text, 40)
        text_x = button_x + (bw - text_size.x) / 2
        text_y = button_y + (base_list_view.BUTTON_HEIGHT - text_size.y) / 2
        text_color = base_list_view.rl.Color(228, 228, 228, 255) if toggle_active else base_list_view.rl.Color(150, 150, 150, 255)
        base_list_view.rl.draw_text_ex(self._font, text, base_list_view.rl.Vector2(text_x, text_y), 40, 0, text_color)

        button_x += bw + spacing

    self._toggle_action.render(toggle_rect)
    return False

  def _handle_mouse_release(self, mouse_pos: base_list_view.MousePos) -> None:
    if self._button_states_getter is None or self._button_toggle_callback is None:
      return

    if not self._toggle_action.get_state():
      return

    spacing = base_list_view.RIGHT_ITEM_PADDING
    button_y = self._rect.y + (self._rect.height - base_list_view.BUTTON_HEIGHT) / 2
    button_x = self._rect.x

    for i, _ in enumerate(self._multiple_button_action.buttons):
      bw = self._button_widths[i]
      button_rect = base_list_view.rl.Rectangle(button_x, button_y, bw, base_list_view.BUTTON_HEIGHT)
      if base_list_view.rl.check_collision_point_rec(mouse_pos, button_rect):
        self._button_toggle_callback(i)
        return
      button_x += bw + spacing

  def get_selected_button(self) -> int:
    return self._multiple_button_action.get_selected_button()

  def get_state(self) -> bool:
    return self._toggle_action.get_state()

  def get_width_hint(self) -> float:
    return self._width_hint

  def set_selected_button(self, index: int) -> None:
    self._multiple_button_action.set_selected_button(index)

  def set_state(self, state: bool) -> None:
    self._toggle_action.set_state(state)

  def set_touch_valid_callback(self, touch_callback: Callable[[], bool]) -> None:
    super().set_touch_valid_callback(touch_callback)
    self._multiple_button_action.set_touch_valid_callback(touch_callback)
    self._toggle_action.set_touch_valid_callback(touch_callback)

  def show_event(self) -> None:
    super().show_event()
    if self._selected_index_getter is not None:
      self.set_selected_button(self._selected_index_getter())
    if self._state_getter is not None:
      self.set_state(self._state_getter())
    self._refresh_layout_cache()

def multiple_button_toggle_item(title: str | Callable[[], str], description: str | Callable[[], str],
                                buttons: list[str | Callable[[], str]], selected_index: int = 0,
                                toggle_initial_state: bool = False,
                                callback: Callable[[int], None] | None = None,
                                toggle_callback: Callable[[bool], None] | None = None,
                                button_states_getter: Callable[[], list[bool] | tuple[bool, ...]] | None = None,
                                button_toggle_callback: Callable[[int], None] | None = None,
                                state_getter: Callable[[], bool] | None = None,
                                selected_index_getter: Callable[[], int] | None = None,
                                button_width: int = base_list_view.BUTTON_WIDTH,
                                icon: str = "", enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = MultipleButtonToggleAction(
    buttons=buttons,
    selected_index=selected_index,
    toggle_initial_state=toggle_initial_state,
    callback=callback,
    toggle_callback=toggle_callback,
    button_states_getter=button_states_getter,
    button_toggle_callback=button_toggle_callback,
    state_getter=state_getter,
    selected_index_getter=selected_index_getter,
    button_width=button_width,
    enabled=enabled,
  )
  return FrogPilotListItem(title=title, description=description, icon=icon, action_item=action)
