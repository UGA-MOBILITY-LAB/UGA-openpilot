import math
import pyray as rl
import time

from decimal import Decimal

from collections.abc import Callable

from openpilot.common.params import ParamKeyType, Params
from openpilot.system.ui.lib.application import FONT_SCALE, FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.list_view import BUTTON_FONT_WEIGHT, BUTTON_HEIGHT, ITEM_TEXT_FONT_SIZE, ITEM_TEXT_VALUE_COLOR, RIGHT_ITEM_PADDING, ItemAction

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem

COARSE_REPEAT_MULTIPLIER = 5
HOLD_REPEAT_DELAY_SECONDS = 0.5
HOLD_REPEAT_INTERVAL_SECONDS = 0.15

BUTTON_WIDTH = 150
BUTTON_FONT_SIZE = 40
STEP_BUTTON_FONT_SIZE = 60
VALUE_PADDING = 40

VALUE_COLOR = rl.Color(224, 232, 121, 255)


class FrogPilotParamValueAction(ItemAction):
  def __init__(self, param_key: str, minimum: int | float, maximum: int | float,
               width_values: tuple[int | float, ...] = (),
               value_formatter: Callable[[int | float], str] = str,
               step: int | float = 1,
               si_to_display: Callable[[int | float], float] | None = None,
               display_to_si: Callable[[int | float], float] | None = None,
               enabled: bool | Callable[[], bool] = True):

    super().__init__(0, enabled)
    self._params = Params(return_defaults=True)
    self._param_type = self._params.get_type(param_key)
    self._font = gui_app.font(FontWeight.MEDIUM)

    self._minimum = minimum
    self._maximum = maximum
    self._param_key = param_key
    self._step = step
    self._width_values = width_values
    self._si_to_display = si_to_display
    self._display_to_si = display_to_si
    self._value = self._read_value()
    self._value_formatter = value_formatter

    self._layout_value_width = self._compute_layout_value_width()

    self._dirty = False
    self._repeat_triggered = False

    self._held_button: str | None = None
    self._hold_origin_value: int | float | None = None
    self._hold_started_at: float | None = None
    self._last_repeat_at: float | None = None

    self._decrement_button = Button(
      "",
      click_callback=lambda: self._handle_step_click("decrement", -self._step),
      font_size=STEP_BUTTON_FONT_SIZE,
      font_weight=BUTTON_FONT_WEIGHT,
      button_style=ButtonStyle.LIST_ACTION,
      border_radius=50,
      text_padding=0,
    )
    self._increment_button = Button(
      "",
      click_callback=lambda: self._handle_step_click("increment", self._step),
      font_size=STEP_BUTTON_FONT_SIZE,
      font_weight=BUTTON_FONT_WEIGHT,
      button_style=ButtonStyle.LIST_ACTION,
      border_radius=50,
      text_padding=0,
    )

  @property
  def _min(self) -> int | float:
    return self._minimum() if callable(self._minimum) else self._minimum

  @property
  def _max(self) -> int | float:
    return self._maximum() if callable(self._maximum) else self._maximum

  def _step_precision(self) -> int | None:
    if not isinstance(self._step, (int, float)):
      return None

    step_decimal = Decimal(str(self._step)).normalize()
    exponent = step_decimal.as_tuple().exponent
    return -exponent if exponent < 0 else None

  def _snap_to_step(self, value: int | float) -> int | float:
    if self._step == 0:
      return value

    snapped = round(value / self._step) * self._step
    precision = self._step_precision()
    return round(snapped, precision) if precision is not None else snapped

  def get_width_hint(self) -> float:
    self._layout_value_width = self._compute_layout_value_width()
    return self._layout_value_width + BUTTON_WIDTH * 2 + RIGHT_ITEM_PADDING * 2

  def _compute_layout_value_width(self) -> float:
    candidates = {self._value, self._min, self._max, *self._width_values}
    widths = []
    for candidate in candidates:
      text = self._value_formatter(candidate)
      widths.append(measure_text_cached(self._font, text, ITEM_TEXT_FONT_SIZE).x)
    return (max(widths) if widths else 0) + VALUE_PADDING

  def _handle_step_click(self, key: str, delta: int | float) -> None:
    if self._repeat_triggered and self._held_button == key:
      self._repeat_triggered = False
      return

    self._step_value(delta)

  def _is_coarse_boundary(self) -> bool:
    coarse_step = self._step * COARSE_REPEAT_MULTIPLIER
    if coarse_step == 0:
      return True

    quotient = self._value / coarse_step
    tolerance = max(abs(self._step) / 1000, 1e-9)
    return math.isclose(quotient, round(quotient), abs_tol=tolerance)

  def _pressed_key(self) -> str | None:
    if self._decrement_button.enabled and self._decrement_button.is_pressed:
      return "decrement"
    if self._increment_button.enabled and self._increment_button.is_pressed:
      return "increment"
    return None

  def _read_value(self) -> int | float:
    raw = self._params.get(self._param_key)
    if self._si_to_display is not None:
      raw = self._si_to_display(raw)
    raw = self._snap_to_step(raw)
    return min(max(raw, self._min), self._max)

  def _flush_value(self) -> None:
    if self._dirty:
      self._dirty = False
      value = self._value
      if self._display_to_si is not None:
        value = self._display_to_si(value)
      if self._param_type == ParamKeyType.FLOAT:
        value = float(value)
      elif self._param_type == ParamKeyType.INT and isinstance(value, float):
        if not value.is_integer():
          raise TypeError(f"Non-integral value for integer param {self._param_key}: {value}")
        value = int(value)
      self._params.put(self._param_key, value)

  def _draw_step_text(self, text: str, rect: rl.Rectangle, enabled: bool) -> None:
    scale = STEP_BUTTON_FONT_SIZE * FONT_SCALE / self._font.baseSize
    glyph = rl.get_glyph_info(self._font, ord(text))
    rec = rl.get_glyph_atlas_rec(self._font, ord(text))
    glyph_center_y = (glyph.offsetY + int(rec.height) / 2) * scale
    text_width = measure_text_cached(self._font, text, STEP_BUTTON_FONT_SIZE).x
    pos = rl.Vector2(
      rect.x + (rect.width - text_width) / 2,
      rect.y + rect.height / 2 - glyph_center_y,
    )
    color = rl.Color(228, 228, 228, 255 if enabled else 51)
    rl.draw_text_ex(self._font, text, pos, STEP_BUTTON_FONT_SIZE, 0, color)

  def _render_step_buttons(self, start_x: float, button_y: float) -> float:
    decrement_rect = rl.Rectangle(start_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    self._decrement_button.set_enabled(self.enabled and self._value > self._min)
    self._decrement_button.render(decrement_rect)
    self._draw_step_text("-", decrement_rect, self._decrement_button.enabled)

    increment_rect = rl.Rectangle(decrement_rect.x + BUTTON_WIDTH + RIGHT_ITEM_PADDING, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    self._increment_button.set_enabled(self.enabled and self._value < self._max)
    self._increment_button.render(increment_rect)
    self._draw_step_text("+", increment_rect, self._increment_button.enabled)

    return increment_rect.x + BUTTON_WIDTH

  def _render(self, rect: rl.Rectangle) -> bool:
    self._layout_value_width = self._compute_layout_value_width()
    button_y = rect.y + (rect.height - BUTTON_HEIGHT) / 2
    value_rect = rl.Rectangle(rect.x, rect.y, self._layout_value_width, rect.height)
    gui_label(
      value_rect,
      self._value_formatter(self._value),
      font_size=ITEM_TEXT_FONT_SIZE,
      color=VALUE_COLOR,
      alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
      alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE,
      elide_right=False,
    )
    self._render_step_buttons(rect.x + self._layout_value_width + RIGHT_ITEM_PADDING, button_y)
    return False

  def _reset_hold_state(self) -> None:
    self._repeat_triggered = False
    self._held_button = None
    self._hold_origin_value = None
    self._hold_started_at = None
    self._last_repeat_at = None

  def _repeat_delta(self) -> int | float:
    base_delta = -self._step if self._held_button == "decrement" else self._step
    if self._hold_origin_value is None:
      return base_delta

    coarse_delta = base_delta * COARSE_REPEAT_MULTIPLIER
    if abs(self._value - self._hold_origin_value) < abs(coarse_delta):
      return base_delta

    return coarse_delta if self._is_coarse_boundary() else base_delta

  def _set_held_button(self, key: str) -> None:
    if self._held_button == key:
      return

    self._held_button = key
    self._hold_origin_value = self._value
    self._hold_started_at = None
    self._last_repeat_at = None
    self._repeat_triggered = False

  def _step_value(self, delta: int | float) -> None:
    new_value = self._snap_to_step(self._value + delta)
    new_value = min(max(new_value, self._min), self._max)
    if new_value == self._value:
      return

    self._value = new_value
    self._dirty = True

  def _update_state(self):
    super()._update_state()
    pressed_key = self._pressed_key()
    if pressed_key is None:
      self._reset_hold_state()
      return

    if self._held_button != pressed_key:
      self._set_held_button(pressed_key)
      return

    now = time.monotonic()
    if self._hold_started_at is None:
      self._hold_started_at = now
      self._last_repeat_at = now
      return

    if now - self._hold_started_at < HOLD_REPEAT_DELAY_SECONDS:
      return

    if self._last_repeat_at is None or now - self._last_repeat_at >= HOLD_REPEAT_INTERVAL_SECONDS:
      self._step_value(self._repeat_delta())
      self._last_repeat_at = now
      self._repeat_triggered = True

  def hide_event(self) -> None:
    super().hide_event()
    self._reset_hold_state()
    self._flush_value()

  def set_touch_valid_callback(self, touch_callback) -> None:
    super().set_touch_valid_callback(touch_callback)
    self._decrement_button.set_touch_valid_callback(touch_callback)
    self._increment_button.set_touch_valid_callback(touch_callback)

  def refresh_value(self) -> None:
    self._value = self._read_value()
    self._layout_value_width = self._compute_layout_value_width()

  def show_event(self) -> None:
    super().show_event()
    self._dirty = False
    self._value = self._read_value()
    self._layout_value_width = self._compute_layout_value_width()
    self._reset_hold_state()

def param_value_item(title, description, param_key: str,
                     minimum: int | float, maximum: int | float,
                     width_values: tuple[int | float, ...] = (),
                     value_formatter: Callable[[int | float], str] = str,
                     step: int | float = 1,
                     si_to_display: Callable[[int | float], float] | None = None,
                     display_to_si: Callable[[int | float], float] | None = None,
                     enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = FrogPilotParamValueAction(
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
  return FrogPilotListItem(title=title, description=description, action_item=action)
