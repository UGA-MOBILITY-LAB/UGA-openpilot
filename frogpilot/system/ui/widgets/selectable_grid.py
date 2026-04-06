import math
from collections.abc import Callable, Iterable

import pyray as rl

from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.scroller_tici import LineSeparator, Scroller

GRID_COLUMNS = 3
GRID_BUTTON_HEIGHT = 100
GRID_BUTTON_SPACING = 20
GRID_BUTTON_FONT_SIZE = 40
GRID_BUTTON_BORDER_RADIUS = 50
SECTION_HEADER_HEIGHT = 80
SECTION_HEADER_FONT_SIZE = 50
SECTION_HEADER_TEXT_PADDING = 20

SELECTED_BG = rl.Color(51, 171, 76, 255)
UNSELECTED_BG = rl.Color(57, 57, 57, 255)
PRESSED_BG = rl.Color(74, 74, 74, 255)
BUTTON_TEXT_COLOR = rl.Color(228, 228, 228, 255)
DISABLED_BG = rl.Color(51, 51, 51, 150)
DISABLED_TEXT = rl.Color(150, 150, 150, 255)


class SelectableButton(Button):
  def __init__(self, text, selected: bool = False, **kwargs):
    kwargs.setdefault("font_size", GRID_BUTTON_FONT_SIZE)
    kwargs.setdefault("border_radius", GRID_BUTTON_BORDER_RADIUS)
    kwargs.setdefault("elide_right", True)
    super().__init__(text, button_style=ButtonStyle.NORMAL, **kwargs)
    self.selected = selected

  def _update_state(self):
    if not self.enabled:
      self._background_color = DISABLED_BG
      self._label.set_text_color(DISABLED_TEXT)
      return

    self._label.set_text_color(BUTTON_TEXT_COLOR)
    if self.selected:
      self._background_color = SELECTED_BG
    elif self.is_pressed:
      self._background_color = PRESSED_BG
    else:
      self._background_color = UNSELECTED_BG


class ButtonGrid(Widget):
  def __init__(self, buttons: list[Button], columns: int = GRID_COLUMNS, button_height: int = GRID_BUTTON_HEIGHT, spacing: int = GRID_BUTTON_SPACING):
    super().__init__()
    self._buttons = buttons
    self._columns = max(1, columns)
    self._button_height = button_height
    self._spacing = spacing

    rows = max(1, math.ceil(len(buttons) / self._columns)) if buttons else 0
    total_height = rows * button_height + max(0, rows - 1) * spacing
    self.set_rect(rl.Rectangle(0, 0, 0, total_height))

  def _render(self, rect: rl.Rectangle) -> None:
    if not self._buttons:
      return

    viewport = self._parent_rect
    available_width = viewport.width if viewport is not None and viewport.width > 0 else rect.width
    col_width = (available_width - self._spacing * (self._columns - 1)) / self._columns

    for i, btn in enumerate(self._buttons):
      r = i // self._columns
      c = i % self._columns
      x = rect.x + c * (col_width + self._spacing)
      y = rect.y + r * (self._button_height + self._spacing)

      if viewport is not None:
        if y + self._button_height < viewport.y or y > viewport.y + viewport.height:
          continue

      btn.set_parent_rect(viewport if viewport is not None else rect)
      btn.render(rl.Rectangle(x, y, col_width, self._button_height))


class SectionHeader(Widget):
  def __init__(self, text, height: int = SECTION_HEADER_HEIGHT, font_size: int = SECTION_HEADER_FONT_SIZE):
    super().__init__()
    self._text_source = text
    self._font_size = font_size
    self._font = gui_app.font(FontWeight.BOLD)
    self.set_rect(rl.Rectangle(0, 0, 0, height))

  def _render(self, rect: rl.Rectangle) -> None:
    text = self._text_source() if callable(self._text_source) else self._text_source
    text_x = rect.x + SECTION_HEADER_TEXT_PADDING
    text_y = rect.y + (rect.height - self._font_size) / 2
    rl.draw_text_ex(self._font, text, rl.Vector2(text_x, text_y), self._font_size, 0, rl.WHITE)


def sectioned_selectable_grid(sections: Iterable[tuple[str, Iterable[tuple[str, str]]]], is_selected: Callable[[str], bool], on_toggle: Callable[[str, bool], None], *, columns: int = GRID_COLUMNS, button_height: int = GRID_BUTTON_HEIGHT, spacing: int = GRID_BUTTON_SPACING) -> Scroller:
  items: list[Widget] = []

  for title, entries in sections:
    entries = list(entries)
    if not entries:
      continue

    if items:
      items.append(LineSeparator())

    items.append(SectionHeader(title))

    buttons: list[Button] = []
    for key, label in entries:
      btn = SelectableButton(label, selected=is_selected(key))
      btn.set_click_callback(_make_toggle_callback(btn, key, on_toggle))
      buttons.append(btn)

    items.append(ButtonGrid(buttons, columns=columns, button_height=button_height, spacing=spacing))

  return Scroller(items, line_separator=False, spacing=spacing)


def _make_toggle_callback(btn: SelectableButton, key: str, on_toggle: Callable[[str, bool], None]) -> Callable[[], None]:
  def callback() -> None:
    btn.selected = not btn.selected
    on_toggle(key, btn.selected)

  return callback
