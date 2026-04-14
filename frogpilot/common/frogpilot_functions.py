#!/usr/bin/env python3
import dataclasses
import json
import requests
import threading
import time

from pathlib import Path

from cereal import messaging
from openpilot.common.basedir import BASEDIR
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.common.time_helpers import system_time_valid
from openpilot.system.athena.registration import register
from openpilot.system.hardware import HARDWARE

from openpilot.frogpilot.common import frogpilot_utilities, frogpilot_variables
from openpilot.frogpilot.common.frogpilot_backups import backup_frogpilot

MAPDIN_DOWNLOAD = 0
MAPDIN_CANCEL_DOWNLOAD = 27
MAPD_DOWNLOAD_STARTED_TIMEOUT = 15.0


def capture_report(discord_user, report, params, frogpilot_toggles):
  if not frogpilot_utilities.is_url_pingable(frogpilot_variables.FROGPILOT_API):
    return

  api_token, build_metadata, device_type, dongle_id = frogpilot_utilities.get_frogpilot_api_info()

  error_file_path = frogpilot_variables.ERROR_LOGS_PATH / "error.txt"
  error_content = "No error log found."
  if error_file_path.exists():
    error_content = error_file_path.read_text()[:1000]

  payload = {
    "api_token": api_token,
    "build_metadata": build_metadata,
    "device": device_type,
    "discord_user": discord_user,
    "error_content": error_content,
    "frogpilot_dongle_id": dongle_id,
    "frogpilot_toggles": frogpilot_toggles,
    "report": report,
  }

  try:
    response = requests.post(
      f"{frogpilot_variables.FROGPILOT_API}/discord/report",
      json=payload,
      headers={"Content-Type": "application/json", "User-Agent": "frogpilot-api/1.0"},
      timeout=30,
    )
    response.raise_for_status()
    print("Successfully sent error report!")
  except requests.exceptions.RequestException as exception:
    print(f"Error sending report: {exception}")


def migrate_params_to_si(params):
  if params.get_bool("ParamsMigratedToSI"):
    return

  is_metric = params.get_bool("IsMetric")

  distance_factor = 1.0 if is_metric else CV.FOOT_TO_METER
  distance_keys = (
    "IncreasedStoppedDistance",
    "IncreasedStoppedDistanceLowVisibility",
    "IncreasedStoppedDistanceRain",
    "IncreasedStoppedDistanceRainStorm",
    "IncreasedStoppedDistanceSnow",
    "LaneDetectionWidth",
  )
  for key in distance_keys:
    value = params.get(key)
    if value is not None and value != 0:
      params.put(key, float(value) * distance_factor)

  path_factor = (1.0 if is_metric else CV.FOOT_TO_METER) / 2.0
  for key in ("PathWidth",):
    value = params.get(key)
    if value is not None and value != 0:
      params.put(key, float(value) * path_factor)

  small_distance_factor = (1.0 if is_metric else CV.INCH_TO_CM) / 200.0
  for key in ("LaneLinesWidth", "RoadEdgesWidth"):
    value = params.get(key)
    if value is not None and value != 0:
      params.put(key, float(value) * small_distance_factor)

  speed_factor = CV.KPH_TO_MS if is_metric else CV.MPH_TO_MS
  speed_keys = (
    "CESignalSpeed",
    "CESpeed",
    "CESpeedLead",
    "MinimumLaneChangeSpeed",
    "Offset1",
    "Offset2",
    "Offset3",
    "Offset4",
    "Offset5",
    "Offset6",
    "Offset7",
    "PauseAOLOnBrake",
    "PauseLateralSpeed",
    "SetSpeedOffset",
  )
  for key in speed_keys:
    value = params.get(key)
    if value is not None and value != 0:
      params.put(key, float(value) * speed_factor)

  params.put_bool("ParamsMigratedToSI", True)


