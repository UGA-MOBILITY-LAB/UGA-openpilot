from collections.abc import Callable

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.system.ui.lib.application import gui_app

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem

BUTTON_PADDING = 20


class FrogPilotMultipleButtonAction(base_list_view.ItemAction):
  def __init__(self, buttons, button_widths, selected_index=0, callback=None):
    spacing = base_list_view.RIGHT_ITEM_PADDING
    super().__init__(width=sum(button_widths) + spacing * (len(buttons) - 1), enabled=True)
    self._buttons = buttons
    self._button_widths = button_widths
    self._selected = selected_index
    self._callback = callback
    self._font = gui_app.font(base_list_view.BUTTON_FONT_WEIGHT)

  def get_selected_button(self):
    return self._selected

  def set_selected_button(self, index):
    if 0 <= index < len(self._buttons):
      self._selected = index

  def _render(self, rect):
    spacing = base_list_view.RIGHT_ITEM_PADDING
    button_y = rect.y + (rect.height - base_list_view.BUTTON_HEIGHT) / 2
    button_x = rect.x

    for i, btn_text in enumerate(self._buttons):
      bw = self._button_widths[i]
      button_rect = base_list_view.rl.Rectangle(button_x, button_y, bw, base_list_view.BUTTON_HEIGHT)

      mouse_pos = base_list_view.rl.get_mouse_position()
      is_pressed = base_list_view.rl.check_collision_point_rec(mouse_pos, button_rect) and self.enabled and self.is_pressed

      if i == self._selected:
        bg_color = base_list_view.rl.Color(51, 171, 76, 255)
      elif is_pressed:
        bg_color = base_list_view.rl.Color(74, 74, 74, 255)
      else:
        bg_color = base_list_view.rl.Color(57, 57, 57, 255)

      base_list_view.rl.draw_rectangle_rounded(button_rect, 1.0, 20, bg_color)

      text = base_list_view._resolve_value(btn_text, "")
      text_size = base_list_view.measure_text_cached(self._font, text, 40)
      text_x = button_x + (bw - text_size.x) / 2
      text_y = button_y + (base_list_view.BUTTON_HEIGHT - text_size.y) / 2
      text_color = base_list_view.rl.Color(228, 228, 228, 255) if self.enabled else base_list_view.rl.Color(150, 150, 150, 255)
      base_list_view.rl.draw_text_ex(self._font, text, base_list_view.rl.Vector2(text_x, text_y), 40, 0, text_color)

      button_x += bw + spacing

  def _handle_mouse_release(self, mouse_pos):
    spacing = base_list_view.RIGHT_ITEM_PADDING
    button_y = self._rect.y + (self._rect.height - base_list_view.BUTTON_HEIGHT) / 2
    button_x = self._rect.x

    for i in range(len(self._buttons)):
      bw = self._button_widths[i]
      button_rect = base_list_view.rl.Rectangle(button_x, button_y, bw, base_list_view.BUTTON_HEIGHT)
      if base_list_view.rl.check_collision_point_rec(mouse_pos, button_rect):
        self._selected = i
        if self._callback:
          self._callback(i)
        return
      button_x += bw + spacing


def multiple_button_item(title: str | Callable[[], str], description: str | Callable[[], str], buttons: list[str | Callable[[], str]], selected_index: int,
                         button_width: int = base_list_view.BUTTON_WIDTH, callback: Callable = None, icon: str = "") -> FrogPilotListItem:
  font = gui_app.font(base_list_view.BUTTON_FONT_WEIGHT)
  button_widths = []
  for btn in buttons:
    text = base_list_view._resolve_value(btn, "")
    text_width = base_list_view.measure_text_cached(font, text, 40).x
    button_widths.append(max(button_width, int(text_width + BUTTON_PADDING * 2)))
  action = FrogPilotMultipleButtonAction(buttons, button_widths, selected_index, callback=callback)
  return FrogPilotListItem(title=title, description=description, icon=icon, action_item=action)
