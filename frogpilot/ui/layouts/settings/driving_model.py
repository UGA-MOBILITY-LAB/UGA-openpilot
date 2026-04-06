from openpilot.frogpilot.system.ui.widgets import FrogPilotWidget

PANEL_KEY = "driving_model"


class FrogPilotDrivingModelPanel(FrogPilotWidget):
  def __init__(self):
    super().__init__()

    subviews = {}

    root_scroller = self._build_section_scroller(PANEL_KEY, "root", subviews)

    self._initialize_views(root_scroller)

  def _value_select_model(self) -> str:
    return self.params.get("DrivingModelName") or ""
