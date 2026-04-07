#!/usr/bin/env python3
import dataclasses

from openpilot.common.params import Params
from openpilot.system.hardware import HARDWARE
from openpilot.system.version import get_build_metadata


def get_frogpilot_api_info():
  params = Params()

  api_token = params.get("FrogPilotApiToken")
  build_metadata = dataclasses.asdict(get_build_metadata())
  device_type = HARDWARE.get_device_type()
  dongle_id = params.get("FrogPilotDongleId")

  return api_token, build_metadata, device_type, dongle_id
