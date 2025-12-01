import pyray as rl

from openpilot.selfdrive.ui.mici.onroad import SIDE_PANEL_WIDTH as STOCK_SIDE_PANEL_WIDTH
from openpilot.selfdrive.ui.mici.onroad import blend_colors as stock_blend_colors


SIDE_PANEL_WIDTH = STOCK_SIDE_PANEL_WIDTH


def blend_colors(a: rl.Color, b: rl.Color, f: float) -> rl.Color:
  return stock_blend_colors(a, b, f)
