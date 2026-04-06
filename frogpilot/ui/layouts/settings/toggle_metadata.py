from dataclasses import dataclass
from enum import Enum

from openpilot.system.hardware.power_monitoring import VBATT_PAUSE_CHARGING
from openpilot.system.ui.lib.multilang import tr_noop

from openpilot.frogpilot.common import frogpilot_variables
from openpilot.frogpilot.system.ui.widgets.unit_conversion import UnitType


class WidgetType(str, Enum):
  BUTTON = "button_item"
  BUTTONS = "buttons_item"
  MULTIPLE_BUTTON = "multiple_button_item"
  TEXT = "text_item"
  TUNING_DUAL_PARAM_VALUE = "_tuning_dual_param_value_item"
  TUNING_MANAGE_TOGGLE = "_tuning_manage_toggle_item"
  TUNING_PARAM_VALUE = "_tuning_param_value_item"
  TUNING_PARAM_VALUE_BUTTON = "_tuning_param_value_button_item"
  TUNING_TOGGLE = "_tuning_toggle_item"


@dataclass(frozen=True)
class ButtonSpec:
  text: str
  action: str


@dataclass(frozen=True)
class MetadataItem:
  widget_type: WidgetType
  title: str
  description: str
  icon: str = ""
  param_key: str | None = None
  button_text: str | None = None
  buttons: tuple[ButtonSpec, ...] = ()
  options: tuple[str, ...] = ()
  child_param_keys: tuple[str, ...] = ()
  visible_state: str | tuple[str, ...] | None = None
  minimum: int | float | None = None
  maximum: int | float | None = None
  title_callback_method: str | None = None
  minimum_callback_method: str | None = None
  maximum_callback_method: str | None = None
  step: int | float = 1
  reboot: bool = False
  refreshes_visibility: bool = False
  button_callback_method: str | None = None
  unit: str | None = None
  unit_type: UnitType | None = None
  metric_title: str | None = None
  secondary: 'MetadataItem | None' = None
  value_map: dict[int | float, str] | None = None
  display_precision: int | None = None
  value_text: str | None = None


@dataclass(frozen=True)
class PanelMetadata:
  sections: dict[str, tuple[str, ...]]
  items: dict[str, MetadataItem]

  def __post_init__(self):
    flat = {}
    self._flatten(self.items, flat)
    object.__setattr__(self, 'items', flat)

  @staticmethod
  def _flatten(items, flat):
    for key, value in items.items():
      if isinstance(value, MetadataItem):
        flat[key] = value
      elif isinstance(value, tuple) and len(value) == 2:
        flat[key] = value[0]
        PanelMetadata._flatten(value[1], flat)


