from collections.abc import Callable

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets.button import Button, ButtonStyle

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem

BUTTON_FONT_SIZE = 40


class ButtonsAction(base_list_view.ItemAction):
  def __init__(self, buttons: list[dict], button_width: int = base_list_view.BUTTON_WIDTH):
    super().__init__(enabled=True)
    self._button_width = button_width
    self._font = gui_app.font(base_list_view.BUTTON_FONT_WEIGHT)
    self._width_hint = 0.0
    self._buttons = [
      {
        "button": Button(
          text="",
          click_callback=spec["callback"],
          font_size=BUTTON_FONT_SIZE,
          font_weight=base_list_view.BUTTON_FONT_WEIGHT,
          button_style=ButtonStyle.LIST_ACTION,
          border_radius=base_list_view.BUTTON_BORDER_RADIUS,
          text_padding=0,
        ),
        "text_source": spec["text"],
        "enabled_source": spec.get("enabled", True),
        "visible_source": spec.get("visible", True),
        "width": float(button_width),
      }
      for spec in buttons
    ]
    self._refresh_buttons()

  @staticmethod
  def _resolve(source, default=True):
    return source() if callable(source) else source if source is not None else default

  def _refresh_buttons(self) -> None:
    self._width_hint = 0.0

    visible_count = 0
    for button_spec in self._buttons:
      if not self._resolve(button_spec["visible_source"], True):
        continue
      text = self._resolve(button_spec["text_source"], "")
      button_spec["button"].set_text(text)
      button_spec["width"] = max(self._button_width, measure_text_cached(self._font, text, BUTTON_FONT_SIZE).x + base_list_view.TEXT_PADDING * 2)
      visible_count += 1

    visible_buttons = [b for b in self._buttons if self._resolve(b["visible_source"], True)]
    total_width = sum(button["width"] for button in visible_buttons)
    total_spacing = max(0, visible_count - 1) * base_list_view.RIGHT_ITEM_PADDING
    self._width_hint = total_width + total_spacing

  def get_width_hint(self) -> float:
    visible_buttons = [b for b in self._buttons if self._resolve(b["visible_source"], True)]
    if not visible_buttons:
      return 0.0
    total_width = sum(b["width"] for b in visible_buttons)
    total_spacing = (len(visible_buttons) - 1) * base_list_view.RIGHT_ITEM_PADDING
    return total_width + total_spacing

  def set_touch_valid_callback(self, touch_callback: Callable[[], bool]) -> None:
    super().set_touch_valid_callback(touch_callback)
    for button in self._buttons:
      button["button"].set_touch_valid_callback(touch_callback)

  def show_event(self) -> None:
    super().show_event()
    self._refresh_buttons()

  def _render(self, rect: base_list_view.rl.Rectangle) -> bool:
    button_y = rect.y + (rect.height - base_list_view.BUTTON_HEIGHT) / 2
    button_x = rect.x

    for button_spec in self._buttons:
      if not self._resolve(button_spec["visible_source"], True):
        continue
      button = button_spec["button"]
      button.set_enabled(self._resolve(button_spec["enabled_source"], True))
      button.render(base_list_view.rl.Rectangle(button_x, button_y, button_spec["width"], base_list_view.BUTTON_HEIGHT))
      button_x += button_spec["width"] + base_list_view.RIGHT_ITEM_PADDING

    return False


def buttons_item(title: str | Callable[[], str], buttons: list[dict], description: str | Callable[[], str] | None = None,
                 icon: str = "", button_width: int = base_list_view.BUTTON_WIDTH) -> FrogPilotListItem:
  action = ButtonsAction(buttons=buttons, button_width=button_width)
  return FrogPilotListItem(title=title, description=description, icon=icon, action_item=action)
