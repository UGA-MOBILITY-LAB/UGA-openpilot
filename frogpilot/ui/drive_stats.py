import threading
import time
from dataclasses import dataclass

import pyray as rl
import requests

from openpilot.common.api import api_get
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.ui.lib.api_helpers import get_token
from openpilot.selfdrive.ui.ui_state import device, ui_state
from openpilot.system.athena.registration import UNREGISTERED_DONGLE_ID
from openpilot.system.ui.lib.application import FONT_SCALE, FontWeight
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import gui_label

from openpilot.frogpilot.common.frogpilot_utilities import use_konik_server

ALL_TIME_TITLE = tr_noop("ALL TIME")
ALL_TIME_KONIK_TITLE = tr_noop("ALL TIME (KONIK)")
DRIVES_LABEL = tr_noop("Drives")
FROGPILOT_TITLE = tr_noop("FROGPILOT")
HOURS_LABEL = tr_noop("Hours")
KILOMETERS_LABEL = tr_noop("KM")
MILES_LABEL = tr_noop("Miles")
PAST_WEEK_TITLE = tr_noop("PAST WEEK")
PAST_WEEK_KONIK_TITLE = tr_noop("PAST WEEK (KONIK)")


@dataclass(frozen=True)
class DriveStatsSection:
  title: str
  title_color: rl.Color
  routes: str
  distance: str
  distance_unit: str
  hours: str


@dataclass(frozen=True)
class DriveStatsRenderConfig:
  panel_roundness: float
  panel_padding_x: int
  panel_padding_top: int
  panel_padding_bottom: int
  section_gap: int
  title_font_size: int
  title_gap: int
  value_font_size: int
  value_gap: int
  unit_font_size: int
  column_gap: int
  divider_height: int


BIG_RENDER_CONFIG = DriveStatsRenderConfig(
  panel_roundness=0.022,
  panel_padding_x=50,
  panel_padding_top=35,
  panel_padding_bottom=30,
  section_gap=20,
  title_font_size=50,
  title_gap=20,
  value_font_size=65,
  value_gap=10,
  unit_font_size=50,
  column_gap=10,
  divider_height=0,
)