TOGGLE_METADATA: dict[str, PanelMetadata] = {
  "alerts_and_sounds": PanelMetadata(
    sections={
      "root": (
        "alert_volume_control",
        "frogpilot_alerts",
      ),

      "alert_volume_control": (
        "disengage_volume",
        "engage_volume",
        "prompt_volume",
        "prompt_distracted_volume",
        "refuse_volume",
        "warning_soft_volume",
        "warning_immediate_volume",
      ),

      "frogpilot_alerts": (
        "goat_scream",
        "green_light_alert",
        "lead_departing_alert",
        "loud_blindspot_alert",
        "speed_limit_changed_alert",
      ),
    },
    items={
      "alert_volume_control": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="AlertVolumeControl",
          title=tr_noop("Alert Volume Controller"),
          description=tr_noop("<b>Set how loud each type of openpilot alert is</b> to keep routine prompts from becoming distracting."),
          icon="frogpilot/assets/toggle_icons/icon_mute.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "disengage_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="DisengageVolume",
            title=tr_noop("Disengage Volume"),
            description=tr_noop("<b>Set the volume for alerts when openpilot disengages.</b><br><br>Examples include: \"Cruise Fault: Restart the Car\", \"Parking Brake Engaged\", \"Pedal Pressed\"."),
            minimum=0,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "engage_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="EngageVolume",
            title=tr_noop("Engage Volume"),
            description=tr_noop("<b>Set the volume for the chime when openpilot engages</b>, such as after pressing the \"RESUME\" or \"SET\" steering wheel buttons."),
            minimum=0,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "prompt_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="PromptVolume",
            title=tr_noop("Prompt Volume"),
            description=tr_noop("<b>Set the volume for prompts that need attention.</b><br><br>Examples include: \"Car Detected in Blindspot\", \"Steering Temporarily Unavailable\", \"Turn Exceeds Steering Limit\"."),
            minimum=0,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "prompt_distracted_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="PromptDistractedVolume",
            title=tr_noop("Prompt Distracted Volume"),
            description=tr_noop("<b>Set the volume for prompts when openpilot detects driver distraction or unresponsiveness.</b><br><br>Examples include: \"Pay Attention\", \"Touch Steering Wheel\"."),
            minimum=0,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "refuse_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="RefuseVolume",
            title=tr_noop("Refuse Volume"),
            description=tr_noop("<b>Set the volume for alerts when openpilot refuses to engage.</b><br><br>Examples include: \"Brake Hold Active\", \"Door Open\", \"Seatbelt Unlatched\"."),
            minimum=0,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "warning_soft_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="WarningSoftVolume",
            title=tr_noop("Warning Soft Volume"),
            description=tr_noop("<b>Set the volume for softer warnings about potential risks.</b><br><br>Examples include: \"BRAKE! Risk of Collision\", \"Steering Temporarily Unavailable\"."),
            minimum=25,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={0: "Muted", 101: "Auto"},
          ),

          "warning_immediate_volume": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="WarningImmediateVolume",
            title=tr_noop("Warning Immediate Volume"),
            description=tr_noop("<b>Set the volume for the loudest warnings that require urgent attention.</b><br><br>Examples include: \"DISENGAGE IMMEDIATELY — Driver Distracted\", \"DISENGAGE IMMEDIATELY — Driver Unresponsive\"."),
            minimum=25,
            maximum=101,
            button_text=tr_noop("Test"),
            button_callback_method="_test_alert",
            unit="%",
            value_map={101: "Auto"},
          ),
        },
      ),

      "frogpilot_alerts": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="CustomAlerts",
          title=tr_noop("FrogPilot Alerts"),
          description=tr_noop("<b>Optional FrogPilot alerts</b> that highlight driving events in a more noticeable way."),
          icon="frogpilot/assets/toggle_icons/icon_green_light.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "goat_scream": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="GoatScream",
            title=tr_noop("Goat Scream"),
            description=tr_noop("<b>Play the infamous \"Goat Scream\" when the steering controller reaches its limit.</b> Based on the \"Turn Exceeds Steering Limit\" event."),
          ),

          "green_light_alert": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="GreenLightAlert",
            title=tr_noop("Green Light Alert"),
            description=tr_noop("<b>Play an alert when the model predicts a red light has turned green.</b><br><br><i><b>Disclaimer</b>: openpilot does not explicitly detect traffic lights. This alert is based on end-to-end model predictions from camera input and may trigger even when the light has not changed.</i>"),
          ),

          "lead_departing_alert": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="LeadDepartingAlert",
            title=tr_noop("Lead Departing Alert"),
            description=tr_noop("<b>Play an alert when the lead vehicle departs from a stop.</b>"),
          ),

          "loud_blindspot_alert": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="LoudBlindspotAlert",
            title=tr_noop("Loud \"Car Detected in Blindspot\" Alert"),
            description=tr_noop("<b>Play a louder alert if a vehicle is in the blind spot when attempting to change lanes.</b> Based on the \"Car Detected in Blindspot\" event."),
            visible_state="_has_bsm_enabled",
          ),

          "speed_limit_changed_alert": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="SpeedLimitChangedAlert",
            title=tr_noop("Speed Limit Changed Alert"),
            description=tr_noop("<b>Play an alert when the posted speed limit changes.</b>"),
            child_param_keys=("ShowSpeedLimits", "SpeedLimitController"),
          ),
        },
      ),
    },
  ),

  "appearance": PanelMetadata(
    sections={
      "root": (
        "advanced_custom_ui",
        "custom_ui",
        "model_ui",
        "navigation_ui",
        "quality_of_life",
      ),

      "advanced_custom_ui": (
        "hide_speed",
        "hide_lead_marker",
        "hide_max_speed",
        "hide_alerts",
        "hide_speed_limit",
        "wheel_speed",
      ),

      "custom_ui": (
        "acceleration_path",
        "adjacent_path",
        "blind_spot_path",
        "compass",
        "onroad_distance_button",
        "pedals_on_ui",
        "rotating_wheel",
      ),

      "model_ui": (
        "dynamic_path_width",
        "lane_lines_width",
        "path_edge_width",
        "path_width",
        "road_edges_width",
      ),

      "navigation_ui": (
        "road_name_ui",
        "show_speed_limits",
        "slc_mapbox_filler_visual",
        "use_vienna",
      ),

      "quality_of_life": (
        "camera_view",
        "driver_camera",
        "stopped_timer",
      ),
    },
    items={
      "advanced_custom_ui": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="AdvancedCustomUI",
          title=tr_noop("Advanced UI Controls"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Advanced visual changes</b> to fine-tune how the driving screen looks."),
          icon="frogpilot/assets/toggle_icons/icon_advanced_device.png",
        ),
        {
          "hide_speed": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HideSpeed",
            title=tr_noop("Hide Current Speed"),
            description=tr_noop("<b>Hide the current speed</b> from the driving screen."),
          ),

          "hide_lead_marker": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HideLeadMarker",
            title=tr_noop("Hide Lead Marker"),
            description=tr_noop("<b>Hide the lead-vehicle marker</b> from the driving screen."),
            visible_state="_has_openpilot_longitudinal",
          ),

          "hide_max_speed": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HideMaxSpeed",
            title=tr_noop("Hide Max Speed"),
            description=tr_noop("<b>Hide the max speed</b> from the driving screen."),
          ),

          "hide_alerts": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HideAlerts",
            title=tr_noop("Hide Non-Critical Alerts"),
            description=tr_noop("<b>Hide non-critical alerts</b> from the driving screen."),
          ),

          "hide_speed_limit": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HideSpeedLimit",
            title=tr_noop("Hide Speed Limits"),
            description=tr_noop("<b>Hide posted speed limits</b> from the driving screen."),
            visible_state="_hide_speed_limit_visible",
          ),

          "wheel_speed": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="WheelSpeed",
            title=tr_noop("Use Wheel Speed"),
            description=tr_noop("<b>Use the vehicle's wheel speed</b> instead of the cluster speed. This is purely a visual change and doesn't impact how openpilot drives!"),
          ),
        },
      ),

      "custom_ui": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="CustomUI",
          title=tr_noop("Driving Screen Widgets"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Custom FrogPilot widgets</b> for the driving screen."),
          icon="selfdrive/assets/icons/calibration.png",
        ),
        {
          "acceleration_path": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="AccelerationPath",
            title=tr_noop("Acceleration Path"),
            description=tr_noop("<b>Color the driving path by planned acceleration and braking.</b>"),
            visible_state="_has_openpilot_longitudinal",
          ),

          "adjacent_path": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="AdjacentPath",
            title=tr_noop("Adjacent Lanes"),
            description=tr_noop("<b>Show the driving paths for the left and right lanes.</b>"),
          ),

          "blind_spot_path": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="BlindSpotPath",
            title=tr_noop("Blind Spot Path"),
            description=tr_noop("<b>Show a red path when a vehicle is in that lane's blind spot.</b>"),
            visible_state="_has_bsm_enabled",
          ),

          "compass": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="Compass",
            title=tr_noop("Compass"),
            description=tr_noop("<b>Show the current driving direction</b> with a simple on-screen compass."),
          ),

          "onroad_distance_button": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="OnroadDistanceButton",
            title=tr_noop("Driving Personality Button"),
            description=tr_noop("<b>Control and view the current driving personality</b> via a driving screen widget."),
            visible_state="_has_openpilot_longitudinal",
          ),

          "pedals_on_ui": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="PedalsOnUI",
            title=tr_noop("Gas / Brake Pedal Indicators"),
            description=tr_noop("<b>On-screen gas and brake indicators.</b><br><br><b>Dynamic</b>: Opacity changes according to how much openpilot is accelerating or braking<br><b>Static</b>: Full when active, dim when not"),
            options=(
              tr_noop("Dynamic"),
              tr_noop("Static"),
            ),
            child_param_keys=(
              "DynamicPedalsOnUI",
              "StaticPedalsOnUI",
            ),
            visible_state="_has_openpilot_longitudinal",
          ),

          "rotating_wheel": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="RotatingWheel",
            title=tr_noop("Rotating Steering Wheel"),
            description=tr_noop("<b>Rotate the driving screen wheel</b> with the physical steering wheel."),
          ),
        },
      ),

      "model_ui": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="ModelUI",
          title=tr_noop("Model UI"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Model visualizations</b> for the driving path, lane lines, path edges, and road edges."),
          icon="frogpilot/assets/toggle_icons/icon_road.png",
        ),
        {
          "dynamic_path_width": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="DynamicPathWidth",
            title=tr_noop("Dynamic Path Width"),
            description=tr_noop("<b>Change the path width based on engagement.</b><br><br><b>Fully Engaged</b>: 100%<br><b>Always On Lateral</b>: 75%<br><b>Disengaged</b>: 50%"),
          ),

          "lane_lines_width": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LaneLinesWidth",
            title=tr_noop("Lane Lines Width"),
            description=tr_noop("<b>Set the lane-line thickness.</b><br><br>Default matches the MUTCD lane-line width standard of 4 inches."),
            minimum=0,
            maximum=24,
            unit=" inches",
            value_map={0: "Off"},
          ),

          "path_edge_width": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="PathEdgeWidth",
            title=tr_noop("Path Edges Width"),
            description=tr_noop("<b>Set the driving-path edge width</b> that represents different driving modes and statuses.<br><br>Default is 20% of the total path width.<br><br>Color Guide:<br><br>- <b>Light Blue</b>: Always On Lateral<br>- <b>Green</b>: Default<br>- <b>Orange</b>: Experimental Mode<br>- <b>Red</b>: Traffic Mode<br>- <b>Yellow</b>: Conditional Experimental Mode overridden"),
            minimum=0,
            maximum=100,
            unit="%",
            value_map={0: "Off"},
          ),

          "path_width": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="PathWidth",
            title=tr_noop("Path Width"),
            description=tr_noop("<b>Set the driving-path width.</b><br><br>Default (6.1 feet) matches the width of a 2019 Lexus ES 350."),
            minimum=0,
            maximum=10,
            step=0.1,
            unit=" feet",
            value_map={0: "Off"},
          ),

          "road_edges_width": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="RoadEdgesWidth",
            title=tr_noop("Road Edges Width"),
            description=tr_noop("<b>Set the road-edge thickness.</b><br><br>Default matches half of the MUTCD lane-line width standard of 4 inches."),
            minimum=0,
            maximum=24,
            unit=" inches",
            value_map={0: "Off"},
          ),
        },
      ),

      "navigation_ui": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="NavigationUI",
          title=tr_noop("Navigation Widgets"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Speed limits, and other navigation widgets.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_map.png",
        ),
        {
          "road_name_ui": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="RoadNameUI",
            title=tr_noop("Road Name"),
            description=tr_noop("<b>Display the road name at the bottom of the driving screen</b> using data from \"OpenStreetMap (OSM)\"."),
          ),

          "show_speed_limits": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ShowSpeedLimits",
            title=tr_noop("Show Speed Limits"),
            description=tr_noop("<b>Show speed limits</b> in the top-left corner of the driving screen. Uses data from the car's dashboard (if supported) and \"OpenStreetMap (OSM)\"."),
            visible_state="_show_speed_limits_visible",
            refreshes_visibility=True,
          ),

          "slc_mapbox_filler_visual": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="SLCMapboxFiller",
            title=tr_noop("Show Speed Limits from Mapbox"),
            description=tr_noop("<b>Use Mapbox speed-limit data when no other source is available.</b>"),
            visible_state="_slc_mapbox_visible",
          ),

          "use_vienna": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="UseVienna",
            title=tr_noop("Use Vienna-Style Speed Signs"),
            description=tr_noop("<b>Show Vienna-style (EU) speed-limit signs</b> instead of MUTCD (US)."),
            child_param_keys=("ShowSpeedLimits", "SpeedLimitController"),
          ),
        },
      ),

      "quality_of_life": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="QOLVisuals",
          title=tr_noop("Quality of Life"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Miscellaneous visual changes</b> to fine-tune how the driving screen looks."),
          icon="frogpilot/assets/toggle_icons/icon_quality_of_life.png",
        ),
        {
          "camera_view": MetadataItem(
            widget_type=WidgetType.MULTIPLE_BUTTON,
            param_key="CameraView",
            title=tr_noop("Camera View"),
            description=tr_noop("<b>Select the active camera view.</b> This is purely a visual change and doesn't impact how openpilot drives!"),
            options=(
              tr_noop("Auto"),
              tr_noop("Driver"),
              tr_noop("Standard"),
              tr_noop("Wide"),
            ),
          ),

          "driver_camera": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="DriverCamera",
            title=tr_noop("Show Driver Camera When In Reverse"),
            description=tr_noop("<b>Show the driver camera feed</b> when the vehicle is in reverse."),
          ),

          "stopped_timer": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="StoppedTimer",
            title=tr_noop("Stopped Timer"),
            description=tr_noop("<b>Show a timer when stopped</b> in place of the current speed to indicate how long the vehicle has been stopped."),
          ),
        },
      ),
    },
  ),

  "data": PanelMetadata(
    sections={"root": ()},
    items={},
  ),

  "device_controls": PanelMetadata(
    sections={
      "root": (
        "device_management",
        "screen_management",
      ),

      "device_management": (
        "device_shutdown",
        "no_logging",
        "no_uploads",
        "higher_bitrate",
        "low_voltage_shutdown",
        "increase_thermal_limits",
        "use_konik_server",
      ),

      "screen_management": (
        "screen_brightness_offroad",
        "screen_brightness_onroad",
        "screen_recorder",
        "screen_timeout_offroad",
        "screen_timeout_onroad",
        "standby_mode",
      ),
    },
    items={
      "device_management": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="DeviceManagement",
          title=tr_noop("Device Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Settings that control how the device runs, powers off, and manages driving data.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_device.png",
        ),
        {
          "device_shutdown": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="DeviceShutdown",
            title=tr_noop("Device Shutdown Timer"),
            description=tr_noop("<b>Keep the device on for the set amount of time after a drive</b> before it shuts down automatically."),
            minimum=0,
            maximum=33,
            value_map={
              0: "5 mins",
              1: "15 mins",
              2: "30 mins",
              3: "45 mins",
              4: "1 hour",
              5: "2 hours",
              6: "3 hours",
              7: "4 hours",
              8: "5 hours",
              9: "6 hours",
              10: "7 hours",
              11: "8 hours",
              12: "9 hours",
              13: "10 hours",
              14: "11 hours",
              15: "12 hours",
              16: "13 hours",
              17: "14 hours",
              18: "15 hours",
              19: "16 hours",
              20: "17 hours",
              21: "18 hours",
              22: "19 hours",
              23: "20 hours",
              24: "21 hours",
              25: "22 hours",
              26: "23 hours",
              27: "24 hours",
              28: "25 hours",
              29: "26 hours",
              30: "27 hours",
              31: "28 hours",
              32: "29 hours",
              33: "30 hours",
            },
          ),

          "no_logging": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="NoLogging",
            title=tr_noop("Disable Logging"),
            description=tr_noop("<b>WARNING: This will prevent your drives from being recorded and all data will be unobtainable!</b><br><br><b>Prevent the device from saving driving data.</b>"),
          ),

          "no_uploads": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="NoUploads",
            title=tr_noop("Disable Uploads"),
            description=tr_noop("<b>WARNING: This will prevent your drives from being uploaded to <b>comma connect</b> which will impact debugging and official support from comma!</b><br><br><b>Prevent the device from uploading driving data.</b>"),
            options=(tr_noop("Disable Onroad Only"),),
            child_param_keys=("DisableOnroadUploads",),
            refreshes_visibility=True,
          ),

          "higher_bitrate": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HigherBitrate",
            title=tr_noop("High-Quality Recording"),
            description=tr_noop("<b>Save drive footage in higher video quality.</b>"),
            reboot=True,
            visible_state="_higher_bitrate_visible",
          ),

          "low_voltage_shutdown": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LowVoltageShutdown",
            title=tr_noop("Low-Voltage Cutoff"),
            description=tr_noop("<b>While parked, if the battery voltage falls below the set level, the device shuts down</b> to prevent excessive battery drain."),
            minimum=VBATT_PAUSE_CHARGING,
            maximum=frogpilot_variables.LOW_VOLTAGE_SHUTDOWN_MAX,
            step=0.1,
            unit=" volts",
          ),

          "increase_thermal_limits": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="IncreaseThermalLimits",
            title=tr_noop("Raise Temperature Limits"),
            description=tr_noop("<b>WARNING: Running at higher temperatures may damage your device!</b><br><br><b>Allow the device to run at higher temperatures</b> before throttling or shutting down. Use only if you understand the risks!"),
          ),

          "use_konik_server": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="UseKonikServer",
            title=tr_noop("Use Konik Server"),
            description=tr_noop("<b>Upload driving data to \"stable.konik.ai\" instead of \"connect.comma.ai\".</b>"),
            reboot=True,
          ),
        },
      ),

      "screen_management": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="ScreenManagement",
          title=tr_noop("Screen Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Settings that control screen brightness, screen recording, and timeout duration.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_light.png",
        ),
        {
          "screen_brightness_offroad": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="ScreenBrightness",
            title=tr_noop("Screen Brightness (Offroad)"),
            description=tr_noop("<b>The screen brightness while not driving.</b>"),
            minimum=1,
            maximum=101,
            unit="%",
            value_map={0: "Screen Off", 101: "Auto"},
          ),

          "screen_brightness_onroad": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="ScreenBrightnessOnroad",
            title=tr_noop("Screen Brightness (Onroad)"),
            description=tr_noop("<b>The screen brightness while driving.</b>"),
            minimum=0,
            maximum=101,
            unit="%",
            value_map={0: "Screen Off", 101: "Auto"},
          ),

          "screen_recorder": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ScreenRecorder",
            title=tr_noop("Screen Recorder"),
            description=tr_noop("<b>Add a button to the driving screen to record the display.</b>"),
          ),

          "screen_timeout_offroad": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="ScreenTimeout",
            title=tr_noop("Screen Timeout (Offroad)"),
            description=tr_noop("<b>How long the screen stays on after being tapped while not driving.</b>"),
            minimum=5,
            maximum=60,
            step=5,
            unit=" seconds",
          ),

          "screen_timeout_onroad": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="ScreenTimeoutOnroad",
            title=tr_noop("Screen Timeout (Onroad)"),
            description=tr_noop("<b>How long the screen stays on after being tapped while driving.</b>"),
            minimum=5,
            maximum=60,
            step=5,
            unit=" seconds",
          ),

          "standby_mode": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="StandbyMode",
            title=tr_noop("Standby Mode"),
            description=tr_noop("<b>Turn the screen off while driving and automatically wake it up for alerts or engagement state changes.</b>"),
          ),
        },
      ),
    },
  ),

  "driving_model": PanelMetadata(
    sections={
      "root": (
        "automatically_download_models",
        "delete_model",
        "download_model",
        "model_randomizer",
        "manage_blacklisted_models",
        "manage_scores",
        "select_model",
      ),
    },
    items={
      "automatically_download_models": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="AutomaticallyDownloadModels",
        title=tr_noop("Automatically Download New Models"),
        description=tr_noop("<b>Automatically download new driving models</b> as they become available."),
      ),

      "delete_model": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Delete Driving Models"),
        description=tr_noop("<b>Delete downloaded driving models</b> to free up storage space."),
        buttons=(
          ButtonSpec(text=tr_noop("DELETE"), action="delete"),
          ButtonSpec(text=tr_noop("DELETE ALL"), action="delete_all"),
        ),
      ),

      "download_model": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Download Driving Models"),
        description=tr_noop("<b>Manually download driving models</b> to the device."),
        buttons=(
          ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
          ButtonSpec(text=tr_noop("DOWNLOAD ALL"), action="download_all"),
        ),
      ),

      "select_model": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="DrivingModel",
        title=tr_noop("Select Driving Model"),
        button_text=tr_noop("SELECT"),
        description=tr_noop("<b>Choose which driving model openpilot uses.</b>"),
        reboot=True,
        visible_state="_no_model_randomizer",
      ),

      "model_randomizer": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="ModelRandomizer",
        title=tr_noop("Model Randomizer"),
        description=tr_noop("<b>Select a random driving model each drive</b> and use feedback prompts at the end of the drive to help find the model that best suits you!"),
        refreshes_visibility=True,
      ),

      "manage_blacklisted_models": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Manage Model Blacklist"),
        description=tr_noop("<b>Add or remove driving models from the \"Model Randomizer\" blacklist.</b>"),
        buttons=(
          ButtonSpec(text=tr_noop("ADD"), action="add"),
          ButtonSpec(text=tr_noop("REMOVE"), action="remove"),
          ButtonSpec(text=tr_noop("REMOVE ALL"), action="remove_all"),
        ),
        visible_state="_has_model_randomizer",
      ),

      "manage_scores": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Manage Model Ratings"),
        description=tr_noop("<b>View or reset saved model ratings</b> used by the \"Model Randomizer\"."),
        buttons=(
          ButtonSpec(text=tr_noop("RESET"), action="reset"),
          ButtonSpec(text=tr_noop("VIEW"), action="view"),
        ),
        visible_state="_has_model_randomizer",
      ),
    },
  ),

  "frogpilot_panel": PanelMetadata(
    sections={
      "root": (
        "tuning_level",
        "alerts_and_sounds",
        "driving_controls",
        "navigation",
        "system_settings",
        "theme_and_appearance",
        "vehicle_settings",
      ),
    },
    items={
      "tuning_level": MetadataItem(
        widget_type=WidgetType.MULTIPLE_BUTTON,
        param_key="TuningLevel",
        title=tr_noop("Tuning Level"),
        description=tr_noop("Choose your tuning level. Lower levels keep it simple; higher levels unlock more toggles for finer control.\n\nMinimal - Ideal for those who prefer simplicity or ease of use\nStandard - Recommended for most users for a balanced experience\nAdvanced - Fine-tuning for experienced users\nDeveloper - Highly customizable settings for seasoned enthusiasts"),
        icon="frogpilot/assets/toggle_icons/icon_tuning.png",
        options=(
          tr_noop("Minimal"),
          tr_noop("Standard"),
          tr_noop("Advanced"),
          tr_noop("Developer"),
        ),
      ),

      "alerts_and_sounds": MetadataItem(
        widget_type=WidgetType.BUTTON,
        title=tr_noop("Alerts and Sounds"),
        description=tr_noop("<b>Adjust alert volumes and enable custom notifications.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_sound.png",
        button_text=tr_noop("MANAGE"),
      ),

      "driving_controls": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Driving Controls"),
        description=tr_noop("<b>Fine-tune custom FrogPilot acceleration, braking, and steering controls.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_steering.png",
        buttons=(
          ButtonSpec(text=tr_noop("DRIVING MODEL"), action="driving_model"),
          ButtonSpec(text=tr_noop("GAS / BRAKE"), action="gas_brake"),
          ButtonSpec(text=tr_noop("STEERING"), action="steering"),
        ),
      ),

      "navigation": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Navigation"),
        description=tr_noop("<b>Download map data for the \"Speed Limit Controller\".</b>"),
        icon="frogpilot/assets/toggle_icons/icon_navigate.png",
        buttons=(
          ButtonSpec(text=tr_noop("MAP DATA"), action="map_data"),
          ButtonSpec(text=tr_noop("NAVIGATION"), action="navigation"),
        ),
      ),

      "system_settings": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("System Settings"),
        description=tr_noop("<b>Manage backups, device settings, screen options, storage, and tools to keep FrogPilot running smoothly.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_system.png",
        buttons=(
          ButtonSpec(text=tr_noop("DATA"), action="data"),
          ButtonSpec(text=tr_noop("DEVICE CONTROLS"), action="device_controls"),
          ButtonSpec(text=tr_noop("UTILITIES"), action="utilities"),
        ),
      ),

      "theme_and_appearance": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Theme and Appearance"),
        description=tr_noop("<b>Customize the look of the driving screen and interface, including themes!</b>"),
        icon="frogpilot/assets/toggle_icons/icon_display.png",
        buttons=(
          ButtonSpec(text=tr_noop("APPEARANCE"), action="appearance"),
          ButtonSpec(text=tr_noop("THEME"), action="theme"),
        ),
      ),

      "vehicle_settings": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Vehicle Settings"),
        description=tr_noop("<b>Configure car-specific options and steering wheel button mappings.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_vehicle.png",
        buttons=(
          ButtonSpec(text=tr_noop("VEHICLE SETTINGS"), action="vehicle_settings"),
          ButtonSpec(text=tr_noop("WHEEL CONTROLS"), action="wheel_controls"),
        ),
      ),
    },
  ),

  "gas_brake": PanelMetadata(
    sections={
      "root": (
        "advanced_longitudinal_tune",
        "conditional_experimental",
        "curve_speed_controller",
        "custom_personalities",
        "longitudinal_tune",
        "quality_of_life",
        "speed_limit_controller",
      ),

      "advanced_longitudinal_tune": (
        "longitudinal_actuator_delay",
        "max_desired_acceleration",
        "start_accel",
        "stop_accel",
        "stopping_decel_rate",
        "v_ego_starting",
        "v_ego_stopping",
      ),

      "conditional_experimental": (
        "ce_speed",
        "ce_curves",
        "ce_stop_lights",
        "ce_lead",
        "ce_model_stop_time",
        "ce_slowdown",
        "ce_signal_speed",
        "show_cem_status",
      ),

      "curve_speed_controller": (
        "calibrated_lateral_acceleration",
        "calibration_progress",
        "reset_curve_data",
        "show_csc_status",
      ),

      "custom_personalities": (
        "traffic_personality_profile",
        "aggressive_personality_profile",
        "standard_personality_profile",
        "relaxed_personality_profile",
      ),

      "traffic_personality": (
        "traffic_follow",
        "traffic_jerk_acceleration",
        "traffic_jerk_deceleration",
        "traffic_jerk_danger",
        "traffic_jerk_speed_decrease",
        "traffic_jerk_speed",
        "reset_traffic_personality",
      ),

      "aggressive_personality": (
        "aggressive_follow",
        "aggressive_jerk_acceleration",
        "aggressive_jerk_deceleration",
        "aggressive_jerk_danger",
        "aggressive_jerk_speed_decrease",
        "aggressive_jerk_speed",
        "reset_aggressive_personality",
      ),

      "standard_personality": (
        "standard_follow",
        "standard_jerk_acceleration",
        "standard_jerk_deceleration",
        "standard_jerk_danger",
        "standard_jerk_speed_decrease",
        "standard_jerk_speed",
        "reset_standard_personality",
      ),

      "relaxed_personality": (
        "relaxed_follow",
        "relaxed_jerk_acceleration",
        "relaxed_jerk_deceleration",
        "relaxed_jerk_danger",
        "relaxed_jerk_speed_decrease",
        "relaxed_jerk_speed",
        "reset_relaxed_personality",
      ),

      "longitudinal_tune": (
        "acceleration_profile",
        "deceleration_profile",
        "human_acceleration",
        "human_following",
        "human_lane_changes",
        "lead_detection_threshold",
        "taco_tune",
      ),

      "quality_of_life": (
        "custom_cruise",
        "custom_cruise_long",
        "force_stops",
        "increased_stopped_distance",
        "map_gears",
        "set_speed_offset",
        "reverse_cruise",
        "weather_presets",
      ),

      "weather_presets": (
        "low_visibility_offsets",
        "rain_offsets",
        "rain_storm_offsets",
        "snow_offsets",
        "set_weather_key",
      ),

      "weather_low_visibility": (
        "increase_following_low_visibility",
        "increased_stopped_distance_low_visibility",
        "reduce_acceleration_low_visibility",
        "reduce_lateral_acceleration_low_visibility",
      ),

      "weather_rain": (
        "increase_following_rain",
        "increased_stopped_distance_rain",
        "reduce_acceleration_rain",
        "reduce_lateral_acceleration_rain",
      ),

      "weather_rain_storm": (
        "increase_following_rain_storm",
        "increased_stopped_distance_rain_storm",
        "reduce_acceleration_rain_storm",
        "reduce_lateral_acceleration_rain_storm",
      ),

      "weather_snow": (
        "increase_following_snow",
        "increased_stopped_distance_snow",
        "reduce_acceleration_snow",
        "reduce_lateral_acceleration_snow",
      ),

      "speed_limit_controller": (
        "slc_fallback",
        "slc_override",
        "slc_priority",
        "slc_offsets",
        "slc_qol",
        "slc_visuals",
      ),

      "slc_offsets": (
        "offset_1",
        "offset_2",
        "offset_3",
        "offset_4",
        "offset_5",
        "offset_6",
        "offset_7",
      ),

      "slc_qol": (
        "set_speed_limit",
        "slc_confirmation",
        "slc_lookahead_higher",
        "slc_lookahead_lower",
        "slc_mapbox_filler",
      ),

      "slc_visuals": (
        "show_slc_offset",
        "speed_limit_sources",
      ),
    },
    items={
      "advanced_longitudinal_tune": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="AdvancedLongitudinalTune",
          title=tr_noop("Advanced Longitudinal Tuning"),
          description=tr_noop("<b>Advanced acceleration and braking control changes</b> to fine-tune how openpilot drives."),
          icon="frogpilot/assets/toggle_icons/icon_advanced_longitudinal_tune.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "longitudinal_actuator_delay": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LongitudinalActuatorDelay",
            title=tr_noop("Actuator Delay"),
            description=tr_noop("<b>The time between openpilot's throttle or brake command and the vehicle's response.</b> Increase if the vehicle feels slow to react; decrease if it feels too eager or overshoots."),
            title_callback_method="_longitudinal_actuator_delay_title",
            minimum=0,
            maximum=1,
            step=0.01,
            unit=" seconds",
          ),

          "max_desired_acceleration": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="MaxDesiredAcceleration",
            title=tr_noop("Maximum Acceleration"),
            description=tr_noop("<b>Limit the strongest acceleration</b> openpilot can command."),
            minimum=0.1,
            maximum=frogpilot_variables.MAX_ACCELERATION,
            step=0.1,
            unit=" m/s²",
          ),

          "start_accel": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="StartAccel",
            title=tr_noop("Start Acceleration"),
            description=tr_noop("<b>Extra acceleration applied when starting from a stop.</b> Increase for quicker takeoffs; decrease for smoother, gentler starts."),
            title_callback_method="_start_accel_title",
            visible_state="_start_accel_visible",
            minimum=0,
            maximum=frogpilot_variables.MAX_ACCELERATION,
            step=0.01,
            unit=" m/s²",
          ),

          "stop_accel": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="StopAccel",
            title=tr_noop("Stop Acceleration"),
            description=tr_noop("<b>Brake force applied to hold the vehicle at a standstill.</b> Increase to prevent rolling on hills; decrease for smoother, softer stops."),
            title_callback_method="_stop_accel_title",
            minimum=-frogpilot_variables.MAX_ACCELERATION,
            maximum=0,
            step=0.01,
            unit=" m/s²",
          ),

          "stopping_decel_rate": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="StoppingDecelRate",
            title=tr_noop("Stopping Rate"),
            description=tr_noop("<b>How quickly braking ramps up when stopping.</b> Increase for shorter, firmer stops; decrease for smoother, longer stops."),
            title_callback_method="_stopping_decel_rate_title",
            visible_state="_stopping_params_visible",
            minimum=0.001,
            maximum=1,
            step=0.001,
            unit=" m/s²",
          ),

          "v_ego_starting": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="VEgoStarting",
            title=tr_noop("Start Speed"),
            description=tr_noop("<b>The speed at which openpilot exits the stopped state.</b> Increase to reduce creeping; decrease to move sooner after stopping."),
            title_callback_method="_v_ego_starting_title",
            visible_state="_stopping_params_visible",
            minimum=0.01,
            maximum=1,
            step=0.01,
            unit=" m/s²",
          ),

          "v_ego_stopping": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="VEgoStopping",
            title=tr_noop("Stop Speed"),
            description=tr_noop("<b>The speed at which openpilot considers the vehicle stopped.</b> Increase to brake earlier and stop smoothly; decrease to wait longer but risk overshooting."),
            title_callback_method="_v_ego_stopping_title",
            visible_state="_stopping_params_visible",
            minimum=0.01,
            maximum=1,
            step=0.01,
            unit=" m/s²",
          ),
        },
      ),

      "conditional_experimental": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="ConditionalExperimental",
          title=tr_noop("Conditional Experimental Mode"),
          description=tr_noop("<b>Automatically switch to \"Experimental Mode\" when set conditions are met.</b> Allows the model to handle challenging situations with smarter decision making."),
          icon="frogpilot/assets/toggle_icons/icon_conditional.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "ce_speed": MetadataItem(
            widget_type=WidgetType.TUNING_DUAL_PARAM_VALUE,
            param_key="CESpeed",
            title=tr_noop("Below"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when driving below this speed without a lead</b> to help openpilot handle low-speed situations more smoothly."),
            minimum=0,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
            secondary=MetadataItem(
              widget_type=WidgetType.TUNING_PARAM_VALUE,
              param_key="CESpeedLead",
              title=tr_noop("With Lead"),
              description=tr_noop("<b>Switch to \"Experimental Mode\" when driving below this speed with a lead</b> to help openpilot handle low-speed situations more smoothly."),
              minimum=0,
              maximum=99,
              unit=" mph",
              unit_type=UnitType.SPEED,
              value_map={0: "Off"},
            ),
            value_map={0: "Off"},
          ),

          "ce_curves": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="CECurves",
            title=tr_noop("Curve Detected Ahead"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when a curve is detected</b> to allow the model to set an appropriate speed for the curve."),
            options=(tr_noop("With Lead"),),
            child_param_keys=("CECurvesLead",),
          ),

          "ce_slowdown": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="CESlowdown",
            title=tr_noop("Slowdown Detected Ahead"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when the driving model predicts a significant slowdown ahead.</b> This helps openpilot prepare for upcoming stops or intersections."),
          ),

          "ce_stop_lights": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="CEStopLights",
            title=tr_noop("\"Detected\" Stop Lights/Signs"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" whenever the driving model \"detects\" a red light or stop sign.</b><br><br><i><b>Disclaimer</b>: openpilot does not explicitly detect traffic lights or stop signs. In \"Experimental Mode\", openpilot makes end-to-end driving decisions from camera input, which means it may stop even when there's no clear reason!</i>"),
            visible_state="_ce_stop_lights_visible",
          ),

          "ce_lead": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="CELead",
            title=tr_noop("Lead Detected Ahead"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when a slower or stopped vehicle is detected.</b> Can make braking smoother and more reliable on some vehicles."),
            options=(
              tr_noop("Slower Lead"),
              tr_noop("Stopped Lead"),
            ),
            child_param_keys=(
              "CESlowerLead",
              "CEStoppedLead",
            ),
          ),

          "ce_model_stop_time": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="CEModelStopTime",
            title=tr_noop("Predicted Stop In"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when openpilot predicts a stop within the set time.</b> This is usually triggered when the model \"sees\" a red light or stop sign ahead.<br><br><i><b>Disclaimer</b>: openpilot does not explicitly detect traffic lights or stop signs. In \"Experimental Mode\", openpilot makes end-to-end driving decisions from camera input, which means it may stop even when there's no clear reason!</i>"),
            minimum=0,
            maximum=9,
            value_map={0: "Off", 1: "1 second"},
            unit=" seconds",
          ),

          "ce_signal_speed": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="CESignalSpeed",
            title=tr_noop("Turn Signal Below"),
            description=tr_noop("<b>Switch to \"Experimental Mode\" when using a turn signal below the set speed</b> to allow the model to choose an appropriate speed for smoother left and right turns."),
            options=(tr_noop("Not For Detected Lanes"),),
            child_param_keys=("CESignalLaneDetection",),
            minimum=0,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
            value_map={0: "Off"},
          ),

          "show_cem_status": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ShowCEMStatus",
            title=tr_noop("Status Widget"),
            description=tr_noop("<b>Show which condition triggered \"Experimental Mode\"</b> on the driving screen."),
          ),
        },
      ),

      "curve_speed_controller": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="CurveSpeedController",
          title=tr_noop("Curve Speed Controller"),
          description=tr_noop("<b>Automatically slow down for upcoming curves</b> using data learned from your driving style, adapting to curves as you would."),
          icon="frogpilot/assets/toggle_icons/icon_speed_map.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "calibrated_lateral_acceleration": MetadataItem(
            widget_type=WidgetType.TEXT,
            param_key="CalibratedLateralAcceleration",
            title=tr_noop("Calibrated Lateral Acceleration"),
            description=tr_noop("<b>The learned lateral acceleration from collected driving data.</b> This sets how fast openpilot will take curves. Higher values allow faster cornering; lower values slow the vehicle for gentler turns."),
            unit=" m/s²",
            display_precision=2,
          ),

          "calibration_progress": MetadataItem(
            widget_type=WidgetType.TEXT,
            param_key="CalibrationProgress",
            title=tr_noop("Calibration Progress"),
            description=tr_noop("<b>How much curve data has been collected.</b> This is a progress meter; it is normal for the value to stay low and rarely reach 100%."),
            unit="%",
            display_precision=2,
          ),

          "reset_curve_data": MetadataItem(
            widget_type=WidgetType.BUTTON,
            title=tr_noop("Reset Curve Data"),
            button_text=tr_noop("RESET"),
            description=tr_noop("<b>Reset collected user data for \"Curve Speed Controller\".</b>"),
          ),

          "show_csc_status": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ShowCSCStatus",
            title=tr_noop("Status Widget"),
            description=tr_noop("<b>Show the \"Curve Speed Controller\" target speed on the driving screen.</b>"),
          ),
        },
      ),

      "custom_personalities": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="CustomPersonalities",
          title=tr_noop("Driving Personalities"),
          description=tr_noop("<b>Customize the \"Driving Personalities\"</b> to better match your driving style."),
          icon="frogpilot/assets/toggle_icons/icon_personality.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "traffic_personality_profile": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Traffic Mode"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Customize the \"Traffic Mode\" personality profile.</b> Designed for stop-and-go driving."),
              icon="frogpilot/assets/stock_theme/distance_icons/traffic.png",
            ),
            {
              "traffic_follow": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficFollow",
                title=tr_noop("Following Distance"),
                description=tr_noop("<b>The minimum following distance to the lead vehicle in \"Traffic Mode\".</b> openpilot blends between this value and the \"Aggressive\" profile as speed increases. Increase for more space; decrease for tighter gaps."),
                minimum=frogpilot_variables.TRAFFIC_FOLLOW_MIN,
                maximum=frogpilot_variables.MAX_T_FOLLOW,
                step=0.01,
                unit=" seconds",
                value_map={1: "1.00 second"},
              ),

              "traffic_jerk_acceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficJerkAcceleration",
                title=tr_noop("Acceleration Smoothness"),
                description=tr_noop("<b>How smoothly openpilot accelerates in \"Traffic Mode\".</b> Increase for gentler starts; decrease for faster but more abrupt takeoffs."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "traffic_jerk_deceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficJerkDeceleration",
                title=tr_noop("Braking Smoothness"),
                description=tr_noop("<b>How smoothly openpilot brakes in \"Traffic Mode\".</b> Increase for gentler stops; decrease for quicker but sharper braking."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "traffic_jerk_danger": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficJerkDanger",
                title=tr_noop("Safety Gap Bias"),
                description=tr_noop("<b>How much extra space openpilot keeps from the vehicle ahead in \"Traffic Mode\".</b> Increase for larger gaps and more cautious following; decrease for tighter gaps and closer following."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "traffic_jerk_speed_decrease": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficJerkSpeedDecrease",
                title=tr_noop("Slowdown Response"),
                description=tr_noop("<b>How smoothly openpilot slows down in \"Traffic Mode\".</b> Increase for more gradual deceleration; decrease for faster but sharper slowdowns."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "traffic_jerk_speed": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="TrafficJerkSpeed",
                title=tr_noop("Speed-Up Response"),
                description=tr_noop("<b>How smoothly openpilot speeds up in \"Traffic Mode\".</b> Increase for more gradual acceleration; decrease for quicker but more jolting acceleration."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "reset_traffic_personality": MetadataItem(
                widget_type=WidgetType.BUTTON,
                title=tr_noop("Reset to Defaults"),
                button_text=tr_noop("RESET"),
                description=tr_noop("<b>Reset \"Traffic Mode\" settings to defaults.</b>"),
              ),
            },
          ),

          "aggressive_personality_profile": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Aggressive"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Customize the \"Aggressive\" personality profile.</b> Designed for assertive driving with tighter gaps."),
              icon="frogpilot/assets/stock_theme/distance_icons/aggressive.png",
            ),
            {
              "aggressive_follow": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveFollow",
                title=tr_noop("Following Distance"),
                description=tr_noop("<b>How many seconds openpilot follows behind lead vehicles when using the \"Aggressive\" profile.</b> Increase for more space; decrease for tighter gaps.<br><br>Default: 1.25 seconds."),
                minimum=1,
                maximum=frogpilot_variables.MAX_T_FOLLOW,
                step=0.01,
                unit=" seconds",
                value_map={1: "1.00 second"},
              ),

              "aggressive_jerk_acceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveJerkAcceleration",
                title=tr_noop("Acceleration Smoothness"),
                description=tr_noop("<b>How smoothly openpilot accelerates with the \"Aggressive\" profile.</b> Increase for gentler starts; decrease for faster but more abrupt takeoffs."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "aggressive_jerk_deceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveJerkDeceleration",
                title=tr_noop("Braking Smoothness"),
                description=tr_noop("<b>How smoothly openpilot brakes with the \"Aggressive\" profile.</b> Increase for gentler stops; decrease for quicker but sharper braking."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "aggressive_jerk_danger": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveJerkDanger",
                title=tr_noop("Safety Gap Bias"),
                description=tr_noop("<b>How much extra space openpilot keeps from the vehicle ahead with the \"Aggressive\" profile.</b> Increase for larger gaps and more cautious following; decrease for tighter gaps and closer following."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "aggressive_jerk_speed_decrease": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveJerkSpeedDecrease",
                title=tr_noop("Slowdown Response"),
                description=tr_noop("<b>How smoothly openpilot slows down with the \"Aggressive\" profile.</b> Increase for more gradual deceleration; decrease for faster but sharper slowdowns."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "aggressive_jerk_speed": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="AggressiveJerkSpeed",
                title=tr_noop("Speed-Up Response"),
                description=tr_noop("<b>How smoothly openpilot speeds up with the \"Aggressive\" profile.</b> Increase for more gradual acceleration; decrease for quicker but more jolting acceleration."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "reset_aggressive_personality": MetadataItem(
                widget_type=WidgetType.BUTTON,
                title=tr_noop("Reset to Defaults"),
                button_text=tr_noop("RESET"),
                description=tr_noop("<b>Reset the \"Aggressive\" profile to defaults.</b>"),
              ),
            },
          ),

          "standard_personality_profile": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Standard"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Customize the \"Standard\" personality profile.</b> Designed for balanced driving with moderate gaps."),
              icon="frogpilot/assets/stock_theme/distance_icons/standard.png",
            ),
            {
              "standard_follow": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardFollow",
                title=tr_noop("Following Distance"),
                description=tr_noop("<b>How many seconds openpilot follows behind lead vehicles when using the \"Standard\" profile.</b> Increase for more space; decrease for tighter gaps.<br><br>Default: 1.45 seconds."),
                minimum=1,
                maximum=frogpilot_variables.MAX_T_FOLLOW,
                step=0.01,
                unit=" seconds",
                value_map={1: "1.00 second"},
              ),

              "standard_jerk_acceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardJerkAcceleration",
                title=tr_noop("Acceleration Smoothness"),
                description=tr_noop("<b>How smoothly openpilot accelerates with the \"Standard\" profile.</b> Increase for gentler starts; decrease for faster but more abrupt takeoffs."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "standard_jerk_deceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardJerkDeceleration",
                title=tr_noop("Braking Smoothness"),
                description=tr_noop("<b>How smoothly openpilot brakes with the \"Standard\" profile.</b> Increase for gentler stops; decrease for quicker but sharper braking."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "standard_jerk_danger": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardJerkDanger",
                title=tr_noop("Safety Gap Bias"),
                description=tr_noop("<b>How much extra space openpilot keeps from the vehicle ahead with the \"Standard\" profile.</b> Increase for larger gaps and more cautious following; decrease for tighter gaps and closer following."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "standard_jerk_speed_decrease": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardJerkSpeedDecrease",
                title=tr_noop("Slowdown Response"),
                description=tr_noop("<b>How smoothly openpilot slows down with the \"Standard\" profile.</b> Increase for more gradual deceleration; decrease for faster but sharper slowdowns."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "standard_jerk_speed": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="StandardJerkSpeed",
                title=tr_noop("Speed-Up Response"),
                description=tr_noop("<b>How smoothly openpilot speeds up with the \"Standard\" profile.</b> Increase for more gradual acceleration; decrease for quicker but more jolting acceleration."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "reset_standard_personality": MetadataItem(
                widget_type=WidgetType.BUTTON,
                title=tr_noop("Reset to Defaults"),
                button_text=tr_noop("RESET"),
                description=tr_noop("<b>Reset the \"Standard\" profile to defaults.</b>"),
              ),
            },
          ),

          "relaxed_personality_profile": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Relaxed"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Customize the \"Relaxed\" personality profile.</b> Designed for smoother, more comfortable driving with larger gaps."),
              icon="frogpilot/assets/stock_theme/distance_icons/relaxed.png",
            ),
            {
              "relaxed_follow": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedFollow",
                title=tr_noop("Following Distance"),
                description=tr_noop("<b>How many seconds openpilot follows behind lead vehicles when using the \"Relaxed\" profile.</b> Increase for more space; decrease for tighter gaps.<br><br>Default: 1.75 seconds."),
                minimum=1,
                maximum=frogpilot_variables.MAX_T_FOLLOW,
                step=0.01,
                unit=" seconds",
                value_map={1: "1.00 second"},
              ),

              "relaxed_jerk_acceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedJerkAcceleration",
                title=tr_noop("Acceleration Smoothness"),
                description=tr_noop("<b>How smoothly openpilot accelerates with the \"Relaxed\" profile.</b> Increase for gentler starts; decrease for faster but more abrupt takeoffs."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "relaxed_jerk_deceleration": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedJerkDeceleration",
                title=tr_noop("Braking Smoothness"),
                description=tr_noop("<b>How smoothly openpilot brakes with the \"Relaxed\" profile.</b> Increase for gentler stops; decrease for quicker but sharper braking."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "relaxed_jerk_danger": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedJerkDanger",
                title=tr_noop("Safety Gap Bias"),
                description=tr_noop("<b>How much extra space openpilot keeps from the vehicle ahead with the \"Relaxed\" profile.</b> Increase for larger gaps and more cautious following; decrease for tighter gaps and closer following."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "relaxed_jerk_speed_decrease": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedJerkSpeedDecrease",
                title=tr_noop("Slowdown Response"),
                description=tr_noop("<b>How smoothly openpilot slows down with the \"Relaxed\" profile.</b> Increase for more gradual deceleration; decrease for faster but sharper slowdowns."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "relaxed_jerk_speed": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="RelaxedJerkSpeed",
                title=tr_noop("Speed-Up Response"),
                description=tr_noop("<b>How smoothly openpilot speeds up with the \"Relaxed\" profile.</b> Increase for more gradual acceleration; decrease for quicker but more jolting acceleration."),
                minimum=frogpilot_variables.JERK_MIN_RAW,
                maximum=frogpilot_variables.JERK_MAX_RAW,
                unit="%",
              ),

              "reset_relaxed_personality": MetadataItem(
                widget_type=WidgetType.BUTTON,
                title=tr_noop("Reset to Defaults"),
                button_text=tr_noop("RESET"),
                description=tr_noop("<b>Reset the \"Relaxed\" profile to defaults.</b>"),
              ),
            },
          ),
        },
      ),

      "longitudinal_tune": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="LongitudinalTune",
          title=tr_noop("Longitudinal Tuning"),
          description=tr_noop("<b>Acceleration and braking control changes</b> to fine-tune how openpilot drives."),
          icon="frogpilot/assets/toggle_icons/icon_longitudinal_tune.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "acceleration_profile": MetadataItem(
            widget_type=WidgetType.MULTIPLE_BUTTON,
            param_key="AccelerationProfile",
            title=tr_noop("Acceleration Profile"),
            description=tr_noop("<b>How quickly openpilot speeds up.</b> \"Eco\" is gentle and efficient, \"Sport\" is firmer and more responsive, and \"Sport+\" accelerates at the maximum rate allowed."),
            options=(
              tr_noop("Standard"),
              tr_noop("Eco"),
              tr_noop("Sport"),
              tr_noop("Sport+"),
            ),
          ),

          "deceleration_profile": MetadataItem(
            widget_type=WidgetType.MULTIPLE_BUTTON,
            param_key="DecelerationProfile",
            title=tr_noop("Deceleration Profile"),
            description=tr_noop("<b>How firmly openpilot slows down.</b> \"Eco\" favors coasting, \"Sport\" applies stronger braking."),
            options=(
              tr_noop("Standard"),
              tr_noop("Eco"),
              tr_noop("Eco+"),
            ),
          ),

          "human_acceleration": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HumanAcceleration",
            title=tr_noop("Human-Like Acceleration"),
            description=tr_noop("<b>Acceleration that mimics human behavior</b> by easing the throttle at low speeds and adding extra power when taking off from a stop."),
            refreshes_visibility=True,
          ),

          "human_following": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HumanFollowing",
            title=tr_noop("Human-Like Following"),
            description=tr_noop("<b>Following behavior that mimics human drivers</b> by closing gaps behind faster vehicles for quicker takeoffs and dynamically adjusting the desired following distance for gentler, more efficient braking."),
          ),

          "human_lane_changes": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="HumanLaneChanges",
            title=tr_noop("Human-Like Lane Changes"),
            description=tr_noop("<b>Lane-change behavior that mimics human drivers</b> by anticipating and tracking adjacent vehicles during lane changes."),
            visible_state="_has_radar",
          ),

          "lead_detection_threshold": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LeadDetectionThreshold",
            title=tr_noop("Lead Detection Sensitivity"),
            description=tr_noop("<b>How sensitive openpilot is to detecting vehicles.</b> Higher sensitivity allows quicker detection at longer distances but may react to non-vehicle objects; lower sensitivity is more conservative and reduces false detections."),
            minimum=frogpilot_variables.LEAD_DETECTION_MIN_RAW,
            maximum=frogpilot_variables.LEAD_DETECTION_MAX_RAW,
            unit="%",
          ),

          "taco_tune": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="TacoTune",
            title=tr_noop("\"Taco Bell Run\" Turn Speed Hack"),
            description=tr_noop("<b>The turn-speed hack from comma's 2022 \"Taco Bell Run\".</b> Designed to slow down for left and right turns."),
          ),
        },
      ),

      "quality_of_life": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="QOLLongitudinal",
          title=tr_noop("Quality of Life"),
          description=tr_noop("<b>Miscellaneous acceleration and braking control changes</b> to fine-tune how openpilot drives."),
          icon="frogpilot/assets/toggle_icons/icon_quality_of_life.png",
          button_text=tr_noop("MANAGE"),
        ),
        {
          "custom_cruise": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="CruiseButtonIncrement",
            title=tr_noop("Cruise Interval"),
            description=tr_noop("<b>How much the set speed increases or decreases</b> for each + or - cruise control button press."),
            visible_state="_no_pcm_cruise",
            minimum=1,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
          ),

          "custom_cruise_long": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="CruiseButtonIncrementLong",
            title=tr_noop("Cruise Interval (Hold)"),
            description=tr_noop("<b>How much the set speed increases or decreases while holding the + or - cruise control buttons.</b>"),
            visible_state="_no_pcm_cruise",
            minimum=1,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
          ),

          "force_stops": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ForceStops",
            title=tr_noop("Force Stop at \"Detected\" Stop Lights/Signs"),
            description=tr_noop("<b>Force openpilot to stop whenever the driving model \"detects\" a red light or stop sign.</b><br><br><i><b>Disclaimer</b>: openpilot does not explicitly detect traffic lights or stop signs. In \"Experimental Mode\", openpilot makes end-to-end driving decisions from camera input, which means it may stop even when there's no clear reason!</i>"),
          ),

          "increased_stopped_distance": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="IncreasedStoppedDistance",
            title=tr_noop("Increase Stopped Distance by:"),
            description=tr_noop("<b>Add extra space when stopped behind vehicles.</b> Increase for more room; decrease for shorter gaps."),
            minimum=0,
            maximum=10,
            value_map={0: "Off", 1: "1 foot"},
            unit=" feet",
            unit_type=UnitType.DISTANCE,
          ),

          "map_gears": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="MapGears",
            title=tr_noop("Map Accel/Decel to Gears"),
            description=tr_noop("<b>Map the Acceleration or Deceleration profiles to the vehicle's \"Eco\" and \"Sport\" gear modes.</b>"),
            visible_state="_is_toyota_non_tsk",
            options=(
              tr_noop("Acceleration"),
              tr_noop("Deceleration"),
            ),
            child_param_keys=(
              "MapAcceleration",
              "MapDeceleration",
            ),
          ),

          "set_speed_offset": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="SetSpeedOffset",
            title=tr_noop("Offset Set Speed by:"),
            description=tr_noop("<b>Increase the set speed by the chosen offset.</b> For example, set +5 if you usually drive 5 over the limit."),
            visible_state="_no_pcm_cruise",
            minimum=0,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
          ),

          "reverse_cruise": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ReverseCruise",
            title=tr_noop("Reverse Cruise Increase"),
            description=tr_noop("<b>Reverse the cruise control button behavior</b> so a short press increases the set speed by 5 instead of 1."),
            visible_state="_is_toyota",
          ),

          "weather_presets": (
            MetadataItem(
              widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
              param_key="WeatherPresets",
              title=tr_noop("Weather Condition Offsets"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Automatically adjust driving behavior based on real-time weather.</b> Helps maintain comfort and safety in low visibility, rain, or snow."),
            ),
            {
              "low_visibility_offsets": (
                MetadataItem(
                  widget_type=WidgetType.BUTTON,
                  title=tr_noop("Low Visibility"),
                  button_text=tr_noop("MANAGE"),
                  description=tr_noop("<b>Driving adjustments for fog, haze, or other low-visibility conditions.</b>"),
                ),
                {
                  "increase_following_low_visibility": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreaseFollowingLowVisibility",
                    title=tr_noop("Increase Following Distance by:"),
                    description=tr_noop("<b>Add extra space behind lead vehicles in low visibility.</b> Increase for more space; decrease for tighter gaps."),
                    minimum=0,
                    maximum=frogpilot_variables.MAX_T_FOLLOW,
                    step=0.01,
                    unit=" seconds",
                  ),

                  "increased_stopped_distance_low_visibility": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreasedStoppedDistanceLowVisibility",
                    title=tr_noop("Increase Stopped Distance by:"),
                    description=tr_noop("<b>Add extra buffer when stopped behind vehicles in low visibility.</b> Increase for more room; decrease for shorter gaps."),
                    minimum=0,
                    maximum=10,
                    value_map={0: "Off", 1: "1 foot"},
                    unit=" feet",
                    unit_type=UnitType.DISTANCE,
                  ),

                  "reduce_acceleration_low_visibility": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceAccelerationLowVisibility",
                    title=tr_noop("Reduce Acceleration by:"),
                    description=tr_noop("<b>Lower the maximum acceleration in low visibility.</b> Increase for softer takeoffs; decrease for quicker but less stable takeoffs."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),

                  "reduce_lateral_acceleration_low_visibility": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceLateralAccelerationLowVisibility",
                    title=tr_noop("Reduce Speed in Curves by:"),
                    description=tr_noop("<b>Lower the desired speed while driving through curves in low visibility.</b> Increase for safer, gentler turns; decrease for more aggressive driving in curves."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),
                },
              ),

              "rain_offsets": (
                MetadataItem(
                  widget_type=WidgetType.BUTTON,
                  title=tr_noop("Rain"),
                  button_text=tr_noop("MANAGE"),
                  description=tr_noop("<b>Driving adjustments for rainy conditions.</b>"),
                ),
                {
                  "increase_following_rain": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreaseFollowingRain",
                    title=tr_noop("Increase Following Distance by:"),
                    description=tr_noop("<b>Add extra space behind lead vehicles in rain.</b> Increase for more space; decrease for tighter gaps."),
                    minimum=0,
                    maximum=frogpilot_variables.MAX_T_FOLLOW,
                    step=0.01,
                    unit=" seconds",
                  ),

                  "increased_stopped_distance_rain": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreasedStoppedDistanceRain",
                    title=tr_noop("Increase Stopped Distance by:"),
                    description=tr_noop("<b>Add extra buffer when stopped behind vehicles in rain.</b> Increase for more room; decrease for shorter gaps."),
                    minimum=0,
                    maximum=10,
                    value_map={0: "Off", 1: "1 foot"},
                    unit=" feet",
                    unit_type=UnitType.DISTANCE,
                  ),

                  "reduce_acceleration_rain": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceAccelerationRain",
                    title=tr_noop("Reduce Acceleration by:"),
                    description=tr_noop("<b>Lower the maximum acceleration in rain.</b> Increase for softer takeoffs; decrease for quicker but less stable takeoffs."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),

                  "reduce_lateral_acceleration_rain": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceLateralAccelerationRain",
                    title=tr_noop("Reduce Speed in Curves by:"),
                    description=tr_noop("<b>Lower the desired speed while driving through curves in rain.</b> Increase for safer, gentler turns; decrease for more aggressive driving in curves."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),
                },
              ),

              "rain_storm_offsets": (
                MetadataItem(
                  widget_type=WidgetType.BUTTON,
                  title=tr_noop("Rainstorms"),
                  button_text=tr_noop("MANAGE"),
                  description=tr_noop("<b>Driving adjustments for rainstorms.</b>"),
                ),
                {
                  "increase_following_rain_storm": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreaseFollowingRainStorm",
                    title=tr_noop("Increase Following Distance by:"),
                    description=tr_noop("<b>Add extra space behind lead vehicles in a rainstorm.</b> Increase for more space; decrease for tighter gaps."),
                    minimum=0,
                    maximum=frogpilot_variables.MAX_T_FOLLOW,
                    step=0.01,
                    unit=" seconds",
                  ),

                  "increased_stopped_distance_rain_storm": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreasedStoppedDistanceRainStorm",
                    title=tr_noop("Increase Stopped Distance by:"),
                    description=tr_noop("<b>Add extra buffer when stopped behind vehicles in a rainstorm.</b> Increase for more room; decrease for shorter gaps."),
                    minimum=0,
                    maximum=10,
                    value_map={0: "Off", 1: "1 foot"},
                    unit=" feet",
                    unit_type=UnitType.DISTANCE,
                  ),

                  "reduce_acceleration_rain_storm": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceAccelerationRainStorm",
                    title=tr_noop("Reduce Acceleration by:"),
                    description=tr_noop("<b>Lower the maximum acceleration in a rainstorm.</b> Increase for softer takeoffs; decrease for quicker but less stable takeoffs."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),

                  "reduce_lateral_acceleration_rain_storm": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceLateralAccelerationRainStorm",
                    title=tr_noop("Reduce Speed in Curves by:"),
                    description=tr_noop("<b>Lower the desired speed while driving through curves in a rainstorm.</b> Increase for safer, gentler turns; decrease for more aggressive driving in curves."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),
                },
              ),

              "snow_offsets": (
                MetadataItem(
                  widget_type=WidgetType.BUTTON,
                  title=tr_noop("Snow"),
                  button_text=tr_noop("MANAGE"),
                  description=tr_noop("<b>Driving adjustments for snowy conditions.</b>"),
                ),
                {
                  "increase_following_snow": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreaseFollowingSnow",
                    title=tr_noop("Increase Following Distance by:"),
                    description=tr_noop("<b>Add extra space behind lead vehicles in snow.</b> Increase for more space; decrease for tighter gaps."),
                    minimum=0,
                    maximum=frogpilot_variables.MAX_T_FOLLOW,
                    step=0.01,
                    unit=" seconds",
                  ),

                  "increased_stopped_distance_snow": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="IncreasedStoppedDistanceSnow",
                    title=tr_noop("Increase Stopped Distance by:"),
                    description=tr_noop("<b>Add extra buffer when stopped behind vehicles in snow.</b> Increase for more room; decrease for shorter gaps."),
                    minimum=0,
                    maximum=10,
                    value_map={0: "Off", 1: "1 foot"},
                    unit=" feet",
                    unit_type=UnitType.DISTANCE,
                  ),

                  "reduce_acceleration_snow": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceAccelerationSnow",
                    title=tr_noop("Reduce Acceleration by:"),
                    description=tr_noop("<b>Lower the maximum acceleration in snow.</b> Increase for softer takeoffs; decrease for quicker but less stable takeoffs."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),

                  "reduce_lateral_acceleration_snow": MetadataItem(
                    widget_type=WidgetType.TUNING_PARAM_VALUE,
                    param_key="ReduceLateralAccelerationSnow",
                    title=tr_noop("Reduce Speed in Curves by:"),
                    description=tr_noop("<b>Lower the desired speed while driving through curves in snow.</b> Increase for safer, gentler turns; decrease for more aggressive driving in curves."),
                    minimum=0,
                    maximum=99,
                    unit="%",
                  ),
                },
              ),

              "set_weather_key": MetadataItem(
                widget_type=WidgetType.BUTTONS,
                param_key="WeatherToken",
                title=tr_noop("Set Your Own Key"),
                description=tr_noop("<b>Set your own \"OpenWeatherMap\" key to increase the weather update rate.</b><br><br><i>Personal keys grant 1,000 free calls per day, allowing for updates every minute. The default key is shared and only updates every 15 minutes.</i>"),
                buttons=(
                  ButtonSpec(text=tr_noop("ADD"), action="add"),
                  ButtonSpec(text=tr_noop("TEST"), action="test"),
                ),
              ),
            },
          ),
        },
      ),

      "speed_limit_controller": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="SpeedLimitController",
          title=tr_noop("Speed Limit Controller"),
          description=tr_noop("<b>Limit openpilot's maximum driving speed to the current speed limit</b> obtained from downloaded maps, Mapbox, or the dashboard for supported vehicles (Ford, Genesis, Hyundai, Kia, Lexus, Toyota)."),
          icon="frogpilot/assets/toggle_icons/icon_speed_limit.png",
          button_text=tr_noop("MANAGE"),
          refreshes_visibility=True,
        ),
        {
          "slc_fallback": MetadataItem(
            widget_type=WidgetType.MULTIPLE_BUTTON,
            param_key="SLCFallback",
            title=tr_noop("Fallback Speed"),
            description=tr_noop("<b>The speed used by \"Speed Limit Controller\" when no speed limit is found.</b><br><br>- <b>Set Speed</b>: Use the cruise set speed<br>- <b>Experimental Mode</b>: Estimate the limit using the driving model<br>- <b>Previous Limit</b>: Keep using the last confirmed limit"),
            options=(
              tr_noop("Set Speed"),
              tr_noop("Experimental Mode"),
              tr_noop("Previous Limit"),
            ),
          ),

          "slc_override": MetadataItem(
            widget_type=WidgetType.MULTIPLE_BUTTON,
            param_key="SLCOverride",
            title=tr_noop("Override Speed"),
            description=tr_noop("<b>The speed used by \"Speed Limit Controller\" after you manually drive faster than the posted limit.</b><br><br>- <b>Set with Gas Pedal</b>: Use the highest speed reached while pressing the gas<br>- <b>Max Set Speed</b>: Use the cruise set speed<br><br>Overrides clear when openpilot disengages."),
            options=(
              tr_noop("None"),
              tr_noop("Set With Gas Pedal"),
              tr_noop("Max Set Speed"),
            ),
          ),

          "slc_priority": MetadataItem(
            widget_type=WidgetType.BUTTON,
            title=tr_noop("Speed Limit Source Priority"),
            button_text=tr_noop("SELECT"),
            description=tr_noop("<b>The source order for speed limits</b> when more than one is available."),
            options=(
              tr_noop("Dashboard"),
              tr_noop("Map Data"),
              tr_noop("Highest"),
              tr_noop("Lowest"),
              tr_noop("None"),
            ),
            child_param_keys=(
              "SLCPriority1",
              "SLCPriority2",
              "SLCPriority3",
            ),
          ),

          "slc_offsets": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Speed Limit Offsets"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Add an offset to the posted speed limit</b> to better match your driving style."),
            ),
            {
              "offset_1": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset1",
                title=tr_noop("Speed Offset (0-24 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 0 and 24 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (0-29 km/h)"),
              ),

              "offset_2": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset2",
                title=tr_noop("Speed Offset (25-34 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 25 and 34 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (30-49 km/h)"),
              ),

              "offset_3": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset3",
                title=tr_noop("Speed Offset (35-44 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 35 and 44 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (50-59 km/h)"),
              ),

              "offset_4": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset4",
                title=tr_noop("Speed Offset (45-54 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 45 and 54 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (60-79 km/h)"),
              ),

              "offset_5": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset5",
                title=tr_noop("Speed Offset (55-64 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 55 and 64 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (80-99 km/h)"),
              ),

              "offset_6": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset6",
                title=tr_noop("Speed Offset (65-74 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 65 and 74 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (100-119 km/h)"),
              ),

              "offset_7": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="Offset7",
                title=tr_noop("Speed Offset (75-99 mph)"),
                description=tr_noop("<b>How much to offset posted speed-limits</b> between 75 and 99 mph."),
                minimum=-99,
                maximum=99,
                unit=" mph",
                unit_type=UnitType.SPEED,
                metric_title=tr_noop("Speed Offset (120-140 km/h)"),
              ),
            },
          ),

          "slc_qol": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Quality of Life"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Miscellaneous \"Speed Limit Controller\" changes</b> to fine-tune how openpilot drives."),
            ),
            {
              "set_speed_limit": MetadataItem(
                widget_type=WidgetType.TUNING_TOGGLE,
                param_key="SetSpeedLimit",
                title=tr_noop("Match Speed Limit on Engage"),
                description=tr_noop("<b>When openpilot is first enabled, automatically set the max speed to the current posted limit.</b>"),
                visible_state="_no_pcm_cruise",
              ),

              "slc_confirmation": MetadataItem(
                widget_type=WidgetType.TUNING_TOGGLE,
                param_key="SLCConfirmation",
                title=tr_noop("Confirm New Speed Limits"),
                description=tr_noop("<b>Ask before changing to a new speed limit.</b> To accept, tap the flashing on-screen widget or press the Cruise Increase button. To deny, press the Cruise Decrease button or ignore the prompt for 30 seconds."),
                options=(
                  tr_noop("Lower Limits"),
                  tr_noop("Higher Limits"),
                ),
                child_param_keys=(
                  "SLCConfirmationLower",
                  "SLCConfirmationHigher",
                ),
              ),

              "slc_lookahead_higher": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="SLCLookaheadHigher",
                title=tr_noop("Higher Limit Lookahead Time"),
                description=tr_noop("<b>How far ahead openpilot anticipates upcoming higher speed limits</b> from downloaded map data."),
                minimum=0,
                maximum=30,
                unit=" seconds",
              ),

              "slc_lookahead_lower": MetadataItem(
                widget_type=WidgetType.TUNING_PARAM_VALUE,
                param_key="SLCLookaheadLower",
                title=tr_noop("Lower Limit Lookahead Time"),
                description=tr_noop("<b>How far ahead openpilot anticipates upcoming lower speed limits</b> from downloaded map data."),
                minimum=0,
                maximum=30,
                unit=" seconds",
              ),

              "slc_mapbox_filler": MetadataItem(
                widget_type=WidgetType.TUNING_TOGGLE,
                param_key="SLCMapboxFiller",
                title=tr_noop("Use Mapbox as Fallback"),
                description=tr_noop("<b>Use Mapbox speed-limit data when no other source is available.</b>"),
                visible_state="_has_mapbox_key",
              ),
            },
          ),

          "slc_visuals": (
            MetadataItem(
              widget_type=WidgetType.BUTTON,
              title=tr_noop("Visual Settings"),
              button_text=tr_noop("MANAGE"),
              description=tr_noop("<b>Visual \"Speed Limit Controller\" changes</b> to fine-tune how the driving screen looks."),
            ),
            {
              "show_slc_offset": MetadataItem(
                widget_type=WidgetType.TUNING_TOGGLE,
                param_key="ShowSLCOffset",
                title=tr_noop("Show Speed Limit Offset"),
                description=tr_noop("<b>Show the current offset from the posted limit</b> on the driving screen."),
              ),

              "speed_limit_sources": MetadataItem(
                widget_type=WidgetType.TUNING_TOGGLE,
                param_key="SpeedLimitSources",
                title=tr_noop("Show Speed Limit Sources"),
                description=tr_noop("<b>Display the speed-limit sources and their current values</b> on the driving screen."),
              ),
            },
          ),
        },
      ),
    },
  ),

  "map_data": PanelMetadata(
    sections={
      "root": (
        "preferred_schedule",
        "last_maps_update",
        "map_sources",
        "update_maps",
        "remove_maps",
        "storage_used",
      ),
    },
    items={
      "last_maps_update": MetadataItem(
        widget_type=WidgetType.TEXT,
        param_key="LastMapsUpdate",
        title=tr_noop("Last Updated"),
        description=tr_noop("<b>When your offline maps were last downloaded.</b>"),
      ),

      "storage_used": MetadataItem(
        widget_type=WidgetType.TEXT,
        title=tr_noop("Storage Used"),
        description=tr_noop("<b>Disk space used by downloaded offline map data.</b>"),
      ),

      "update_maps": MetadataItem(
        widget_type=WidgetType.BUTTON,
        title=tr_noop("Download Maps"),
        button_text=tr_noop("DOWNLOAD"),
        description=tr_noop("<b>Download the selected offline maps now.</b> Runs in the background \u2014 you can keep using the menus while it works."),
      ),

      "remove_maps": MetadataItem(
        widget_type=WidgetType.BUTTON,
        title=tr_noop("Remove Downloaded Maps"),
        button_text=tr_noop("REMOVE"),
        description=tr_noop("<b>Delete all downloaded offline map data.</b> You can re-download maps at any time."),
      ),

      "preferred_schedule": MetadataItem(
        widget_type=WidgetType.MULTIPLE_BUTTON,
        param_key="PreferredSchedule",
        title=tr_noop("Automatically Update Maps"),
        description=tr_noop("<b>How often maps update</b> from \"OpenStreetMap (OSM)\" with the latest speed limit information. Weekly updates run every Sunday; monthly updates run on the 1st."),
        options=(
          tr_noop("Manually"),
          tr_noop("Weekly"),
          tr_noop("Monthly"),
        ),
      ),

      "map_sources": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Map Sources"),
        description=tr_noop("<b>Select the countries or U.S. states to use with \"Speed Limit Controller\".</b>"),
        buttons=(
          ButtonSpec(text=tr_noop("COUNTRIES"), action="countries"),
          ButtonSpec(text=tr_noop("STATES"), action="states"),
        ),
      ),
    },
  ),

  "navigation": PanelMetadata(
    sections={
      "root": (
        "manage_settings_at",
        "public_mapbox_key",
        "secret_mapbox_key",
        "mapbox_setup_instructions",
        "speed_limit_filler",
      ),
    },
    items={
      "manage_settings_at": MetadataItem(
        widget_type=WidgetType.TEXT,
        title=tr_noop("Manage Your Settings At"),
        description="",
        value_text=tr_noop("Offline..."),
      ),

      "public_mapbox_key": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        param_key="MapboxPublicKey",
        title=tr_noop("Public Mapbox Key"),
        description=tr_noop("<b>Manage your Public Mapbox Key.</b>"),
        buttons=(
          ButtonSpec(text=tr_noop("ADD"), action="add"),
          ButtonSpec(text=tr_noop("TEST"), action="test"),
        ),
      ),

      "secret_mapbox_key": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        param_key="MapboxSecretKey",
        title=tr_noop("Secret Mapbox Key"),
        description=tr_noop("<b>Manage your Secret Mapbox Key.</b>"),
        buttons=(
          ButtonSpec(text=tr_noop("ADD"), action="add"),
          ButtonSpec(text=tr_noop("TEST"), action="test"),
        ),
      ),

      "mapbox_setup_instructions": MetadataItem(
        widget_type=WidgetType.BUTTON,
        title=tr_noop("Mapbox Setup Instructions"),
        button_text=tr_noop("VIEW"),
        description=tr_noop("<b>Instructions on how to set up Mapbox</b> for \"Primeless Navigation\"."),
      ),

      "speed_limit_filler": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        param_key="SpeedLimitFiller",
        title=tr_noop("Speed Limit Filler"),
        description=tr_noop("<b>Automatically collect missing or incorrect speed limits while you drive</b> using speeds limits sourced from your dashboard (if supported), Mapbox, and \"Navigate on openpilot\".<br><br>When you're parked and connected to Wi-Fi, FrogPilot will automatically processes this data into a file to be used with the tool located at \"SpeedLimitFiller.frogpilot.com\".<br><br>You can download this file from \"The Pond\" in the \"Download Speed Limits\" menu.<br><br>Need a step-by-step guide? Visit <b>#speed-limit-filler</b> in the FrogPilot Discord!"),
        buttons=(
          ButtonSpec(text=tr_noop("CANCEL"), action="cancel"),
          ButtonSpec(text=tr_noop("Manually Update Speed Limits"), action="manually_update_speed_limits"),
        ),
      ),
    },
  ),

  "steering": PanelMetadata(
    sections={
      "root": (
        "advanced_lateral_tune",
        "always_on_lateral",
        "lane_changes",
        "lateral_tuning",
        "quality_of_life",
      ),

      "advanced_lateral_tune": (
        "steer_delay",
        "steer_friction",
        "steer_kp",
        "steer_lat_accel",
        "steer_ratio",
        "force_auto_tune",
        "force_auto_tune_off",
        "force_torque_controller",
      ),

      "always_on_lateral": (
        "always_on_lateral_lkas",
        "pause_aol_on_brake",
      ),

      "lane_changes": (
        "nudgeless_lane_change",
        "lane_change_time",
        "minimum_lane_change_speed",
        "lane_detection_width",
        "one_lane_change",
      ),

      "lateral_tuning": (
        "turn_desires",
        "nnff",
        "nnff_lite",
      ),

      "quality_of_life": (
        "pause_lateral_speed",
      ),
    },
    items={
      "advanced_lateral_tune": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="AdvancedLateralTune",
          title=tr_noop("Advanced Lateral Tuning"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Advanced steering control changes to fine-tune how openpilot drives.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_advanced_lateral_tune.png",
          visible_state="_advanced_lateral_tune_visible",
        ),
        {
          "steer_delay": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="SteerDelay",
            title=tr_noop("Actuator Delay"),
            description=tr_noop("<b>The time between openpilot's steering command and the vehicle's response.</b> Increase if the vehicle reacts late; decrease if it feels jumpy. Auto-learned by default."),
            title_callback_method="_steer_delay_title",
            minimum=0.01,
            maximum=1,
            step=0.01,
            button_text=tr_noop("Reset"),
            button_callback_method="_reset_steering_param",
            visible_state="_steer_delay_visible",
          ),

          "steer_friction": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="SteerFriction",
            title=tr_noop("Friction"),
            description=tr_noop("<b>Compensates for steering friction.</b> Increase if the wheel sticks near center; decrease if it jitters. Auto-learned by default."),
            title_callback_method="_steer_friction_title",
            minimum=0,
            maximum=1,
            step=0.01,
            button_text=tr_noop("Reset"),
            button_callback_method="_reset_steering_param",
            visible_state="_steer_friction_visible",
          ),

          "steer_kp": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="SteerKP",
            title=tr_noop("Kp Factor"),
            description=tr_noop("<b>How strongly openpilot corrects lane position.</b> Higher is tighter but twitchier; lower is smoother but slower. Auto-learned by default."),
            title_callback_method="_steer_kp_title",
            minimum_callback_method="_steer_kp_min",
            maximum_callback_method="_steer_kp_max",
            step=0.01,
            button_text=tr_noop("Reset"),
            button_callback_method="_reset_steering_param",
            visible_state="_steer_kp_visible",
          ),

          "steer_lat_accel": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="SteerLatAccel",
            title=tr_noop("Lateral Acceleration"),
            description=tr_noop("<b>Maps steering torque to turning response.</b> Increase for sharper turns; decrease for gentler steering. Auto-learned by default."),
            title_callback_method="_steer_lat_accel_title",
            minimum_callback_method="_steer_lat_accel_min",
            maximum_callback_method="_steer_lat_accel_max",
            step=0.01,
            button_text=tr_noop("Reset"),
            button_callback_method="_reset_steering_param",
            visible_state="_steer_lat_accel_visible",
          ),

          "steer_ratio": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="SteerRatio",
            title=tr_noop("Steer Ratio"),
            description=tr_noop("<b>The relationship between steering wheel rotation and road wheel angle.</b> Increase if steering feels too quick or twitchy; decrease if it feels too slow or weak. Auto-learned by default."),
            title_callback_method="_steer_ratio_title",
            minimum_callback_method="_steer_ratio_min",
            maximum_callback_method="_steer_ratio_max",
            step=0.01,
            button_text=tr_noop("Reset"),
            button_callback_method="_reset_steering_param",
            visible_state="_steer_ratio_visible",
          ),

          "force_auto_tune": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ForceAutoTune",
            title=tr_noop("Force Auto-Tune On"),
            description=tr_noop("<b>Force-enable openpilot's live auto-tuning for \"Friction\" and \"Lateral Acceleration\".</b>"),
            visible_state="_force_auto_tune_visible",
            refreshes_visibility=True,
          ),

          "force_auto_tune_off": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ForceAutoTuneOff",
            title=tr_noop("Force Auto-Tune Off"),
            description=tr_noop("<b>Force-disable openpilot's live auto-tuning for \"Friction\" and \"Lateral Acceleration\" and use the set value instead.</b>"),
            visible_state="_has_auto_tune",
            refreshes_visibility=True,
          ),

          "force_torque_controller": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ForceTorqueController",
            title=tr_noop("Force Torque Controller"),
            description=tr_noop("<b>Use torque-based steering control instead of angle-based control for smoother lane keeping, especially in curves.</b>"),
            reboot=True,
            visible_state="_force_torque_visible",
            refreshes_visibility=True,
          ),
        },
      ),

      "always_on_lateral": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="AlwaysOnLateral",
          title=tr_noop("Always On Lateral"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>openpilot's steering remains active even when the accelerator or brake pedals are pressed.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_always_on_lateral.png",
          reboot=True,
        ),
        {
          "always_on_lateral_lkas": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="AlwaysOnLateralLKAS",
            title=tr_noop("Enable With LKAS"),
            description=tr_noop("<b>Enable \"Always On Lateral\" whenever \"LKAS\" is on, even when openpilot is not engaged.</b>"),
            visible_state="_lkas_allowed_for_aol",
          ),

          "pause_aol_on_brake": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="PauseAOLOnBrake",
            title=tr_noop("Pause on Brake Press Below"),
            description=tr_noop("<b>Pause \"Always On Lateral\" below the set speed while the brake pedal is pressed.</b>"),
            minimum=0,
            maximum=99,
            value_map={0: "Off"},
          ),
        },
      ),

      "lane_changes": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="LaneChanges",
          title=tr_noop("Lane Changes"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Allow openpilot to change lanes.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_lane.png",
          refreshes_visibility=True,
        ),
        {
          "nudgeless_lane_change": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="NudgelessLaneChange",
            title=tr_noop("Automatic Lane Changes"),
            description=tr_noop("<b>When the turn signal is on, openpilot will automatically change lanes.</b> No steering-wheel nudge required!"),
            refreshes_visibility=True,
          ),

          "lane_change_time": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LaneChangeTime",
            title=tr_noop("Lane Change Delay"),
            description=tr_noop("<b>Delay between turn signal activation and the start of an automatic lane change.</b>"),
            minimum=0,
            maximum=5,
            step=0.1,
            unit=" seconds",
            value_map={0: "Instant", 1: "1 second"},
            visible_state="_nudgeless_visible",
          ),

          "minimum_lane_change_speed": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="MinimumLaneChangeSpeed",
            title=tr_noop("Minimum Lane Change Speed"),
            description=tr_noop("<b>Lowest speed at which openpilot will change lanes.</b>"),
            minimum=0,
            maximum=99,
            unit=" mph",
            unit_type=UnitType.SPEED,
            value_map={0: "Off"},
          ),

          "lane_detection_width": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LaneDetectionWidth",
            title=tr_noop("Minimum Lane Width"),
            description=tr_noop("<b>Prevent automatic lane changes into lanes narrower than the set width.</b>"),
            minimum=0,
            maximum=15,
            step=0.1,
            unit=" feet",
            unit_type=UnitType.LANE_WIDTH,
            value_map={0: "Off"},
            visible_state="_nudgeless_visible",
          ),

          "one_lane_change": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="OneLaneChange",
            title=tr_noop("One Lane Change Per Signal"),
            description=tr_noop("<b>Limit automatic lane changes to one per turn-signal activation.</b>"),
          ),
        },
      ),

      "lateral_tuning": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="LateralTune",
          title=tr_noop("Lateral Tuning"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Miscellaneous steering control changes</b> to fine-tune how openpilot drives."),
          icon="frogpilot/assets/toggle_icons/icon_lateral_tune.png",
        ),
        {
          "turn_desires": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="TurnDesires",
            title=tr_noop("Force Turn Desires Below Lane Change Speed"),
            description=tr_noop("<b>While driving below the minimum lane change speed with an active turn signal, instruct openpilot to turn left/right.</b>"),
          ),

          "nnff": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="NNFF",
            title=tr_noop("Neural Network Feedforward (NNFF)"),
            description=tr_noop("<b>Twilsonco's \"Neural Network FeedForward\" controller.</b> Uses a trained neural network model to predict steering torque based on vehicle speed, roll, and past/future planned path data for smoother, model-based steering."),
            reboot=True,
            visible_state="_nnff_visible",
            refreshes_visibility=True,
          ),

          "nnff_lite": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="NNFFLite",
            title=tr_noop("Neural Network Feedforward (NNFF) Lite"),
            description=tr_noop("<b>A lightweight version of Twilsonco's \"Neural Network FeedForward\" controller.</b> Uses the \"look-ahead\" planned lateral jerk logic from the full model to help smoothen steering adjustments in curves, but does not use the full neural network for torque calculation."),
            reboot=True,
            visible_state="_nnff_lite_visible",
          ),
        },
      ),

      "quality_of_life": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="QOLLateral",
          title=tr_noop("Quality of Life"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>Steering control changes to fine-tune how openpilot drives.</b>"),
          icon="frogpilot/assets/toggle_icons/icon_quality_of_life.png",
        ),
        {
          "pause_lateral_speed": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="PauseLateralSpeed",
            title=tr_noop("Pause Steering Below"),
            description=tr_noop("<b>Pause steering below the set speed.</b>"),
            options=(tr_noop("Turn Signal Only"),),
            child_param_keys=("PauseLateralOnSignal",),
            minimum=0,
            maximum=99,
            value_map={0: "Off"},
          ),
        },
      ),
    },
  ),

  "theme": PanelMetadata(
    sections={
      "root": (
        "custom_themes",
        "holiday_themes",
        "rainbow_path",
        "random_events",
        "random_themes",
        "startup_alert",
      ),

      "custom_themes": (
        "color_scheme",
        "distance_icon_pack",
        "icon_pack",
        "signal_animation",
        "sound_pack",
        "wheel_icon",
        "download_status_label",
      ),
    },
    items={
      "custom_themes": (
        MetadataItem(
          widget_type=WidgetType.TUNING_MANAGE_TOGGLE,
          param_key="CustomThemes",
          title=tr_noop("Custom Themes"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>The overall look and feel of openpilot.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
          icon="frogpilot/assets/toggle_icons/icon_frog.png",
        ),
        {
          "color_scheme": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="ColorScheme",
            title=tr_noop("Color Scheme"),
            description=tr_noop("<b>The color scheme used throughout openpilot.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "distance_icon_pack": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="DistanceIconPack",
            title=tr_noop("Distance Button"),
            description=tr_noop("<b>The distance button icons shown on the driving screen.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "icon_pack": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="IconPack",
            title=tr_noop("Icon Pack"),
            description=tr_noop("<b>The icon style used across openpilot.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "signal_animation": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="SignalAnimation",
            title=tr_noop("Turn Signal"),
            description=tr_noop("<b>Themed turn-signal animations.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "sound_pack": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="SoundPack",
            title=tr_noop("Sound Pack"),
            description=tr_noop("<b>The sound pack used by openpilot.</b> Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "wheel_icon": MetadataItem(
            widget_type=WidgetType.BUTTONS,
            param_key="WheelIcon",
            title=tr_noop("Steering Wheel"),
            description=tr_noop("<b>The steering-wheel icon</b> shown at the top-right of the driving screen. Use the \"Theme Maker\" in \"The Pond\" to create and share your own themes!"),
            buttons=(
              ButtonSpec(text=tr_noop("DELETE"), action="delete"),
              ButtonSpec(text=tr_noop("DOWNLOAD"), action="download"),
              ButtonSpec(text=tr_noop("SELECT"), action="select"),
            ),
          ),

          "download_status_label": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("Download Status"),
            description="",
          ),
        },
      ),

      "holiday_themes": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="HolidayThemes",
        title=tr_noop("Holiday Themes"),
        description=tr_noop("<b>Themes based on U.S. holidays.</b> Minor holidays last one day; major holidays (Christmas, Easter, Halloween) run for a full week."),
        icon="frogpilot/assets/toggle_icons/icon_calendar.png",
      ),

      "rainbow_path": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="RainbowPath",
        title=tr_noop("Rainbow Path"),
        description=tr_noop("<b>Color the driving path like a Mario Kart-style \"Rainbow Road\".</b>"),
        icon="frogpilot/assets/toggle_icons/icon_rainbow.png",
      ),

      "random_events": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="RandomEvents",
        title=tr_noop("Random Events"),
        description=tr_noop("<b>Occasional on-screen effects triggered by driving conditions.</b> These are purely a visual and don't impact how openpilot drives!"),
        icon="frogpilot/assets/toggle_icons/icon_random.png",
      ),

      "random_themes": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="RandomThemes",
        title=tr_noop("Random Themes"),
        description=tr_noop("<b>Pick a random theme between each drive</b> from the themes you have downloaded. Great for variety without changing settings while driving."),
        icon="frogpilot/assets/toggle_icons/icon_random_themes.png",
        options=(tr_noop("Include Holiday Themes"),),
        child_param_keys=("RandomThemesHolidays",),
      ),

      "startup_alert": MetadataItem(
        widget_type=WidgetType.BUTTONS,
        title=tr_noop("Startup Alert"),
        description=tr_noop("<b>Customize the \"Startup Alert\" message</b> shown at the start of each drive."),
        icon="frogpilot/assets/toggle_icons/icon_message.png",
        buttons=(
          ButtonSpec(text=tr_noop("STOCK"), action="stock"),
          ButtonSpec(text=tr_noop("FROGPILOT"), action="frogpilot"),
          ButtonSpec(text=tr_noop("CUSTOM"), action="custom"),
          ButtonSpec(text=tr_noop("CLEAR"), action="clear"),
        ),
        child_param_keys=(
          "StartupMessageTop",
          "StartupMessageBottom",
        ),
      ),
    },
  ),

  "utilities": PanelMetadata(
    sections={
      "root": (
        "debug_mode",
        "force_drive_state",
      ),
    },
    items={
      "debug_mode": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="DebugMode",
        title=tr_noop("Debug Mode"),
        description=tr_noop("<b>Use all of FrogPilot's developer metrics on your next drive</b> to diagnose issues and improve bug reports."),
      ),

      "force_drive_state": MetadataItem(
        widget_type=WidgetType.MULTIPLE_BUTTON,
        title=tr_noop("Force Drive State"),
        description=tr_noop("<b>Force openpilot to be offroad or onroad.</b>"),
        options=(
          tr_noop("OFFROAD"),
          tr_noop("ONROAD"),
          tr_noop("OFF"),
        ),
        child_param_keys=(
          "ForceOffroad",
          "ForceOnroad",
        ),
      ),
    },
  ),

  "vehicle_settings": PanelMetadata(
    sections={
      "root": (
        "car_make",
        "car_model",
        "force_fingerprint",
        "disable_openpilot_longitudinal",
        "gm_toggles",
        "hkg_toggles",
        "subaru_toggles",
        "toyota_toggles",
        "vehicle_info",
      ),

      "gm_toggles": (
        "volt_sng",
      ),

      "hkg_toggles": (
        "taco_tune_hacks",
      ),

      "subaru_toggles": (
        "subaru_sng",
      ),

      "toyota_toggles": (
        "toyota_doors",
        "cluster_offset",
        "frogs_go_moos_tweak",
        "lock_doors_timer",
        "sng_hack",
      ),

      "vehicle_info": (
        "hardware_detected",
        "blind_spot_support",
        "pedal_support",
        "openpilot_longitudinal",
        "radar_support",
        "sdsu_support",
        "sng_support",
      ),
    },
    items={
      "car_make": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="CarMake",
        title=tr_noop("Car Make"),
        button_text=tr_noop("SELECT"),
        description=tr_noop(""),
      ),

      "car_model": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="CarModel",
        title=tr_noop("Car Model"),
        button_text=tr_noop("SELECT"),
        description=tr_noop(""),
        child_param_keys=("CarModelName",),
      ),

      "force_fingerprint": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="ForceFingerprint",
        title=tr_noop("Disable Automatic Fingerprint Detection"),
        description=tr_noop("<b>Force the selected fingerprint</b> and prevent it from ever changing."),
      ),

      "disable_openpilot_longitudinal": MetadataItem(
        widget_type=WidgetType.TUNING_TOGGLE,
        param_key="DisableOpenpilotLongitudinal",
        title=tr_noop("Disable openpilot Longitudinal Control"),
        description=tr_noop("<b>Disable openpilot longitudinal</b> and use the car's stock ACC instead."),
        reboot=True,
      ),

      "gm_toggles": (
        MetadataItem(
          widget_type=WidgetType.BUTTON,
          title=tr_noop("General Motors Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>FrogPilot features for General Motors vehicles.</b>"),
          visible_state="_is_gm",
        ),
        {
          "volt_sng": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="VoltSNG",
            title=tr_noop("Stop-and-Go Hack"),
            description=tr_noop("<b>Force stop-and-go</b> on the 2017 Chevy Volt."),
            visible_state=("_is_gm", "_has_openpilot_longitudinal", "_no_sng"),
          ),
        },
      ),

      "hkg_toggles": (
        MetadataItem(
          widget_type=WidgetType.BUTTON,
          title=tr_noop("Hyundai/Kia/Genesis Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>FrogPilot features for Genesis, Hyundai, and Kia vehicles.</b>"),
          visible_state="_is_hkg",
        ),
        {
          "taco_tune_hacks": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="TacoTuneHacks",
            title=tr_noop("\"Taco Bell Run\" Torque Hack"),
            description=tr_noop("<b>The steering torque hack from comma's 2022 \"Taco Bell Run\".</b> Designed to increase steering torque at low speeds for left and right turns."),
            reboot=True,
            visible_state="_is_hkg",
          ),
        },
      ),

      "subaru_toggles": (
        MetadataItem(
          widget_type=WidgetType.BUTTON,
          title=tr_noop("Subaru Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>FrogPilot features for Subaru vehicles.</b>"),
          visible_state="_is_subaru",
        ),
        {
          "subaru_sng": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="SubaruSNG",
            title=tr_noop("Stop and Go"),
            description=tr_noop("Stop and go for supported Subaru vehicles."),
            visible_state=("_is_subaru", "_has_sng"),
          ),
        },
      ),

      "toyota_toggles": (
        MetadataItem(
          widget_type=WidgetType.BUTTON,
          title=tr_noop("Toyota/Lexus Settings"),
          button_text=tr_noop("MANAGE"),
          description=tr_noop("<b>FrogPilot features for Lexus and Toyota vehicles.</b>"),
          visible_state="_is_toyota",
        ),
        {
          "cluster_offset": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE_BUTTON,
            param_key="ClusterOffset",
            title=tr_noop("Dashboard Speed Offset"),
            description=tr_noop("<b>The speed offset openpilot uses to match the speed on the dashboard display.</b>"),
            minimum=1.000,
            maximum=1.050,
            step=0.001,
            unit="x",
            button_text=tr_noop("Reset"),
            visible_state="_is_toyota",
          ),

          "frogs_go_moos_tweak": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="FrogsGoMoosTweak",
            title=tr_noop("FrogsGoMoo's Personal Tweaks"),
            description=tr_noop("<b>Personal tweaks by FrogsGoMoo for quicker acceleration and smoother braking.</b>"),
            visible_state=("_is_toyota", "_has_openpilot_longitudinal"),
            refreshes_visibility=True,
          ),

          "lock_doors_timer": MetadataItem(
            widget_type=WidgetType.TUNING_PARAM_VALUE,
            param_key="LockDoorsTimer",
            title=tr_noop("Lock Doors On Ignition Off After"),
            description=tr_noop("<b>Automatically lock the doors on ignition off</b> when no one is detected in the front seats."),
            minimum=0,
            maximum=300,
            step=5,
            unit=" seconds",
            value_map={0: "Never"},
            visible_state="_is_toyota",
          ),

          "sng_hack": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="SNGHack",
            title=tr_noop("Stop-and-Go Hack"),
            description=tr_noop("<b>Force stop-and-go</b> on Lexus/Toyota vehicles without stock stop-and-go functionality."),
            visible_state="_sng_hack_visible",
          ),

          "toyota_doors": MetadataItem(
            widget_type=WidgetType.TUNING_TOGGLE,
            param_key="ToyotaDoors",
            title=tr_noop("Automatically Lock/Unlock Doors"),
            description=tr_noop("<b>Automatically lock/unlock doors</b> when shifting in and out of drive."),
            options=(
              tr_noop("Lock"),
              tr_noop("Unlock"),
            ),
            child_param_keys=(
              "LockDoors",
              "UnlockDoors",
            ),
            visible_state="_is_toyota",
          ),
        },
      ),

      "vehicle_info": (
        MetadataItem(
          widget_type=WidgetType.BUTTON,
          title=tr_noop("Vehicle Info"),
          button_text=tr_noop("VIEW"),
          description=tr_noop("<b>Information about your vehicle in regards to openpilot support and functionality.</b>"),
        ),
        {
          "blind_spot_support": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("Blind Spot Support"),
            description=tr_noop("<b>Does openpilot use the vehicle's blind spot data?</b>"),
          ),

          "hardware_detected": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("3rd Party Hardware Detected"),
            description=tr_noop("<b>Detected 3rd party hardware.</b>"),
          ),

          "openpilot_longitudinal": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("openpilot Longitudinal Support"),
            description=tr_noop("<b>Can openpilot control the vehicle's acceleration and braking?</b>"),
          ),

          "pedal_support": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("comma Pedal Support"),
            description=tr_noop("<b>Does your vehicle support the \"comma pedal\"?</b>"),
          ),

          "radar_support": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("Radar Support"),
            description=tr_noop("<b>Does openpilot use the vehicle's radar data</b> alongside the device's camera for tracking lead vehicles?"),
          ),

          "sdsu_support": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("SDSU Support"),
            description=tr_noop("<b>Does your vehicle support \"SDSUs\"?</b>"),
          ),

          "sng_support": MetadataItem(
            widget_type=WidgetType.TEXT,
            title=tr_noop("Stop-and-Go Support"),
            description=tr_noop("<b>Does your vehicle support stop-and-go driving?</b>"),
          ),
        },
      ),
    },
  ),

  "wheel_controls": PanelMetadata(
    sections={
      "root": (
        "distance_button_control",
        "long_distance_button_control",
        "very_long_distance_button_control",
        "lkas_button_control",
      ),
    },
    items={
      "distance_button_control": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="DistanceButtonControl",
        title=tr_noop("Distance Button"),
        button_text=tr_noop("SELECT"),
        description=tr_noop("<b>Action performed when the \"Distance\" button is pressed.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_mute.png",

        options=(
          tr_noop("No Action"),
          tr_noop("Change \"Personality Profile\""),
          tr_noop("Force openpilot to Coast"),
          tr_noop("Pause Steering"),
          tr_noop("Pause Acceleration/Braking"),
          tr_noop("Toggle \"Experimental Mode\" On/Off"),
          tr_noop("Toggle \"Traffic Mode\" On/Off"),
        ),
      ),

      "long_distance_button_control": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="LongDistanceButtonControl",
        title=tr_noop("Distance Button (Long Press)"),
        button_text=tr_noop("SELECT"),
        description=tr_noop("<b>Action performed when the \"Distance\" button is pressed for more than 0.5 seconds.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_mute.png",

        options=(
          tr_noop("No Action"),
          tr_noop("Change \"Personality Profile\""),
          tr_noop("Force openpilot to Coast"),
          tr_noop("Pause Steering"),
          tr_noop("Pause Acceleration/Braking"),
          tr_noop("Toggle \"Experimental Mode\" On/Off"),
          tr_noop("Toggle \"Traffic Mode\" On/Off"),
        ),
      ),

      "very_long_distance_button_control": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="VeryLongDistanceButtonControl",
        title=tr_noop("Distance Button (Very Long Press)"),
        button_text=tr_noop("SELECT"),
        description=tr_noop("<b>Action performed when the \"Distance\" button is pressed for more than 2.5 seconds.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_mute.png",

        options=(
          tr_noop("No Action"),
          tr_noop("Change \"Personality Profile\""),
          tr_noop("Force openpilot to Coast"),
          tr_noop("Pause Steering"),
          tr_noop("Pause Acceleration/Braking"),
          tr_noop("Toggle \"Experimental Mode\" On/Off"),
          tr_noop("Toggle \"Traffic Mode\" On/Off"),
        ),
      ),

      "lkas_button_control": MetadataItem(
        widget_type=WidgetType.BUTTON,
        param_key="LKASButtonControl",
        title=tr_noop("LKAS Button"),
        button_text=tr_noop("SELECT"),
        description=tr_noop("<b>Action performed when the \"LKAS\" button is pressed.</b>"),
        icon="frogpilot/assets/toggle_icons/icon_mute.png",

        options=(
          tr_noop("No Action"),
          tr_noop("Change \"Personality Profile\""),
          tr_noop("Force openpilot to Coast"),
          tr_noop("Pause Steering"),
          tr_noop("Pause Acceleration/Braking"),
          tr_noop("Toggle \"Experimental Mode\" On/Off"),
          tr_noop("Toggle \"Traffic Mode\" On/Off"),
        ),
      ),
    },
  ),
}
