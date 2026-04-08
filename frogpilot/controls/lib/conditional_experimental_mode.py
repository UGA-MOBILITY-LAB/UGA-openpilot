#!/usr/bin/env python3
import numpy as np

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.realtime import DT_MDL

from openpilot.frogpilot.common import frogpilot_variables

CEStatus = {
  "OFF": 0,              # Off
  "USER_DISABLED": 1,    # "Experimental Mode" disabled by user
  "USER_OVERRIDDEN": 2,  # "Experimental Mode" enabled by user
  "CURVATURE": 3,        # Road curvature condition
  "LEAD": 4,             # Slower lead vehicle condition
  "SIGNAL": 5,           # Turn signal condition
  "SLOWDOWN": 6,         # Model-predicted slowdown condition
  "SPEED": 7,            # Speed condition
  "SPEED_LIMIT": 8,      # Speed limit controller condition
  "STOP_LIGHT": 9,       # Stop light or sign condition
}

class ConditionalExperimentalMode:
  def __init__(self, FrogPilotPlanner):
    self.frogpilot_planner = FrogPilotPlanner

    self.curvature_filter = FirstOrderFilter(0, 0.5, DT_MDL)
    self.slow_lead_filter = FirstOrderFilter(0, 1, DT_MDL)
    self.slowdown_filter = FirstOrderFilter(0, 0.5, DT_MDL)
    self.stop_light_filter = FirstOrderFilter(0, 0.5, DT_MDL)

    self.experimental_mode = False
    self.slowdown_detected = False
    self.stop_light_detected = False

  def update(self, v_ego, sm, frogpilot_toggles):
    if frogpilot_toggles.experimental_mode_via_press:
      self.status_value = self.frogpilot_planner.params_memory.get("ConditionalExperimentalStatus")
    else:
      self.status_value = CEStatus["OFF"]

    if self.status_value not in (CEStatus["USER_DISABLED"], CEStatus["USER_OVERRIDDEN"]) and not sm["carState"].standstill:
      self.update_conditions(v_ego, sm, frogpilot_toggles)
      self.experimental_mode = self.check_conditions(v_ego, sm, frogpilot_toggles)
      self.frogpilot_planner.params_memory.put("ConditionalExperimentalStatus", self.status_value)
    else:
      self.experimental_mode &= sm["carState"].standstill and self.frogpilot_planner.model_stopped
      self.experimental_mode &= self.status_value != CEStatus["USER_DISABLED"]
      self.experimental_mode |= self.status_value == CEStatus["USER_OVERRIDDEN"]

      self.stop_light_detected &= self.status_value not in (CEStatus["USER_DISABLED"], CEStatus["USER_OVERRIDDEN"])
      self.stop_light_filter.x = 0

  def check_conditions(self, v_ego, sm, frogpilot_toggles):
    if self.curve_detected and (not self.frogpilot_planner.frogpilot_following.following_lead or frogpilot_toggles.conditional_curves_lead) and frogpilot_toggles.conditional_curves:
      self.status_value = CEStatus["CURVATURE"]
      return True

    if self.slow_lead_detected and frogpilot_toggles.conditional_lead:
      self.status_value = CEStatus["LEAD"]
      return True

    if (sm["carState"].leftBlinker or sm["carState"].rightBlinker) and v_ego < frogpilot_toggles.conditional_signal:
      desired_lane = self.frogpilot_planner.lane_width_left if sm["carState"].leftBlinker else self.frogpilot_planner.lane_width_right
      if desired_lane < frogpilot_toggles.lane_detection_width or not frogpilot_toggles.conditional_signal_lane_detection:
        self.status_value = CEStatus["SIGNAL"]
        return True

    if self.slowdown_detected and frogpilot_toggles.conditional_slowdown:
      self.status_value = CEStatus["SLOWDOWN"]
      return True

    if 1 <= v_ego < (frogpilot_toggles.conditional_limit_lead if self.frogpilot_planner.frogpilot_following.following_lead else frogpilot_toggles.conditional_limit):
      self.status_value = CEStatus["SPEED"]
      return True

    if self.frogpilot_planner.frogpilot_vcruise.slc.experimental_mode:
      self.status_value = CEStatus["SPEED_LIMIT"]
      return True

    if self.stop_light_detected and frogpilot_toggles.conditional_model_stop_time != 0:
      self.status_value = CEStatus["STOP_LIGHT"]
      return True

    return False

  def update_conditions(self, v_ego, sm, frogpilot_toggles):
    self.curve_detection(v_ego, frogpilot_toggles)
    self.slow_lead_detection(v_ego, frogpilot_toggles)
    self.slowdown_detection(v_ego, sm)
    self.stop_sign_and_light_detection(v_ego, sm, frogpilot_toggles.conditional_model_stop_time)

  def curve_detection(self, v_ego, frogpilot_toggles):
    self.curvature_filter.update(self.frogpilot_planner.driving_in_curve or self.frogpilot_planner.road_curvature_detected)
    self.curve_detected = self.curvature_filter.x >= frogpilot_variables.THRESHOLD and v_ego > frogpilot_variables.CRUISING_SPEED

  def slow_lead_detection(self, v_ego, frogpilot_toggles):
    if self.frogpilot_planner.tracking_lead:
      slower_lead = (v_ego - self.frogpilot_planner.lead_one.vLead) > frogpilot_variables.CRUISING_SPEED and frogpilot_toggles.conditional_slower_lead
      stopped_lead = self.frogpilot_planner.lead_one.vLead < 1 and frogpilot_toggles.conditional_stopped_lead

      self.slow_lead_filter.update(slower_lead or stopped_lead)
      self.slow_lead_detected = self.slow_lead_filter.x >= frogpilot_variables.THRESHOLD
    else:
      self.slow_lead_filter.x = 0
      self.slow_lead_detected = False

  def slowdown_detection(self, v_ego, sm):
    slowdown_detected = bool(np.any(np.asarray(sm["modelV2"].velocity.x)[1:] <= frogpilot_variables.SLOWDOWN_PERCENTAGE * v_ego))
    self.slowdown_filter.update(slowdown_detected and not self.curve_detected)
    self.slowdown_detected = self.slowdown_filter.x >= frogpilot_variables.THRESHOLD and v_ego > frogpilot_variables.CRUISING_SPEED

  def stop_sign_and_light_detection(self, v_ego, sm, model_time):
    stop_detected = (self.frogpilot_planner.model_length < v_ego * model_time) or self.frogpilot_planner.model_stopped
    self.stop_light_filter.update(stop_detected)
    self.stop_light_detected = self.stop_light_filter.x >= frogpilot_variables.THRESHOLD and not self.frogpilot_planner.tracking_lead
