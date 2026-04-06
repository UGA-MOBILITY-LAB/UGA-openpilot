import math
import numpy as np
import sounddevice as sd
import wave

from pathlib import Path

from openpilot.common.basedir import BASEDIR
from openpilot.frogpilot.common import frogpilot_variables
from openpilot.selfdrive.ui.soundd import AMBIENT_DB, DB_SCALE, MAX_VOLUME, MIN_VOLUME, SAMPLE_RATE, VOLUME_BASE, AudibleAlert, sound_list

AUTO_VOLUME = 101
STOCK_SOUND_PATH = Path(BASEDIR) / "selfdrive" / "assets" / "sounds"


class FrogPilotSoundPreview:
  @staticmethod
  def _read_wav(sound_path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(sound_path), "rb") as wav_file:
      sample_rate = wav_file.getframerate()
      channels = wav_file.getnchannels()
      frames = wav_file.getnframes()
      audio = np.frombuffer(wav_file.readframes(frames), dtype=np.int16).astype(np.float32) / (2**15)

    if sample_rate != SAMPLE_RATE:
      raise ValueError(f"Unexpected sample rate for preview file {sound_path}: {sample_rate}")
    if channels > 1:
      audio = audio.reshape(-1, channels)

    return audio, sample_rate

  @staticmethod
  def _resolve_sound_path(alert_name: str) -> Path | None:
    alert = getattr(AudibleAlert, alert_name, None)
    sound = sound_list.get(alert)
    if sound is None:
      return None

    frogpilot_toggles = frogpilot_variables.get_frogpilot_toggles()
    sound_directory = STOCK_SOUND_PATH if frogpilot_toggles.sound_pack == "stock" else frogpilot_variables.ACTIVE_THEME_PATH / "sounds"

    filename, _, _ = sound
    fallback_filename = "engage.wav" if filename == "startup.wav" else filename
    candidate_paths = [sound_directory / filename]
    if "_tizi" in filename:
      candidate_paths.append(sound_directory / filename.replace("_tizi", ""))
    candidate_paths.append(STOCK_SOUND_PATH / fallback_filename)

    return next((path for path in candidate_paths if path.exists()), None)

  @staticmethod
  def _volume_gain(volume: float | int) -> float:
    if volume <= 0:
      return 0.0

    if volume >= AUTO_VOLUME:
      auto_weighted_db = AMBIENT_DB + DB_SCALE
      auto_volume = ((auto_weighted_db - AMBIENT_DB) / DB_SCALE) * (MAX_VOLUME - MIN_VOLUME) + MIN_VOLUME
      return math.pow(VOLUME_BASE, (auto_volume - 1))

    return max(0.0, min(float(volume) / 100.0, MAX_VOLUME))

  @classmethod
  def play_preview(cls, sound_path: Path, volume: float | int) -> None:
    gain = cls._volume_gain(volume)
    if gain <= 0:
      return

    audio, sample_rate = cls._read_wav(sound_path)
    sd.play(audio * gain, samplerate=sample_rate)

  def preview_alert(self, alert_name: str, volume: float | int) -> None:
    sound_path = self._resolve_sound_path(alert_name)
    if sound_path is None:
      return

    self.stop()
    self.play_preview(sound_path, volume)

  @staticmethod
  def stop() -> None:
    sd.stop()
