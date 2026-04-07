#!/usr/bin/env python3
import dataclasses
import requests
import threading
import time

from pathlib import Path

from openpilot.common.basedir import BASEDIR
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.common.time_helpers import system_time_valid
from openpilot.system.hardware import HARDWARE

from openpilot.frogpilot.common import frogpilot_utilities, frogpilot_variables


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


def frogpilot_boot_functions(params):
  migrate_params_to_si(params)

  params_memory = Params(memory=True)

  frogpilot_variables.FrogPilotVariables()

  def boot_thread():
    while not system_time_valid():
      print("Waiting for system time to become valid...")
      time.sleep(1)

  threading.Thread(target=boot_thread, daemon=True).start()


def install_frogpilot(build_metadata, params):
  paths = [
  ]
  for path in paths:
    path.mkdir(parents=True, exist_ok=True)

  register_device(build_metadata, params)

  update_boot_logo(frogpilot=True)


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
