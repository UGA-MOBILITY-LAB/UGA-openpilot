from cereal import messaging

from openpilot.common.params import Params


class FrogPilotUIState:
  _instance: 'FrogPilotUIState | None' = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._initialize()
    return cls._instance

  def _initialize(self) -> None:
    self.params = Params()

    self.pm = messaging.PubMaster([])

  def update(self) -> None:
    pass


frogpilot_ui_state = FrogPilotUIState()
