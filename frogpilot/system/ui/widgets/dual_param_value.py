import pyray as rl

from collections.abc import Callable

from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets.list_view import ITEM_TEXT_COLOR, ITEM_TEXT_FONT_SIZE, RIGHT_ITEM_PADDING, ItemAction

from openpilot.frogpilot.system.ui.widgets.list_view import FrogPilotListItem
from openpilot.frogpilot.system.ui.widgets.param_value import FrogPilotParamValueAction


class FrogPilotDualParamValueAction(ItemAction):
  def __init__(self, left: FrogPilotParamValueAction, right: FrogPilotParamValueAction,
               right_title: Callable[[], str] | None = None,
               right_description: Callable[[], str] | None = None,
               enabled: bool | Callable[[], bool] = True):
    super().__init__(0, enabled)
    self._left = left
    self._right = right
    self._right_title = right_title
    self._right_description = right_description
    self._font = gui_app.font(FontWeight.MEDIUM)
    self._right_title_rect = rl.Rectangle(0, 0, 0, 0)
    self._parent_item = None
    self._left_description = None

  def get_width_hint(self) -> float:
    width = self._left.get_width_hint() + RIGHT_ITEM_PADDING + self._right.get_width_hint()
    if self._right_title is not None:
      title_text = self._right_title()
      width += measure_text_cached(self._font, title_text, ITEM_TEXT_FONT_SIZE).x + RIGHT_ITEM_PADDING
    return width

  def _render(self, rect: rl.Rectangle) -> bool:
    left_width = self._left.get_width_hint()
    left_rect = rl.Rectangle(rect.x, rect.y, left_width, rect.height)

    self._left.set_enabled(self.enabled)
    self._left.render(left_rect)

    right_x = rect.x + left_width + RIGHT_ITEM_PADDING

    if self._right_title is not None:
      title_text = self._right_title()
      title_size = measure_text_cached(self._font, title_text, ITEM_TEXT_FONT_SIZE)
      title_y = rect.y + (rect.height - title_size.y) / 2
      self._right_title_rect = rl.Rectangle(right_x, rect.y, title_size.x, rect.height)
      rl.draw_text_ex(self._font, title_text, rl.Vector2(right_x, title_y), ITEM_TEXT_FONT_SIZE, 0, ITEM_TEXT_COLOR)
      right_x += title_size.x + RIGHT_ITEM_PADDING

    right_width = self._right.get_width_hint()
    right_rect = rl.Rectangle(right_x, rect.y, right_width, rect.height)

    self._right.set_enabled(self.enabled)
    self._right.render(right_rect)
    return False

  def _handle_mouse_release(self, mouse_pos) -> None:
    if self._right_description is not None and self._parent_item is not None:
      if rl.check_collision_point_rec(mouse_pos, self._right_title_rect):
        self._parent_item._description = self._right_description
        self._parent_item._parse_description(self._parent_item.description)
        self._parent_item._set_description_visible(not self._parent_item.description_visible)

  def _update_state(self):
    super()._update_state()
    self._left._update_state()
    self._right._update_state()
    if (self._left_description is not None and self._parent_item is not None
        and not self._parent_item.description_visible
        and self._parent_item._description is not self._left_description):
      self._parent_item._description = self._left_description

  def hide_event(self) -> None:
    super().hide_event()
    self._left.hide_event()
    self._right.hide_event()

  def refresh_value(self) -> None:
    self._left.refresh_value()
    self._right.refresh_value()

  def set_touch_valid_callback(self, touch_callback) -> None:
    super().set_touch_valid_callback(touch_callback)
    self._left.set_touch_valid_callback(touch_callback)
    self._right.set_touch_valid_callback(touch_callback)

  def show_event(self) -> None:
    super().show_event()
    self._left.show_event()
    self._right.show_event()


def dual_param_value_item(title, description, left: FrogPilotParamValueAction, right: FrogPilotParamValueAction,
                          right_title: Callable[[], str] | None = None,
                          right_description: Callable[[], str] | None = None,
                          enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = FrogPilotDualParamValueAction(left, right, right_title=right_title, right_description=right_description, enabled=enabled)
  item = FrogPilotListItem(title=title, description=description, action_item=action)
  action._parent_item = item
  action._left_description = item._description
  return item