def frogpilot_boot_functions(build_metadata, params):
  migrate_params_to_si(params)

  maps_selected = params.get("MapsSelected")
  if maps_selected:
    try:
      data = json.loads(maps_selected)
      if isinstance(data, dict):
        new_items = []
        for nation in data.get("nations", []):
          new_items.append(f"nation.{nation}")
        for state in data.get("states", []):
          new_items.append(f"us_state.{state}")
        new_items.sort()
        params.put("MapsSelected", ",".join(new_items))
    except (json.JSONDecodeError, TypeError, ValueError):
      pass

  frogpilot_variables.FrogPilotVariables()

  if frogpilot_utilities.use_konik_server():
    if params.get("KonikDongleId") is not None:
      params.put("DongleId", params.get("KonikDongleId"))
    else:
      params.put("KonikDongleId", register(show_spinner=True, register_konik=True))
      params.put("DongleId", params.get("KonikDongleId"))
  elif params.get("DongleId") == params.get("KonikDongleId"):
    params.put("DongleId", params.get("StockDongleId"))

  def boot_thread():
    while not system_time_valid():
      print("Waiting for system time to become valid...")
      time.sleep(1)

    backup_frogpilot(build_metadata, params)

  threading.Thread(target=boot_thread, daemon=True).start()


def install_frogpilot(build_metadata, params):
  paths = [
    frogpilot_variables.ERROR_LOGS_PATH,
    frogpilot_variables.HD_LOGS_PATH,
    frogpilot_variables.KONIK_LOGS_PATH,
    frogpilot_variables.THEME_SAVE_PATH
  ]
  for path in paths:
    path.mkdir(parents=True, exist_ok=True)

  register_device(build_metadata, params)

  update_boot_logo(frogpilot=True)

  if build_metadata.channel == "FrogPilot-Development" and frogpilot_utilities.is_FrogsGoMoo():
    mount_options = frogpilot_utilities.run_cmd(["findmnt", "-n", "-o", "OPTIONS", "/persist"], "Successfully retrieved mount options", "Failed to retrieve mount options")
    frogpilot_utilities.run_cmd(["sudo", "mount", "-o", "remount,rw", "/persist"], "Successfully remounted /persist as read-write", "Failed to remount /persist")
    frogpilot_utilities.run_cmd(["sudo", "python3", frogpilot_variables.FROGS_GO_MOO_PATH], "Successfully ran frogsgomoo.py", "Failed to run frogsgomoo.py")
    frogpilot_utilities.run_cmd(["sudo", "mount", "-o", f"remount,{mount_options}", "/persist"], "Successfully restored /persist mount options", "Failed to restore /persist mount options")


def register_device(build_metadata, params):
  def register_thread():
    while not frogpilot_utilities.is_url_pingable(frogpilot_variables.FROGPILOT_API):
      time.sleep(60)

    payload = {
      "build_metadata": dataclasses.asdict(build_metadata),
      "device": HARDWARE.get_device_type(),
      "dongle_id": params.get("DongleId"),
    }

    try:
      response = requests.post(
        f"{frogpilot_variables.FROGPILOT_API}/register",
        json=payload,
        headers={"Content-Type": "application/json", "User-Agent": "frogpilot-api/1.0"},
        timeout=10,
      )
      response.raise_for_status()

      data = response.json()
      params.put("FrogPilotApiToken", data.get("api_token", ""))
      params.put("FrogPilotDongleId", data.get("frogpilot_dongle_id", ""))
    except Exception:
      pass

  threading.Thread(target=register_thread, daemon=True).start()


def uninstall_frogpilot():
  update_boot_logo(stock=True)

  HARDWARE.uninstall()


def update_boot_logo(frogpilot=False, stock=False):
  boot_logo_location = Path("/usr/comma/bg.jpg")

  if not boot_logo_location.is_file():
    print(f"Error: Boot logo file not found at {boot_logo_location}")
    return

  if frogpilot:
    target_logo = Path(BASEDIR) / "frogpilot/assets/other_images/frogpilot_boot_logo.jpg"
  elif stock:
    target_logo = Path(BASEDIR) / "frogpilot/assets/other_images/stock_bg.jpg"
  else:
    print('Error: Must specify either "frogpilot=True" or "stock=True"')
    return

  if not target_logo.is_file():
    print(f"Error: Target logo file not found at {target_logo}")
    return

  if boot_logo_location.read_bytes() != target_logo.read_bytes():
    mount_options = frogpilot_utilities.run_cmd(["findmnt", "-n", "-o", "OPTIONS", "/"], "Successfully retrieved mount options", "Failed to retrieve mount options")
    frogpilot_utilities.run_cmd(["sudo", "mount", "-o", "remount,rw", "/"], "Successfully remounted / as read-write", "Failed to remount /")
    frogpilot_utilities.run_cmd(["sudo", "cp", target_logo, boot_logo_location], "Successfully replaced boot logo", "Failed to replace boot logo")
    frogpilot_utilities.run_cmd(["sudo", "mount", "-o", f"remount,{mount_options}", "/"], "Successfully restored / mount options", "Failed to restore / mount options")


