#!/usr/bin/env bash
# op_pc_run.sh — Launch FrogPilot on PC with a video file as the camera source.
#
# Workflow:
#   1. Start uga/tools/video_to_vipc.py in the background to publish camera
#      frames + roadCameraState into the VisionIPC "camerad" namespace.
#   2. Start ./launch_chffrplus.sh which spawns manager. On PC the real
#      `camerad` native binary stays gated behind the `driverview` condition
#      (system/manager/process_config.py:driverview = started or
#      IsDriverViewEnabled). With IsDriverViewEnabled=false the real camerad
#      will not race with our fake.
#
# Usage:
#     ./uga/launch/op_pc_run.sh [VIDEO_PATH]
#
# Defaults:
#     VIDEO_PATH defaults to ~/dashcam_test.mp4
#
# Stop:
#     Ctrl-C — both video_to_vipc and launch_chffrplus.sh are killed.

set -e

VIDEO_PATH="${1:-$HOME/dashcam_test.mp4}"

if [ ! -f "$VIDEO_PATH" ]; then
    echo "ERROR: video not found at $VIDEO_PATH" >&2
    echo "Usage: $0 [path/to/video.mp4]" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Belt-and-suspenders: ensure driver view is OFF so manager does not start the
# real camerad and conflict with our fake VisionIPC publisher.
python3 -c "from openpilot.common.params import Params; Params().put_bool('IsDriverViewEnabled', False)" \
    2>/dev/null || true

# Background: video → VisionIPC + cereal roadCameraState
python3 uga/tools/video_to_vipc.py "$VIDEO_PATH" --wide --loop &
VIPC_PID=$!

cleanup() {
    kill -TERM "$VIPC_PID" 2>/dev/null || true
    wait "$VIPC_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Give vipc 1 sec to bring the server up before manager attaches modeld
sleep 1

# Foreground: standard launch — manager auto-detects PC mode
exec ./launch_chffrplus.sh
