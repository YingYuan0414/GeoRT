import argparse

import numpy as np
import rerun as rr

# Per-dataset hue: sriram=blue, alex=green, ying=red
DATASETS = [
    ("data/human_sriram.npy", "sriram", [0.2, 0.4, 1.0]),   # blue
    ("data/human_alex.npy",   "alex",   [0.2, 1.0, 0.4]),   # green
    ("data/human_ying.npy",   "ying",   [1.0, 0.3, 0.3]),   # red
]

# Space datasets side-by-side along X (meters)
X_OFFSET = 0.3


def make_colors(n_points, base_color):
    """Gradient from dark to bright using the base hue."""
    base = np.array(base_color)
    colors = np.outer(np.linspace(0.3, 1.0, n_points), base)
    return np.clip(colors, 0, 1)


def log_hand(entity, points, frame_idx, x_offset, base_color):
    rr.set_time_sequence("frame", frame_idx)

    offset_points = points + np.array([x_offset, 0, 0])
    colors = make_colors(len(points), base_color)

    rr.log(
        f"hands/{entity}/points",
        rr.Points3D(
            positions=offset_points,
            colors=colors,
            radii=0.005,
            labels=[str(i) for i in range(len(points))],
        ),
    )


def log_axes():
    rr.set_time_sequence("frame", 0)
    axis_length = 0.1
    origin = np.array([0.0, 0.0, 0.0])
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
    parser = argparse.ArgumentParser(description="Visualize multiple mocap datasets in Rerun.")
    parser.add_argument("--step", type=int, default=1, help="Frame step size (default: 1)")
    args = parser.parse_args()

    rr.init("visualize_mocap", spawn=True)
    log_axes()

    datasets = []
    for path, name, color in DATASETS:
        data = np.load(path, allow_pickle=True)
        print(f"Loaded {path}: shape={data.shape}")
        datasets.append((name, data, color))

    max_frames = max(len(d[:: args.step]) for _, d, _ in datasets)

    for frame_idx in range(max_frames):
        for ds_idx, (name, data, color) in enumerate(datasets):
            stepped = data[:: args.step]
            # Hold last frame when this dataset runs out
            actual_idx = min(frame_idx, len(stepped) - 1)
            log_hand(name, stepped[actual_idx], frame_idx, x_offset=ds_idx * X_OFFSET, base_color=color)

    print("Done.")


if __name__ == "__main__":
    main()