def update_maps(now, params, manual_update=False, progress_cb=None, cancel_check=None):
  maps_selected = params.get("MapsSelected")
  if not maps_selected:
    return "no_selection"

  day = now.day
  is_first = day == 1
  is_sunday = now.weekday() == 6
  schedule = params.get("PreferredSchedule")

  maps_downloaded = frogpilot_variables.MAPS_PATH.exists()
  if maps_downloaded and (schedule == 0 or (schedule == 1 and not is_sunday) or (schedule == 2 and not is_first)) and not manual_update:
    return "skipped"

  suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
  todays_date = now.strftime(f"%B {day}{suffix}, %Y")

  if maps_downloaded and params.get("LastMapsUpdate") == todays_date and not manual_update:
    return "already_updated"

  pm = messaging.PubMaster(["mapdIn"])
  sm = messaging.SubMaster(["mapdExtendedOut"])

  time.sleep(1)

  msg = messaging.new_message("mapdIn")
  msg.mapdIn.type = MAPDIN_DOWNLOAD
  msg.mapdIn.str = maps_selected
  pm.send("mapdIn", msg)
  cloudlog.info(f"update_maps: sent download request for {maps_selected!r} (manual={manual_update})")

  sent_at = time.monotonic()
  started = False
  cancelled = False
  cancel_sent = False
  timed_out = False
  while True:
    sm.update(1000)

    if cancel_check is not None and cancel_check() and not cancel_sent:
      cancel_msg = messaging.new_message("mapdIn")
      cancel_msg.mapdIn.type = MAPDIN_CANCEL_DOWNLOAD
      pm.send("mapdIn", cancel_msg)
      cancel_sent = True
      cloudlog.info("update_maps: cancel requested")

    if sm.updated["mapdExtendedOut"]:
      progress = sm["mapdExtendedOut"].downloadProgress

      if progress_cb is not None:
        progress_cb(progress)

      if progress.active:
        started = True

      if progress.cancelled:
        cancelled = True

      if not progress.active and (started or cancel_sent):
        break

    if not started and not cancel_sent and (time.monotonic() - sent_at) > MAPD_DOWNLOAD_STARTED_TIMEOUT:
      cloudlog.warning(f"update_maps: mapd did not start download within {MAPD_DOWNLOAD_STARTED_TIMEOUT}s; aborting")
      timed_out = True
      break

  if not cancelled and not timed_out:
    params.put("LastMapsUpdate", todays_date)
    cloudlog.info(f"update_maps: completed, LastMapsUpdate={todays_date}")
    return "ok"

  cloudlog.info(f"update_maps: finished without writing timestamp (cancelled={cancelled}, timed_out={timed_out})")
  if timed_out:
    return "timed_out"
  return "cancelled"


def update_openpilot(thread_manager, params):
  def update_available():
    frogpilot_utilities.run_cmd(["pkill", "-SIGUSR1", "-f", "system.updated.updated"], "Checking for updates...", "Failed to check for update...", report=False)

    while params.get("UpdaterState") != "checking...":
      time.sleep(1)

    while params.get("UpdaterState") == "checking...":
      time.sleep(1)

    if not params.get_bool("UpdaterFetchAvailable"):
      return False

    while params.get_bool("IsOnroad") or thread_manager.is_thread_alive("lock_doors"):
      time.sleep(60)

    frogpilot_utilities.run_cmd(["pkill", "-SIGHUP", "-f", "system.updated.updated"], "Update available, downloading...", "Failed to download update...", report=False)

    while not params.get_bool("UpdateAvailable"):
      time.sleep(60)

    return True

  if params.get("UpdaterState") != "idle":
    return

  while params.get_bool("IsOnroad") or thread_manager.is_thread_alive("lock_doors"):
    time.sleep(60)

  if not update_available():
    return

  while True:
    if not update_available():
      break

  HARDWARE.reboot()
