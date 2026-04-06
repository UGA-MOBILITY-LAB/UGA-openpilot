from openpilot.frogpilot.system.sound_preview import FrogPilotSoundPreview
from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget

PANEL_KEY = "alerts_and_sounds"


class FrogPilotSoundsPanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()
    self._sound_preview = FrogPilotSoundPreview()

    subviews = {}

    subviews["alert_volume_control"] = self._build_section_scroller(PANEL_KEY, "alert_volume_control", subviews)
    subviews["frogpilot_alerts"] = self._build_section_scroller(PANEL_KEY, "frogpilot_alerts", subviews)

    root_scroller = self._build_section_scroller(PANEL_KEY, "root", subviews)

    self._initialize_views(root_scroller, *subviews.values())

  def _test_alert(self, param_key: str) -> None:
    alert_name = param_key.removesuffix("Volume")
    alert_name = alert_name[:1].lower() + alert_name[1:]
    self._sound_preview.preview_alert(alert_name, self.params.get(param_key))

  def hide_event(self) -> None:
    self._sound_preview.stop()
    super().hide_event()
