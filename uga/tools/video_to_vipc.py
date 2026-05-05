#!/usr/bin/env python3
"""
video_to_vipc.py — Feed a video file into openpilot's modeld via VisionIPC.

Substitutes for the camerad process when running offline on PC. Reads frames
from an MP4/MKV/etc., converts to NV12, pushes to a VisionIPC server under the
"camerad" namespace (so modeld attaches transparently), and publishes a cereal
roadCameraState message per frame.

Usage:
    python3 uga/tools/video_to_vipc.py path/to/dashcam.mp4 \
        [--width 1928 --height 1208 --fps 20] [--wide] [--loop]

Run order on PC:
    1. (terminal A) python3 uga/tools/video_to_vipc.py ~/dashcam_test.mp4 --wide --loop
    2. (terminal B) ./launch_chffrplus.sh
       — manager will start modeld, which connects to the VisionIPC "camerad"
         endpoint we created. modeld doesn't care that the publisher is us, not
         the real camerad, as long as the stream + cereal messages arrive.

Origin / lineage:
    Modeled after the (deleted-in-FrogPilot) commaai upstream `tools/webcam/camerad.py`
    and `tools/webcam/camera.py`. Adapted for video-file input (no webcam) and
    target resolution that matches openpilot's model expectations.

Known issues / TODO:
    1. Resolution defaults (1928x1208) come from comma-camera convention. The
       FrogPilot World Model may want a different size — verify by reading
       modeld's calibration check on first run, then adjust --width/--height.
    2. We do not produce a `liveCalibration` message. modeld waits for one
       before activating. On PC, calibrationd should still run from manager;
       if not, we may need to publish a synthetic liveCalibration here too.
    3. transform is identity (no rotation). For dashcam pointing forward
       through windshield this is usually correct.
    4. Frame timestamps are synthesized from frame_id × (1/fps). Real camerad
       uses sensor SOF/EOF; the synthesized values are monotonic but not
       physical. This is fine for offline testing; revisit if modeld
       rejects timestamps.
    5. PyAV reformat output stride may differ from width on some sizes.
       For 1928x1208 (mod 8) it should be fine — verified empirically required.
"""

import argparse
import sys
import time

import av
import numpy as np

import cereal.messaging as messaging
from msgq.visionipc import VisionIpcServer, VisionStreamType


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("video", help="Path to video file (mp4, mkv, mov, etc.)")
    p.add_argument("--width", type=int, default=1928,
                   help="Target frame width fed to modeld (default 1928)")
    p.add_argument("--height", type=int, default=1208,
                   help="Target frame height fed to modeld (default 1208)")
    p.add_argument("--fps", type=int, default=20,
                   help="Push rate to VisionIPC and cereal (default 20)")
    p.add_argument("--loop", action="store_true",
                   help="Loop video on EOF instead of exiting")
    p.add_argument("--wide", action="store_true",
                   help="Also mirror frames to wideRoadCameraState (mock dual cam)")
    return p.parse_args()


def to_nv12(av_frame, width, height):
    """Reformat a PyAV VideoFrame to NV12 at target size and return raw bytes.

    NV12 layout: Y plane (W*H bytes) followed by interleaved UV plane (W*H/2 bytes).
    Total = W * H * 3 // 2.
    """
    nv12 = av_frame.reformat(width=width, height=height, format="nv12")
    arr = nv12.to_ndarray()  # shape varies; PyAV tends to return (H*1.5, W) for nv12
    return arr.tobytes()


def main():
    args = parse_args()

    expected_size = args.width * args.height * 3 // 2

    # cereal publishers
    msg_names = ["roadCameraState"]
    if args.wide:
        msg_names.append("wideRoadCameraState")
    pm = messaging.PubMaster(msg_names)

    # VisionIPC server — name "camerad" so modeld attaches as if to real camerad
    server = VisionIpcServer("camerad")
    server.create_buffers(
        VisionStreamType.VISION_STREAM_ROAD, 20, False, args.width, args.height,
    )
    if args.wide:
        server.create_buffers(
            VisionStreamType.VISION_STREAM_WIDE_ROAD, 20, False, args.width, args.height,
        )
    server.start_listener()

    print(f"[video_to_vipc] VisionIPC 'camerad' started: "
          f"{args.width}x{args.height} NV12 @ {args.fps} Hz "
          f"(expected NV12 size = {expected_size} bytes)")
    if args.wide:
        print(f"[video_to_vipc]   + wideRoadCameraState mirror enabled")

    frame_period = 1.0 / args.fps
    frame_id = 0
    next_send = time.monotonic()

    while True:
        try:
            container = av.open(args.video)
        except av.AVError as e:
            print(f"[video_to_vipc] failed to open {args.video}: {e}", file=sys.stderr)
            sys.exit(1)

        stream = container.streams.video[0]
        print(f"[video_to_vipc] opened {args.video}: "
              f"{stream.codec_context.width}x{stream.codec_context.height} "
              f"@ {float(stream.average_rate):.2f} fps")

        for av_frame in container.decode(stream):
            yuv = to_nv12(av_frame, args.width, args.height)
            if len(yuv) != expected_size:
                # PyAV padding mismatch — log once then continue using whatever we got
                if frame_id == 0:
                    print(f"[video_to_vipc] WARN frame 0 NV12 size {len(yuv)} != expected "
                          f"{expected_size}; padding/stride likely. Trying anyway.")

            sof_ns = int(frame_id * frame_period * 1e9)
            eof_ns = sof_ns

            server.send(
                VisionStreamType.VISION_STREAM_ROAD, yuv, frame_id, sof_ns, eof_ns,
            )
            if args.wide:
                server.send(
                    VisionStreamType.VISION_STREAM_WIDE_ROAD, yuv, frame_id, sof_ns, eof_ns,
                )

            for name in msg_names:
                dat = messaging.new_message(name, valid=True)
                fd = getattr(dat, name)
                fd.frameId = frame_id
                fd.timestampSof = sof_ns
                fd.timestampEof = eof_ns
                fd.transform = [1.0, 0.0, 0.0,
                                0.0, 1.0, 0.0,
                                0.0, 0.0, 1.0]
                pm.send(name, dat)

            frame_id += 1

            # rate-limit to args.fps
            next_send += frame_period
            sleep_for = next_send - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                # falling behind; reset baseline so we don't accumulate lag
                next_send = time.monotonic()

        container.close()
        if not args.loop:
            print(f"[video_to_vipc] EOF after {frame_id} frames; exiting")
            break
        print(f"[video_to_vipc] EOF at frame {frame_id}; looping")


if __name__ == "__main__":
    main()
