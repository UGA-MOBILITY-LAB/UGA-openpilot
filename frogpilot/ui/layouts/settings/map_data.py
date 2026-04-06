import json
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path

from openpilot.common.basedir import BASEDIR
from openpilot.common.swaglog import cloudlog
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog

from openpilot.frogpilot.common import frogpilot_functions, frogpilot_variables
from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget
from openpilot.frogpilot.system.ui.widgets.selectable_grid import sectioned_selectable_grid

PROGRESS_LERP_SECONDS = 1.0
PROGRESS_CACHE_SECONDS = 0.05
DOWNLOADED_STICKY_SECONDS = 3.0

PANEL_KEY = "map_data"

_DOWNLOAD_MENU_PATH = Path(BASEDIR) / "frogpilot" / "navigation" / "download_menu.json"

COUNTRY_REGIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
  ("Africa", (
    "DZ", "AO", "BJ", "BW", "BF", "BI", "CM", "CF", "TD", "CG", "CD", "DJ", "EG", "GQ", "ER",
    "ET", "GA", "GM", "GH", "GN", "GW", "CI", "KE", "LS", "LR", "LY", "MG", "MW", "ML", "MR",
    "MA", "MZ", "NA", "NE", "NG", "RW", "SN", "SL", "SO", "ZA", "SS", "SD", "SZ", "TZ", "TG",
    "TN", "UG", "ZM", "ZW",
  )),
  ("Antarctica", ("AQ", "TF")),
  ("Asia", (
    "AF", "AM", "AZ", "BD", "BT", "BN", "KH", "CN", "CY", "TL", "GE", "IN", "ID", "IR", "IQ",
    "IL", "JP", "JO", "KZ", "KW", "KG", "LA", "LB", "MY", "MN", "MM", "NP", "KP", "OM", "PK",
    "PH", "QA", "SA", "KR", "LK", "SY", "TW", "TJ", "TH", "TR", "TM", "AE", "UZ", "VN", "PS",
    "YE",
  )),
  ("Europe", (
    "AL", "AT", "BY", "BE", "BA", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU",
    "IS", "IE", "IT", "LV", "LT", "LU", "MK", "MD", "ME", "NL", "NO", "PL", "PT", "RO", "RU",
    "RS", "SK", "SI", "ES", "SE", "CH", "UA", "GB",
  )),
  ("North America", (
    "BS", "BZ", "CA", "CR", "CU", "DO", "SV", "GL", "GT", "HT", "HN", "JM", "MX", "NI", "PA",
    "PR", "TT", "US",
  )),
  ("Oceania", ("AU", "FJ", "NC", "NZ", "PG", "SB", "VU")),
  ("South America", ("AR", "BO", "BR", "CL", "CO", "EC", "FK", "GY", "PY", "PE", "SR", "UY", "VE")),
)

US_STATE_REGIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
  ("Northeast", ("CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT")),
  ("Midwest", ("IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI")),
  ("South", ("AL", "AR", "DE", "DC", "FL", "GA", "KY", "LA", "MD", "MS", "NC", "OK", "SC", "TN", "TX", "VA", "WV")),
  ("West", ("AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY")),
  ("Territories", ("AS", "GM", "MP", "PR", "VI")),
)


def _load_regions(section: str) -> tuple[tuple[str, str], ...]:
  try:
    with _DOWNLOAD_MENU_PATH.open(encoding="utf-8") as f:
      data = json.load(f)
  except (OSError, json.JSONDecodeError):
    return ()

  section_data = data.get(section) or {}
  entries = [(code, info.get("full_name", code)) for code, info in section_data.items()]
  entries.sort(key=lambda entry: entry[1])
  return tuple(entries)


COUNTRIES = _load_regions("nation")
US_STATES = _load_regions("us_state")


class FrogPilotMapDataPanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()

    self._selected: set[str] = self._load_selected_tokens()
    self._storage_cache: str | None = None
    self._downloading = False
    self._cancel_requested = False
    self._progress_total_raw = 0
    self._progress_target = 0
    self._progress_prev = 0.0
    self._progress_target_time = 0.0
    self._cached_value = ""
    self._cached_value_time = 0.0
    self._downloaded_recently = False

    subviews = {}
    subviews["countries"] = self._build_region_view(COUNTRIES, COUNTRY_REGIONS, "nation")
    subviews["states"] = self._build_region_view(US_STATES, US_STATE_REGIONS, "us_state")

    root_scroller = self._build_section_scroller(PANEL_KEY, "root", subviews)

    self._initialize_views(root_scroller, subviews["countries"], subviews["states"])

  def _build_region_view(self, regions: tuple[tuple[str, str], ...], groupings: tuple[tuple[str, tuple[str, ...]], ...], prefix: str):
    name_by_code = dict(regions)
    sections: list[tuple[str, list[tuple[str, str]]]] = []

    categorized: set[str] = set()
    for section_name, codes in groupings:
      categorized.update(codes)
      entries = sorted(
        ((f"{prefix}.{code}", tr(name_by_code[code])) for code in codes if code in name_by_code),
        key=lambda e: e[1],
      )
      if entries:
        sections.append((tr(section_name), entries))

    uncategorized = [(f"{prefix}.{code}", tr(name)) for code, name in regions if code not in categorized]
    if uncategorized:
      sections.append((tr("Other"), uncategorized))

    return sectioned_selectable_grid(
      sections,
      is_selected=lambda token: token in self._selected,
      on_toggle=self._on_selection_changed,
    )

  def _on_selection_changed(self, token: str, selected: bool) -> None:
    if selected:
      self._selected.add(token)
    else:
      self._selected.discard(token)
    self.params.put("MapsSelected", ",".join(sorted(self._selected)))

  def _load_selected_tokens(self) -> set[str]:
    raw = self.params.get("MapsSelected") or ""
    return set(filter(None, raw.split(",")))

  def _value_last_maps_update(self) -> str:
    value = self.params.get("LastMapsUpdate") or ""
    return value if value else tr("Never")

  def _on_update_maps(self) -> None:
    if self._downloading:
      self._cancel_requested = True
      return
    if not self._selected:
      gui_app.set_modal_overlay(alert_dialog(tr("Select countries or states first.")))
      return

    self._downloading = True
    self._cancel_requested = False
    self._downloaded_recently = False
    self._reset_progress_state()
    threading.Thread(target=self._run_update_maps, daemon=True).start()

  def _reset_progress_state(self) -> None:
    self._progress_total_raw = 0
    self._progress_target = 0
    self._progress_prev = 0.0
    self._progress_target_time = time.monotonic()
    self._cached_value = ""
    self._cached_value_time = 0.0

  def _run_update_maps(self) -> None:
    status = "error"
    try:
      status = self._attempt_update_maps()
    except Exception:
      cloudlog.exception("_run_update_maps: unhandled exception")
      status = "error"
    finally:
      self._downloading = False
      self._cancel_requested = False
      self._reset_progress_state()
      self._storage_cache = None

    if status == "ok":
      self._downloaded_recently = True
      threading.Timer(DOWNLOADED_STICKY_SECONDS, self._clear_downloaded).start()
    elif status == "timed_out":
      gui_app.set_modal_overlay(alert_dialog(tr("Map service isn't responding. Please reboot the device.")))
    elif status == "error":
      gui_app.set_modal_overlay(alert_dialog(tr("Download failed.")))

  def _attempt_update_maps(self) -> str:
    return frogpilot_functions.update_maps(
      datetime.now(), self.params, manual_update=True,
      progress_cb=self._on_download_progress,
      cancel_check=lambda: self._cancel_requested,
    ) or "ok"

  def _on_download_progress(self, progress) -> None:
    done = int(getattr(progress, "downloadedFiles", 0))
    total = int(getattr(progress, "totalFiles", 0))
    self._progress_total_raw = total
    if total <= 0:
      return
    new_target = min(100, int(done * 100 / total))
    if new_target != self._progress_target:
      self._progress_prev = self._displayed_pct_now()
      self._progress_target = new_target
      self._progress_target_time = time.monotonic()

  def _displayed_pct_now(self) -> float:
    elapsed = time.monotonic() - self._progress_target_time
    factor = min(1.0, elapsed / PROGRESS_LERP_SECONDS) if PROGRESS_LERP_SECONDS > 0 else 1.0
    return self._progress_prev + (self._progress_target - self._progress_prev) * factor

  def _clear_downloaded(self) -> None:
    self._downloaded_recently = False

  def _text_update_maps(self) -> str:
    return tr("CANCEL") if self._downloading else tr("DOWNLOAD")

  def _value_update_maps(self) -> str:
    now = time.monotonic()
    if now - self._cached_value_time >= PROGRESS_CACHE_SECONDS:
      self._cached_value = self._compute_value_text()
      self._cached_value_time = now
    return self._cached_value

  def _compute_value_text(self) -> str:
    if self._downloaded_recently:
      return tr("Downloaded!")
    if not self._downloading:
      return ""
    if self._cancel_requested:
      return tr("Cancelling...")
    if self._progress_total_raw <= 0:
      return tr("Starting...")
    pct = int(round(self._displayed_pct_now()))
    return f"{pct}% "

  def _on_remove_maps(self) -> None:
    dialog = ConfirmDialog(tr("Are you sure you want to delete all downloaded maps?"), tr("Remove"))
    gui_app.set_modal_overlay(dialog, callback=self._remove_maps)

  def _remove_maps(self, result: int) -> None:
    if result != 1:
      return

    shutil.rmtree(frogpilot_variables.MAPS_PATH, ignore_errors=True)
    self.params.remove("LastMapsUpdate")
    self._storage_cache = None

    if self._current_view is not None:
      self._current_view.show_event()

  def _value_storage_used(self) -> str:
    if self._storage_cache is None:
      self._storage_cache = self._compute_storage_used()
    return self._storage_cache

  def _compute_storage_used(self) -> str:
    maps_path = frogpilot_variables.MAPS_PATH
    if not maps_path.exists():
      return self._format_bytes(0)

    total = 0
    for p in maps_path.rglob("*"):
      if p.is_file():
        try:
          total += p.stat().st_size
        except OSError:
          pass
    return self._format_bytes(total)

  @staticmethod
  def _format_bytes(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
      if num_bytes < 1024:
        if unit == "B":
          return f"{int(num_bytes)} {unit}"
        return f"{num_bytes:.1f} {unit}"
      num_bytes /= 1024
    return f"{num_bytes:.1f} PB"

  def show_event(self) -> None:
    self._storage_cache = None
    super().show_event()
