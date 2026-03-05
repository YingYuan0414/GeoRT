import argparse
import time

import geort
import numpy as np
import rerun as rr

from geort.mocap.manus_mocap import ManusMocap


def log_hand(points):
    indices = np.arange(len(points))
    colors = np.zeros((len(points), 3))
    colors[:, 0] = indices / (len(points) - 1)        # R
    colors[:, 2] = 1.0 - indices / (len(points) - 1)  # B

    rr.log(
        "hand/points",
        rr.Points3D(
            positions=points,
            colors=colors,
            radii=0.005,
            labels=[str(i) for i in indices],
        ),
    )

    axis_length = 0.5
    origin = np.array([0, 0, 0])
    rr.log(
        "world_axes",
        rr.LineStrips3D(
            [
                np.array([origin, origin + [axis_length, 0, 0]]),
                np.array([origin, origin + [0, axis_length, 0]]),
                np.array([origin, origin + [0, 0, axis_length]]),
            ],
            colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
        ),
    )


def main():
    parser = argparse.ArgumentParser(description="Collect Manus glove mocap data.")
    parser.add_argument("--name", default="human_ying", help="Dataset output name (default: human_ying)")
    parser.add_argument("--steps", type=int, default=5000, help="Number of steps to collect (default: 5000)")
    parser.add_argument("--host", default="localhost", help="ZMQ host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="ZMQ port (default: 8000)")
    parser.add_argument("--right-sn", default="cd9db816", help="Right glove serial number (default: cd9db816)")
    parser.add_argument("--left-sn", default="6fb94ce0", help="Left glove serial number (default: 6fb94ce0)")
    parser.add_argument("--visualize", action="store_true", help="Stream to Rerun viewer")
    args = parser.parse_args()

    if args.visualize:
        rr.init("collect_mocap", spawn=True)

    mocap = ManusMocap(
        host=args.host,
        port=args.port,
        right_glove_sn=args.right_sn,
        left_glove_sn=args.left_sn,
    )

    data = []

    for step in range(args.steps):
        res = mocap.get()
        if res["status"] == "recording":
            hand_keypoint = res["result"]
            data.append(hand_keypoint)
            print(f"collected step: {step} / {args.steps}")
            if args.visualize:
                log_hand(hand_keypoint)
        else:
            print("no data")

        time.sleep(0.01)

    geort.save_human_data(data, args.name)


if __name__ == "__main__":
    main()
