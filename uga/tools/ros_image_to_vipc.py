#!/usr/bin/env python3
"""
ros_image_to_vipc.py — Bridge a ROS 2 sensor_msgs/Image topic into openpilot's
VisionIPC + cereal roadCameraState.

Replaces video_to_vipc.py for the recommended Step 1 / Step 2 path: the input
is a real Lucid frame stream (BAYER_RG_8 2448x2048 @ 5Hz from ds_video_gst on
Mach-E), either replayed from a rosbag or read live from the camera driver.
The same code handles both — only the upstream "ros2 bag play" vs live driver
differs.

Run order on Nuvo:

    Terminal A (replay mode):
        source /opt/ros/humble/setup.bash
        ros2 bag play ~/recorded.bag --loop

    Terminal A (live mode, on vehicle):
        ros2 launch uga devices.launch.xml      # in UGA-AUTOWARE

    Terminal B:
        source /opt/ros/humble/setup.bash
        cd ~/UGA-openpilot
        python3 uga/tools/ros_image_to_vipc.py

    Terminal C:
        cd ~/UGA-openpilot
        ./launch_chffrplus.sh

    (or use uga/launch/op_pc_run.sh --rosbag <bag-dir> to wrap A+B+C)

Conversion path:
    sensor_msgs/Image (BAYER_RG_8) -> cv2 demosaic -> BGR
                                   -> PyAV reformat -> NV12 1928x1208
                                   -> VisionIpcServer.send()
                                   -> cereal pubmaster (roadCameraState)

Mach-E is monocular: WIDE_ROAD stream is mirrored from ROAD by default
(modeld:87,113-114 hard-codes two image inputs). Use --no-wide to disable.

Frame rate: Lucid runs at 5 Hz; modeld expects ~20 Hz. By default each frame
is repeated 4 times (--upsample 4) with synthesized sub-frame timestamps.

Known limitations / TODOs:
    1. liveCalibration message is not produced here — assumes manager runs
       calibrationd which infers calibration from the synthesized stream. If
       modeld stalls on calibration, we may need to publish a fake
       liveCalibration message with Lucid intrinsics.
    2. transform is identity. For the Mach-E URDF the camera is at
       (1.730, 0, 1.714) base_footprint forward. If modeld needs a non-trivial
       transform we'll plug it in here.
    3. BAYER pattern auto-detection covers RGGB and GBRG. If Lucid actually
       outputs GRBG/BGGR, edit bayer_to_nv12() below.
    4. Repeating frames at 4x is an upsample hack — the model sees the same
       pixels 4 times in a row. May confuse temporal dynamics. Long-term:
       run the Lucid at 20 Hz natively.
"""

import argparse
import sys

import numpy as np
import cv2
import av

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image
except ImportError:
    print("ERROR: rclpy not found. Source ROS 2 first:", file=sys.stderr)
    print("    source /opt/ros/humble/setup.bash", file=sys.stderr)
    sys.exit(1)

import cereal.messaging as messaging
from msgq.visionipc import VisionIpcServer, VisionStreamType


ROAD_W = 1928
ROAD_H = 1208


def bayer_to_nv12(bayer_bytes: bytes, raw_w: int, raw_h: int, encoding: str) -> bytes:
    """BAYER -> demosaic -> resize -> NV12 raw bytes."""
    bayer = np.frombuffer(bayer_bytes, dtype=np.uint8).reshape((raw_h, raw_w))

    enc = encoding.lower()
    if "rggb" in enc or enc in ("bayer_rg8", "bayer_rggb8"):
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BayerRG2BGR)
    elif "gbrg" in enc or enc == "bayer_gbrg8":
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BayerGB2BGR)
    elif "grbg" in enc:
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BayerGR2BGR)
    elif "bggr" in enc:
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BayerBG2BGR)
    else:
        # default to RGGB which is what ds_video_gst emits on the Lucid
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BayerRG2BGR)

    # PyAV: BGR -> NV12 with target size in one reformat
    av_frame = av.VideoFrame.from_ndarray(bgr, format="bgr24")
    nv12 = av_frame.reformat(width=ROAD_W, height=ROAD_H, format="nv12")
    return nv12.to_ndarray().tobytes()


class RosImageToVipc(Node):

    def __init__(self, topic: str, upsample: int, wide: bool):
        super().__init__("ros_image_to_vipc")
        self.upsample = max(1, upsample)
        self.wide = wide
        self.frame_id = 0
        self.skipped_warns = 0

        self.msg_names = ["roadCameraState"]
        if wide:
            self.msg_names.append("wideRoadCameraState")
        self.pm = messaging.PubMaster(self.msg_names)

        self.server = VisionIpcServer("camerad")
        self.server.create_buffers(
            VisionStreamType.VISION_STREAM_ROAD, 20, False, ROAD_W, ROAD_H,
        )
        if wide:
            self.server.create_buffers(
                VisionStreamType.VISION_STREAM_WIDE_ROAD, 20, False, ROAD_W, ROAD_H,
            )
        self.server.start_listener()

        wide_note = " + WIDE_ROAD mirror (Mach-E is monocular)" if wide else ""
        self.get_logger().info(
            f"VisionIPC 'camerad' up: {ROAD_W}x{ROAD_H} NV12 ROAD{wide_note}"
        )

        self.sub = self.create_subscription(Image, topic, self.on_image, 10)
        self.get_logger().info(
            f"Subscribed to '{topic}' (upsample x{self.upsample})"
        )

    def on_image(self, msg: Image):
        try:
            nv12_bytes = bayer_to_nv12(
                bytes(msg.data), msg.width, msg.height, msg.encoding,
            )
        except Exception as e:
            self.get_logger().error(f"convert failed (encoding={msg.encoding}): {e}")
            return

        base_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
        for i in range(self.upsample):
            ts_ns = base_ns + i * 50_000_000  # 50 ms spacing per repeat (20 Hz)

            self.server.send(
                VisionStreamType.VISION_STREAM_ROAD, nv12_bytes, self.frame_id, ts_ns, ts_ns,
            )
            if self.wide:
                self.server.send(
                    VisionStreamType.VISION_STREAM_WIDE_ROAD, nv12_bytes, self.frame_id, ts_ns, ts_ns,
                )

            for name in self.msg_names:
                dat = messaging.new_message(name, valid=True)
                fd = getattr(dat, name)
                fd.frameId = self.frame_id
                fd.timestampSof = ts_ns
                fd.timestampEof = ts_ns
                fd.transform = [1.0, 0.0, 0.0,
                                0.0, 1.0, 0.0,
                                0.0, 0.0, 1.0]
                self.pm.send(name, dat)

            self.frame_id += 1

        if self.frame_id % 100 == 0:
            self.get_logger().info(
                f"published frame_id={self.frame_id} (input encoding={msg.encoding} {msg.width}x{msg.height})"
            )


def main():
    p = argparse.ArgumentParser(
        description="Bridge ROS 2 sensor_msgs/Image to openpilot VisionIPC + cereal",
    )
    p.add_argument(
        "--topic", default="/camera/image_rect",
        help="ROS image topic (default /camera/image_rect from ds_video_gst)",
    )
    p.add_argument(
        "--upsample", type=int, default=4,
        help="Repeat each frame N times (default 4 to bring 5 Hz Lucid up to 20 Hz)",
    )
    p.add_argument(
        "--no-wide", action="store_true",
        help="Disable WIDE_ROAD mirror (default: enabled, Mach-E is monocular)",
    )
    args = p.parse_args()

    rclpy.init()
    try:
        node = RosImageToVipc(args.topic, args.upsample, not args.no_wide)
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
