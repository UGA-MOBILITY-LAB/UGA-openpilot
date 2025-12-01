import json

from cereal import messaging

from openpilot.common.params import Params

from openpilot.frogpilot.common.frogpilot_variables import FrogPilotVariables


class FrogPilotUIState:
  _instance: 'FrogPilotUIState | None' = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._initialize()
    return cls._instance

  def _initialize(self) -> None:
    self.params = Params()

    self.pm = messaging.PubMaster(["frogpilotUI"])

    self.frogpilot_variables = FrogPilotVariables()
    self.frogpilot_toggles = self.frogpilot_variables.frogpilot_toggles

    self._publish()

  def _publish(self) -> None:
    msg = messaging.new_message("frogpilotUI")
    msg.frogpilotUI.frogpilotToggles = json.dumps(vars(self.frogpilot_toggles))
    self.pm.send("frogpilotUI", msg)

  def update(self) -> None:
    pass

  def update_toggles(self, started=False, holiday_theme="stock") -> None:
    self.frogpilot_toggles = self.frogpilot_variables.update(holiday_theme=holiday_theme, started=started)
    self._publish()


frogpilot_ui_state = FrogPilotUIState()
