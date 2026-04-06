from collections.abc import Callable

import pyray as rl

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.list_view import BUTTON_HEIGHT, ITEM_TEXT_FONT_SIZE, ITEM_TEXT_VALUE_COLOR, RIGHT_ITEM_PADDING

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem
from openpilot.frogpilot.system.ui.widgets.param_value import BUTTON_WIDTH, VALUE_COLOR, FrogPilotParamValueAction


class FrogPilotParamValueToggleAction(FrogPilotParamValueAction):
  def __init__(self, param_key: str, minimum: int | float, maximum: int | float,
               buttons: list[str | Callable[[], str]],
               button_states_getter: Callable[[], list[bool] | tuple[bool, ...]],
               button_toggle_callback: Callable[[int], None],
               width_values: tuple[int | float, ...] = (),
               value_formatter: Callable[[int | float], str] = str,
               step: int | float = 1,
               si_to_display=None,
               display_to_si=None,
               enabled: bool | Callable[[], bool] = True):

    super().__init__(
      param_key=param_key,
      minimum=minimum,
      maximum=maximum,
      width_values=width_values,
      value_formatter=value_formatter,
      step=step,
      si_to_display=si_to_display,
      display_to_si=display_to_si,
      enabled=enabled,
    )

    self._buttons = buttons
    self._button_states_getter = button_states_getter
    self._button_toggle_callback = button_toggle_callback
    self._font = gui_app.font(FontWeight.MEDIUM)

    self._button_widths = []
    padding = 20
    for btn in buttons:
      text = base_list_view._resolve_value(btn, "")
      text_size = base_list_view.measure_text_cached(self._font, text, 40)
      self._button_widths.append(max(BUTTON_WIDTH, int(text_size.x + padding * 2)))

    self._toggle_buttons_width = sum(self._button_widths)

  def get_width_hint(self) -> float:
    return self._toggle_buttons_width + RIGHT_ITEM_PADDING * len(self._button_widths) + super().get_width_hint()

  def _handle_mouse_release(self, mouse_pos: base_list_view.MousePos) -> None:
    button_y = self._rect.y + (self._rect.height - BUTTON_HEIGHT) / 2
    button_x = self._rect.x

    for index, _ in enumerate(self._buttons):
      bw = self._button_widths[index]
      button_rect = rl.Rectangle(button_x, button_y, bw, BUTTON_HEIGHT)
      if rl.check_collision_point_rec(mouse_pos, button_rect):
        self._button_toggle_callback(index)
        return
      button_x += bw + RIGHT_ITEM_PADDING

  def _render(self, rect: rl.Rectangle) -> bool:
    button_y = rect.y + (rect.height - BUTTON_HEIGHT) / 2
    button_x = rect.x
    button_states = tuple(self._button_states_getter())
    self._layout_value_width = self._compute_layout_value_width()

    for index, button_text in enumerate(self._buttons):
      bw = self._button_widths[index]
      button_rect = rl.Rectangle(button_x, button_y, bw, BUTTON_HEIGHT)

      mouse_pos = rl.get_mouse_position()
      is_pressed = rl.check_collision_point_rec(mouse_pos, button_rect) and self.enabled and self.is_pressed
      is_selected = index < len(button_states) and button_states[index]

      if is_selected:
        bg_color = rl.Color(51, 171, 76, 255)
      elif is_pressed:
        bg_color = rl.Color(74, 74, 74, 255)
      else:
        bg_color = rl.Color(57, 57, 57, 255)

      if not self.enabled:
        bg_color = rl.Color(bg_color.r, bg_color.g, bg_color.b, 150)

      rl.draw_rectangle_rounded(button_rect, 1.0, 20, bg_color)

      text = base_list_view._resolve_value(button_text, "")
      text_size = base_list_view.measure_text_cached(self._font, text, 40)
      text_x = button_x + (bw - text_size.x) / 2
      text_y = button_y + (BUTTON_HEIGHT - text_size.y) / 2
      text_color = rl.Color(228, 228, 228, 255) if self.enabled else rl.Color(150, 150, 150, 255)
      rl.draw_text_ex(self._font, text, rl.Vector2(text_x, text_y), 40, 0, text_color)

      button_x += bw + RIGHT_ITEM_PADDING

    value_rect = rl.Rectangle(button_x, rect.y, self._layout_value_width, rect.height)
    gui_label(
      value_rect,
      self._value_formatter(self._value),
      font_size=ITEM_TEXT_FONT_SIZE,
      color=VALUE_COLOR,
      alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
      alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE,
      elide_right=False,
    )
    self._render_step_buttons(button_x + self._layout_value_width + RIGHT_ITEM_PADDING, button_y)
    return False


def param_value_toggle_item(title, description, param_key: str,
                            minimum: int | float, maximum: int | float,
                            buttons: list[str | Callable[[], str]],
                            button_states_getter: Callable[[], list[bool] | tuple[bool, ...]],
                            button_toggle_callback: Callable[[int], None],
                            width_values: tuple[int | float, ...] = (),
                            value_formatter: Callable[[int | float], str] = str,
                            step: int | float = 1,
                            si_to_display=None,
                            display_to_si=None,
                            enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = FrogPilotParamValueToggleAction(
    param_key=param_key,
    minimum=minimum,
    maximum=maximum,
    width_values=width_values,
    buttons=buttons,
    button_states_getter=button_states_getter,
    button_toggle_callback=button_toggle_callback,
    value_formatter=value_formatter,
    step=step,
    si_to_display=si_to_display,
    display_to_si=display_to_si,
    enabled=enabled,
  )
  return FrogPilotListItem(title=title, description=description, action_item=action)