class DriveStatsLayoutBase(Widget):
  API_TIMEOUT = 10.0
  PARAM_KEY = "ApiCache_DriveStats"
  SLEEP_INTERVAL = 0.5
  UPDATE_INTERVAL = 30.0
  PANEL_COLOR = rl.Color(51, 51, 51, 255)
  FROGPILOT_GREEN = rl.Color(23, 134, 67, 255)
  UNIT_COLOR = rl.Color(160, 160, 160, 255)
  DIVIDER_COLOR = rl.Color(255, 255, 255, 26)

  def __init__(self):
    super().__init__()
    self._params = Params()
    self._is_metric = self._params.get_bool("IsMetric")
    self._konik = use_konik_server()
    self._session = requests.Session()  # reuse session to reduce SSL handshake overhead
    self._stats = self._load_remote_stats()
    self._frogpilot_stats = self._load_frogpilot_stats()

    self._running = True
    self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
    self._update_thread.start()

  def __del__(self):
    self._running = False
    try:
      if self._update_thread and self._update_thread.is_alive():
        self._update_thread.join(timeout=1.0)
    except Exception:
      pass

  def show_event(self):
    super().show_event()
    self._refresh_data()

  def _refresh_data(self):
    self._is_metric = self._params.get_bool("IsMetric")
    self._stats = self._load_remote_stats()
    self._frogpilot_stats = self._load_frogpilot_stats()
    self._sync_minutes_param()

  def _load_frogpilot_stats(self) -> dict[str, object]:
    stats = self._params.get("FrogPilotStats")
    return stats if isinstance(stats, dict) else {}

  def _load_remote_stats(self) -> dict[str, dict[str, float]]:
    return self._coerce_remote_stats(self._params.get(self.PARAM_KEY))

  def _coerce_remote_stats(self, raw_stats: object) -> dict[str, dict[str, float]]:
    if not isinstance(raw_stats, dict):
      return {"all": {}, "week": {}}

    return {
      "all": self._coerce_remote_bucket(raw_stats.get("all")),
      "week": self._coerce_remote_bucket(raw_stats.get("week")),
    }

  def _coerce_remote_bucket(self, raw_bucket: object) -> dict[str, float]:
    if not isinstance(raw_bucket, dict):
      return {}

    return {
      "distance": self._coerce_float(raw_bucket.get("distance")),
      "minutes": self._coerce_float(raw_bucket.get("minutes")),
      "routes": self._coerce_float(raw_bucket.get("routes")),
    }

  @staticmethod
  def _coerce_float(value: object) -> float:
    try:
      return float(value)
    except (TypeError, ValueError):
      return 0.0

  def _build_sections(self) -> list[DriveStatsSection]:
    distance_unit = tr(KILOMETERS_LABEL) if self._is_metric else tr(MILES_LABEL)
    return [
      self._build_remote_section("all", tr(ALL_TIME_KONIK_TITLE) if self._konik else tr(ALL_TIME_TITLE), rl.WHITE, distance_unit),
      self._build_remote_section("week", tr(PAST_WEEK_KONIK_TITLE) if self._konik else tr(PAST_WEEK_TITLE), rl.WHITE, distance_unit),
      self._build_frogpilot_section(distance_unit),
    ]

  def _build_remote_section(self, key: str, title: str, title_color: rl.Color, distance_unit: str) -> DriveStatsSection:
    bucket = self._stats.get(key, {})
    distance = int(bucket.get("distance", 0.0) * (CV.MPH_TO_KPH if self._is_metric else 1.0))
    hours = int(bucket.get("minutes", 0.0) / 60.0)
    routes = int(bucket.get("routes", 0.0))
    return DriveStatsSection(
      title=title,
      title_color=title_color,
      routes=str(routes),
      distance=str(distance),
      distance_unit=distance_unit,
      hours=str(hours),
    )

  def _build_frogpilot_section(self, distance_unit: str) -> DriveStatsSection:
    distance = int(self._coerce_float(self._frogpilot_stats.get("FrogPilotMeters")) * (0.001 if self._is_metric else CV.KPH_TO_MPH / 1000.0))
    hours = int(self._coerce_float(self._frogpilot_stats.get("FrogPilotSeconds")) / (60.0 * 60.0))
    routes = int(self._coerce_float(self._frogpilot_stats.get("FrogPilotDrives")))
    return DriveStatsSection(
      title=tr(FROGPILOT_TITLE),
      title_color=self.FROGPILOT_GREEN,
      routes=str(routes),
      distance=str(distance),
      distance_unit=distance_unit,
      hours=str(hours),
    )

  def _fetch_drive_stats(self):
    dongle_id = self._params.get("DongleId")
    if not dongle_id or dongle_id == UNREGISTERED_DONGLE_ID:
      return

    try:
      identity_token = get_token(dongle_id)
      response = api_get(f"v1.1/devices/{dongle_id}/stats", timeout=self.API_TIMEOUT, access_token=identity_token, session=self._session)
      if response.status_code != 200:
        return

      stats = self._coerce_remote_stats(response.json())
      self._stats = stats
      self._params.put(self.PARAM_KEY, stats)
      self._sync_minutes_param()
    except Exception as exc:
      cloudlog.error(f"Failed to fetch drive stats: {exc}")

  def _sync_minutes_param(self):
    key = "KonikMinutes" if self._konik else "openpilotMinutes"
    minutes = int(self._stats.get("all", {}).get("minutes", 0.0))
    self._params.put_nonblocking(key, minutes)

  def _update_loop(self):
    while self._running:
      if not ui_state.started and device._awake:
        self._fetch_drive_stats()

      for _ in range(int(self.UPDATE_INTERVAL / self.SLEEP_INTERVAL)):
        if not self._running:
          break
        time.sleep(self.SLEEP_INTERVAL)

  def _render_section(self, rect: rl.Rectangle, section: DriveStatsSection, config: DriveStatsRenderConfig):
    title_height = round(config.title_font_size * FONT_SCALE)
    value_height = round(config.value_font_size * FONT_SCALE)
    unit_height = round(config.unit_font_size * FONT_SCALE)

    content_x = rect.x
    content_width = rect.width
    title_rect = rl.Rectangle(content_x, rect.y, content_width, title_height)
    gui_label(title_rect, section.title, font_size=config.title_font_size, color=section.title_color, font_weight=FontWeight.MEDIUM)

    values_y = title_rect.y + title_height + config.title_gap
    column_width = (content_width - (config.column_gap * 2)) / 3
    metrics = (
      (section.routes, tr(DRIVES_LABEL)),
      (section.distance, section.distance_unit),
      (section.hours, tr(HOURS_LABEL)),
    )

    for index, (value, unit) in enumerate(metrics):
      column_x = content_x + index * (column_width + config.column_gap)
      value_rect = rl.Rectangle(column_x, values_y, column_width, value_height)
      unit_rect = rl.Rectangle(column_x, values_y + value_height + config.value_gap, column_width, unit_height)
      gui_label(value_rect, value, font_size=config.value_font_size, font_weight=FontWeight.NORMAL)
      gui_label(unit_rect, unit, font_size=config.unit_font_size, color=self.UNIT_COLOR, font_weight=FontWeight.LIGHT)


class DriveStatsLayout(DriveStatsLayoutBase):
  def _render(self, rect: rl.Rectangle):
    config = BIG_RENDER_CONFIG
    sections = self._build_sections()

    rl.draw_rectangle_rounded(rect, config.panel_roundness, 20, self.PANEL_COLOR)

    inner_x = rect.x + config.panel_padding_x
    inner_y = rect.y + config.panel_padding_top
    inner_width = rect.width - (config.panel_padding_x * 2)
    inner_height = rect.height - config.panel_padding_top - config.panel_padding_bottom
    section_height = (inner_height - config.section_gap * (len(sections) - 1)) / len(sections)

    for index, section in enumerate(sections):
      section_y = inner_y + index * (section_height + config.section_gap)
      section_rect = rl.Rectangle(inner_x, section_y, inner_width, section_height)
      self._render_section(section_rect, section, config)
