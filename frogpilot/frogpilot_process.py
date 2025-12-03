#!/usr/bin/env python3
import datetime
import time

from cereal import messaging
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL, Priority, Ratekeeper, config_realtime_process
from openpilot.common.time_helpers import system_time_valid

from openpilot.frogpilot.assets.theme_manager import THEME_COMPONENT_PARAMS, ThemeManager
from openpilot.frogpilot.common import frogpilot_backups, frogpilot_functions, frogpilot_utilities, frogpilot_variables
from openpilot.frogpilot.controls.frogpilot_planner import FrogPilotPlanner
from openpilot.frogpilot.system.frogpilot_stats import send_stats
from openpilot.frogpilot.system.frogpilot_tracking import FrogPilotTracking

ASSET_CHECK_RATE = (1 / DT_MDL)

def check_assets(theme_manager, thread_manager, params_memory, frogpilot_toggles):
  for asset_type, asset_param in THEME_COMPONENT_PARAMS.items():
    asset_to_download = params_memory.get(asset_param)
    if asset_to_download:
      thread_manager.run_with_lock(theme_manager.download_theme, (asset_type, asset_to_download, asset_param, frogpilot_toggles))

def transition_offroad(gps_position, thread_manager, time_validated, sm, params, frogpilot_toggles):
  if time_validated:
    thread_manager.run_with_lock(send_stats, (gps_position, params, frogpilot_toggles))

def transition_onroad(error_log):
  if error_log.is_file():
    error_log.unlink()

def update_checks(now, theme_manager, thread_manager, params, params_memory, frogpilot_toggles, boot_run=False):
  while not (frogpilot_utilities.is_url_pingable("https://github.com") or frogpilot_utilities.is_url_pingable("https://gitlab.com")):
    time.sleep(60)

  theme_manager.update_themes(frogpilot_toggles, boot_run)

  if frogpilot_toggles.automatic_updates:
    thread_manager.run_with_lock(frogpilot_functions.update_openpilot, (thread_manager, params))

  time.sleep(1)

def on_toggles_updated(theme_manager, thread_manager, time_validated, sm, params, frogpilot_toggles):
  new_toggles = frogpilot_variables.get_frogpilot_toggles(sm)

  theme_manager.update_active_theme(frogpilot_toggles)

  if time_validated:
    thread_manager.run_with_lock(frogpilot_backups.backup_toggles, (params))

  return new_toggles

def frogpilot_thread():
  rate_keeper = Ratekeeper(1 / DT_MDL, None)

  config_realtime_process(5, Priority.CTRL_LOW)

  pm = messaging.PubMaster(["frogpilotPlan"])
  sm = messaging.SubMaster(["carControl", "carState", "controlsState", "deviceState", "driverMonitoringState",
                            "frogpilotCarState", "frogpilotModelV2", "frogpilotSelfdriveState", "frogpilotUI",
                            "gpsLocation", "gpsLocationExternal", "liveParameters", "managerState", "mapdOut",
                            "modelV2", "onroadEvents", "pandaStates", "radarState", "selfdriveState"],
                            poll="modelV2")

  params = Params(return_defaults=True)
  params_memory = Params(memory=True)

  theme_manager = ThemeManager(params, params_memory)
  thread_manager = frogpilot_utilities.ThreadManager()

  frogpilot_toggles = frogpilot_variables.get_frogpilot_toggles()

  run_update_checks = False
  started_previously = False
  time_validated = False

  error_log = frogpilot_variables.ERROR_LOGS_PATH / "error.txt"
  if error_log.is_file():
    error_log.unlink()

  frogpilot_planner = FrogPilotPlanner(error_log, theme_manager)

  while True:
    sm.update()

    now = datetime.datetime.now(datetime.UTC)

    started = sm["deviceState"].started

    if not started and started_previously:
      transition_offroad(frogpilot_planner.gps_position, thread_manager, time_validated, sm, params, frogpilot_toggles)

      run_update_checks = True
    elif started and not started_previously:
      frogpilot_planner = FrogPilotPlanner(error_log)
      frogpilot_tracking = FrogPilotTracking(frogpilot_planner, frogpilot_toggles)

      transition_onroad(error_log)

    if started and sm.updated["modelV2"]:
      frogpilot_planner.update(now, time_validated, sm, frogpilot_toggles)
      frogpilot_planner.publish(theme_manager.theme_updated, sm, pm, frogpilot_toggles)

      frogpilot_tracking.update(now, time_validated, sm, frogpilot_toggles)
    elif not started:
      frogpilot_plan_send = messaging.new_message("frogpilotPlan")
      frogpilot_plan_send.frogpilotPlan.themeUpdated = theme_manager.theme_updated
      pm.send("frogpilotPlan", frogpilot_plan_send)

    started_previously = started

    if rate_keeper.frame % ASSET_CHECK_RATE == 0:
      check_assets(theme_manager, thread_manager, params_memory, frogpilot_toggles)

    if sm.updated["frogpilotUI"]:
      frogpilot_toggles = on_toggles_updated(theme_manager, thread_manager, time_validated, sm, params, frogpilot_toggles)

    run_update_checks |= now.second == 0 and (now.minute % 60 == 0 or (now.minute % 5 == 0 and frogpilot_utilities.is_FrogsGoMoo()))
    run_update_checks &= time_validated

    if run_update_checks:
      thread_manager.run_with_lock(update_checks, (now, theme_manager, thread_manager, params, params_memory, frogpilot_toggles))

      run_update_checks = False
    elif not time_validated:
      time_validated = system_time_valid()
      if not time_validated:
        continue

      thread_manager.run_with_lock(frogpilot_backups.backup_toggles, (params, True))
      thread_manager.run_with_lock(send_stats, (frogpilot_planner.gps_position, params, frogpilot_toggles))
      thread_manager.run_with_lock(update_checks, (now, theme_manager, thread_manager, params, params_memory, frogpilot_toggles, True))

    rate_keeper.keep_time()

def main():
  frogpilot_thread()

if __name__ == "__main__":
  main()
