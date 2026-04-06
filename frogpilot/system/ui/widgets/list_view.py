import os

from collections.abc import Callable

import openpilot.system.ui.widgets.list_view as base_list_view

from openpilot.common.basedir import BASEDIR
from openpilot.system.ui.lib.application import gui_app

FROGPILOT_ICON_SIZE = 80
FROGPILOT_ITEM_BASE_HEIGHT = 146


class FrogPilotListItem(base_list_view.ListItem):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._title_text = ""
    self._title_size = base_list_view.rl.Vector2(0.0, 0.0)
    self._title_width = 0.0
    self._refresh_title_layout()

    content_width = int(self._rect.width - base_list_view.ITEM_PADDING * 2)
    self.set_rect(base_list_view.rl.Rectangle(self._rect.x, self._rect.y, self._rect.width, self.get_item_height(self._font, content_width)))

  def _refresh_title_layout(self) -> None:
    title = self.title
    if title == self._title_text:
      return

    self._title_text = title
    self._title_size = base_list_view.measure_text_cached(self._font, title, base_list_view.ITEM_TEXT_FONT_SIZE)
    self._title_width = self._title_size.x

  def set_icon(self, icon: str | None):
    self.icon = icon
    if self.icon:
      path = os.path.join(BASEDIR, self.icon)
      image = base_list_view.rl.load_image(path)
      base_list_view.rl.image_resize(image, FROGPILOT_ICON_SIZE, FROGPILOT_ICON_SIZE)
      self._icon_texture = base_list_view.rl.load_texture_from_image(image)
      base_list_view.rl.unload_image(image)
    else:
      self._icon_texture = None

  def hide_event(self):
    super().hide_event()
    if self.action_item is not None:
      self.action_item.hide_event()

  def show_event(self):
    super().show_event()
    self._refresh_title_layout()
    if self.action_item is not None:
      self.action_item.show_event()

  def _update_state(self):
    super()._update_state()
    self._refresh_title_layout()

  def _render(self, _):
    if not self.is_visible:
      return

    # Don't draw items that are not in parent's viewport
    if ((self._rect.y + self.rect.height) <= self._parent_rect.y or
      self._rect.y >= (self._parent_rect.y + self._parent_rect.height)):
      return

    content_x = self._rect.x + base_list_view.ITEM_PADDING
    text_x = content_x

    # Only draw title and icon for items that have them
    if self._title_text:
      # Draw icon if present
      if self.icon:
        base_list_view.rl.draw_texture(self._icon_texture, int(content_x), int(self._rect.y + (FROGPILOT_ITEM_BASE_HEIGHT - self._icon_texture.height) // 2), base_list_view.rl.WHITE)
        text_x += base_list_view.ICON_SIZE + base_list_view.ITEM_PADDING

      # Draw main text
      item_y = self._rect.y + (FROGPILOT_ITEM_BASE_HEIGHT - self._title_size.y) // 2
      base_list_view.rl.draw_text_ex(self._font, self._title_text, base_list_view.rl.Vector2(text_x, item_y), base_list_view.ITEM_TEXT_FONT_SIZE, 0, base_list_view.ITEM_TEXT_COLOR)

    # Draw description if visible
    if self.description_visible:
      content_width = int(self._rect.width - base_list_view.ITEM_PADDING * 2)
      description_height = self._html_renderer.get_total_height(content_width)
      description_rect = base_list_view.rl.Rectangle(
        self._rect.x + base_list_view.ITEM_PADDING,
        self._rect.y + base_list_view.ITEM_DESC_V_OFFSET,
        content_width,
        description_height
      )
      self._html_renderer.render(description_rect)

    # Draw right item if present
    if self.action_item:
      right_rect = self.get_right_item_rect(self._rect)
      right_rect.y = self._rect.y
      if self.action_item.render(right_rect) and self.action_item.enabled:
        # Right item was clicked/activated
        if self.callback:
          self.callback()

  def get_item_height(self, font: base_list_view.rl.Font, max_width: int) -> float:
    if not self.is_visible:
      return 0

    height = float(FROGPILOT_ITEM_BASE_HEIGHT)
    if self.description_visible:
      description_height = self._html_renderer.get_total_height(max_width)
      height += (description_height - (FROGPILOT_ITEM_BASE_HEIGHT - base_list_view.ITEM_DESC_V_OFFSET) + base_list_view.ITEM_PADDING)
    return height

  def get_right_item_rect(self, item_rect: base_list_view.rl.Rectangle) -> base_list_view.rl.Rectangle:
    if not self.action_item:
      return base_list_view.rl.Rectangle(0, 0, 0, 0)

    right_width = self.action_item.get_width_hint()
    if right_width == 0:  # Full width action (like DualButtonAction)
      return base_list_view.rl.Rectangle(item_rect.x + base_list_view.ITEM_PADDING, item_rect.y,
                                         item_rect.width - (base_list_view.ITEM_PADDING * 2), FROGPILOT_ITEM_BASE_HEIGHT)

    # Clip width to available space, never overlapping this Item's title
    content_width = item_rect.width - (base_list_view.ITEM_PADDING * 2)
    right_width = min(content_width - self._title_width, right_width)

    right_x = item_rect.x + item_rect.width - right_width
    right_y = item_rect.y
    return base_list_view.rl.Rectangle(right_x, right_y, right_width, FROGPILOT_ITEM_BASE_HEIGHT)


# Factory functions
def button_item(title: str | Callable[[], str], button_text: str | Callable[[], str], description: str | Callable[[], str] | None = None,
                callback: Callable | None = None, icon: str = "", value: str | Callable[[], str] | None = None,
                enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = base_list_view.ButtonAction(text=button_text, enabled=enabled)
  if value is not None:
    action.set_value(value)
  return FrogPilotListItem(title=title, description=description, icon=icon, action_item=action, callback=callback)


def dual_button_item(left_text: str | Callable[[], str], right_text: str | Callable[[], str], left_callback: Callable = None, right_callback: Callable = None,
                     description: str | Callable[[], str] | None = None, enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = base_list_view.DualButtonAction(left_text, right_text, left_callback, right_callback, enabled)
  return FrogPilotListItem(title="", description=description, action_item=action)


def simple_item(title: str | Callable[[], str], callback: Callable | None = None) -> FrogPilotListItem:
  return FrogPilotListItem(title=title, callback=callback)


def text_item(title: str | Callable[[], str], value: str | Callable[[], str], description: str | Callable[[], str] | None = None,
              callback: Callable | None = None, enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = base_list_view.TextAction(text=value, color=base_list_view.ITEM_TEXT_VALUE_COLOR, enabled=enabled)
  return FrogPilotListItem(title=title, description=description, action_item=action, callback=callback)


def toggle_item(title: str | Callable[[], str], description: str | Callable[[], str] | None = None, initial_state: bool = False,
                callback: Callable | None = None, icon: str = "", enabled: bool | Callable[[], bool] = True) -> FrogPilotListItem:
  action = base_list_view.ToggleAction(initial_state=initial_state, enabled=enabled, callback=callback)
  return FrogPilotListItem(title=title, description=description, action_item=action, icon=icon)
