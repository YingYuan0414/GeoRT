"""
Usage:
    python geort/scripts/plot_mocap.py -data human_sriram
    python geort/scripts/plot_mocap.py -data human_sriram --ref human_alex
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from geort.utils.path import get_human_data

FINGERTIP_IDS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}

FINGER_COLORS = {
    "thumb":  "red",
    "index":  "blue",
    "middle": "green",
    "ring":   "orange",
    "pinky":  "purple",
}


def load_data(name):
    path = get_human_data(name)
    if path is None:
        raise FileNotFoundError(f"Could not find data file for '{name}' in data/")
    data = np.load(path)
    print(f"[{name}] shape={data.shape}  range=[{data.min():.4f}, {data.max():.4f}]")
    return data


def viz_fingertip_trajectories(data, label):
    ids = {k: v for k, v in FINGERTIP_IDS.items() if v < data.shape[1]}
    t = np.arange(data.shape[0])
    fig, axes = plt.subplots(len(ids), 3, figsize=(14, 3 * len(ids)), sharex=True)
    fig.suptitle(f"Fingertip XYZ Trajectories [{label}]", fontsize=13)
    for row, (fname, idx) in enumerate(ids.items()):
        pts = data[:, idx, :]
        for col, axis_name in enumerate(["X", "Y", "Z"]):
            ax = axes[row, col]
            ax.plot(t, pts[:, col], color=FINGER_COLORS[fname], linewidth=0.8)
            ax.set_ylabel(f"{fname} {axis_name}")
            ax.grid(True, alpha=0.3)
        axes[row, 0].set_title(f"{fname} (idx {idx})", loc='left')
    for col in range(3):
        axes[-1, col].set_xlabel("Frame")
    plt.tight_layout()
    plt.show()


def viz_comparison_scatter(data_a, name_a, data_b, name_b):
    ids = {k: v for k, v in FINGERTIP_IDS.items()
           if v < data_a.shape[1] and v < data_b.shape[1]}
    fig, axes = plt.subplots(len(ids), 3, figsize=(12, 3 * len(ids)))
    fig.suptitle(f"Fingertip Workspace: {name_a} (blue) vs {name_b} (orange)", fontsize=12)
    plane_pairs = [("Y", "Z", 1, 2), ("X", "Z", 0, 2), ("X", "Y", 0, 1)]
    for row, (fname, idx) in enumerate(ids.items()):
        pts_a = data_a[:, idx, :]
        pts_b = data_b[:, idx, :]
        for col, (xn, yn, xi, yi) in enumerate(plane_pairs):
            ax = axes[row, col]
            ax.scatter(pts_a[:, xi], pts_a[:, yi], s=1, alpha=0.2, color='steelblue', label=name_a)
            ax.scatter(pts_b[:, xi], pts_b[:, yi], s=1, alpha=0.2, color='darkorange', label=name_b)
            ax.set_xlabel(xn); ax.set_ylabel(yn)
            ax.set_title(f"{fname}: {xn}-{yn}", fontsize=9)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
        axes[row, 0].legend(markerscale=5, fontsize=7)
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-data', type=str, required=True)
    parser.add_argument('--ref', type=str, default=None)
    args = parser.parse_args()

    data = load_data(args.data)
    viz_fingertip_trajectories(data, args.data)

    if args.ref:
        ref = load_data(args.ref)
        viz_comparison_scatter(data, args.data, ref, args.ref)


if __name__ == '__main__':
    main()
