import pyray as rl

from collections.abc import Callable

from openpilot.system.ui.widgets.button import Button, ButtonStyle
from openpilot.system.ui.widgets.label import gui_label
from openpilot.system.ui.widgets.list_view import BUTTON_FONT_WEIGHT, BUTTON_HEIGHT, ITEM_TEXT_FONT_SIZE, ITEM_TEXT_VALUE_COLOR, RIGHT_ITEM_PADDING

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem
from openpilot.frogpilot.system.ui.widgets.param_value import BUTTON_FONT_SIZE, BUTTON_WIDTH, VALUE_COLOR, FrogPilotParamValueAction

AUXILIARY_BUTTON_WIDTH = 200


class FrogPilotParamValueButtonAction(FrogPilotParamValueAction):
  def __init__(self, param_key: str, minimum: int | float, maximum: int | float,
               button_text: str | Callable[[], str], button_callback: Callable[[], None],
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
    self._extra_button_width = AUXILIARY_BUTTON_WIDTH

    self._button_callback = button_callback
    self._left_button = Button(
      button_text,
      click_callback=self._handle_left_button_click,
      font_size=BUTTON_FONT_SIZE,
      font_weight=BUTTON_FONT_WEIGHT,
      button_style=ButtonStyle.LIST_ACTION,
      border_radius=50,
      text_padding=0,
    )

  def get_width_hint(self) -> float:
    return self._extra_button_width + RIGHT_ITEM_PADDING + super().get_width_hint()

  def _handle_left_button_click(self) -> None:
    self._flush_value()
    self._button_callback()

  def _render(self, rect: rl.Rectangle) -> bool:
    button_y = rect.y + (rect.height - BUTTON_HEIGHT) / 2
    self._layout_value_width = self._compute_layout_value_width()

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
    buttons_end_x = self._render_step_buttons(rect.x + self._layout_value_width + RIGHT_ITEM_PADDING, button_y)
    reset_x = buttons_end_x + RIGHT_ITEM_PADDING
    self._left_button.set_enabled(self.enabled)
    self._left_button.render(rl.Rectangle(reset_x, button_y, AUXILIARY_BUTTON_WIDTH, BUTTON_HEIGHT))
    return False

  def set_touch_valid_callback(self, touch_callback) -> None:
    super().set_touch_valid_callback(touch_callback)
    self._left_button.set_touch_valid_callback(touch_callback)


def param_value_button_item(title, description, param_key: str,
                            minimum: int | float, maximum: int | float,
                            button_text: str | Callable[[], str], button_callback: Callable[[], None],
                            width_values: tuple[int | float, ...] = (),
                            value_formatter: Callable[[int | float], str] = str,
                            step: int | float = 1,
                            si_to_display=None,
                            display_to_si=None,
                            enabled: bool | Callable[[], bool] = True):
  action = FrogPilotParamValueButtonAction(
    param_key=param_key,
    minimum=minimum,
    maximum=maximum,
    width_values=width_values,
    button_text=button_text,
    button_callback=button_callback,
    value_formatter=value_formatter,
    step=step,
    si_to_display=si_to_display,
    display_to_si=display_to_si,
    enabled=enabled,
  )
  return FrogPilotListItem(title=title, description=description, action_item=action)
