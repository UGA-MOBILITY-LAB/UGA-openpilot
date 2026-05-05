#!/usr/bin/env bash
# op_pc_run.sh — Launch FrogPilot on PC with a video file or rosbag as the camera source.
#
# Modes:
#   ./uga/launch/op_pc_run.sh ~/dashcam_test.mp4
#       MP4/video mode — uses uga/tools/video_to_vipc.py (no ROS required).
#       Good for hello-world with any handheld dashcam footage.
#
#   ./uga/launch/op_pc_run.sh --rosbag ~/recording_dir
#       rosbag mode — replays a rosbag2 directory. Real Lucid frames from
#       /camera/image_rect (BAYER_RG_8 2448x2048 @ 5Hz) pipe through
#       uga/tools/ros_image_to_vipc.py. This is the recommended Step 1 path
#       and the same code carries forward to Step 2 (live driver).
#
#   ./uga/launch/op_pc_run.sh --live
#       live mode (on vehicle) — assumes ds_video_gst is already running and
#       publishing /camera/image_rect. Skips bag play, only starts the bridge
#       and manager.
#
# Stop: Ctrl-C (kills all child processes).

set -e

MODE=""
INPUT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --rosbag) MODE="rosbag"; shift; INPUT="$1"; shift ;;
        --live)   MODE="live";   shift ;;
        -h|--help)
            sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *)
            if [ -z "$INPUT" ] && [ -z "$MODE" ]; then
                MODE="video"
                INPUT="$1"
            else
                echo "ERROR: unknown arg: $1" >&2
                exit 1
            fi
            shift ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "Usage:"
    echo "  $0 ~/dashcam_test.mp4              (mp4 mode)"
    echo "  $0 --rosbag ~/recording_dir        (rosbag mode, recommended)"
    echo "  $0 --live                          (on vehicle, ds_video_gst running)"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Force-disable driverview so the real native camerad doesn't compete with
# our fake VisionIPC publisher (driverview gates camerad in process_config.py).
python3 -c "from openpilot.common.params import Params; Params().put_bool('IsDriverViewEnabled', False)" \
    2>/dev/null || true

PIDS=()
cleanup() {
    for pid in "${PIDS[@]}"; do
        kill -TERM "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

source_ros() {
    if [ -z "${ROS_DISTRO:-}" ]; then
        if [ -f /opt/ros/humble/setup.bash ]; then
            # shellcheck disable=SC1091
            source /opt/ros/humble/setup.bash
        else
            echo "ERROR: ROS 2 not sourced and /opt/ros/humble/setup.bash missing" >&2
            exit 1
        fi
    fi
}

case "$MODE" in
    video)
        if [ ! -f "$INPUT" ]; then
            echo "ERROR: video file not found: $INPUT" >&2
            exit 1
        fi
        echo "[op_pc_run] video mode: $INPUT"
        python3 uga/tools/video_to_vipc.py "$INPUT" --wide --loop &
        PIDS+=($!)
        sleep 1
        ;;

    rosbag)
        if [ ! -d "$INPUT" ] && [ ! -f "${INPUT}.db3" ] && [ ! -f "$INPUT" ]; then
            echo "ERROR: rosbag not found at: $INPUT" >&2
            exit 1
        fi
        source_ros
        echo "[op_pc_run] rosbag mode: $INPUT"
        # bridge first so it has the topic ready when bag play starts
        python3 uga/tools/ros_image_to_vipc.py &
        PIDS+=($!)
        sleep 2
        ros2 bag play "$INPUT" --loop &
        PIDS+=($!)
        sleep 1
        ;;

    live)
        source_ros
        echo "[op_pc_run] live mode (assumes ds_video_gst already publishing /camera/image_rect)"
        python3 uga/tools/ros_image_to_vipc.py &
        PIDS+=($!)
        sleep 2
        ;;
esac

# Foreground: standard launch — manager auto-detects PC mode
exec ./launch_chffrplus.sh
