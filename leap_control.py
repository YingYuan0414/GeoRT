"""
LEAP hand control scripts.

leap_control.py <mode> [args]

Modes:
  basic   -- command hand to a fixed target (open -> curl -> open)
  live    -- real-time Manus glove control via GeoRT model

Usage:
  python leap_control.py basic
  python leap_control.py live -hand leap_right_manus -ckpt_tag sriram_1
"""

import sys
import time
import argparse
import numpy as np

sys.path.insert(0, '/home/leap/Desktop/deoxys_control/deoxys/leap_control')
from main import LeapNode

from geort import load_model, get_config
from geort.mocap.manus_mocap import ManusMocap


# ── Joint layout (allegro convention: 0 = open, + = close) ────────────────────
OPEN_HAND = np.zeros(16)

CURLED = np.array([
    0.0, 0.5, 0.8, 0.5,   # index
    0.0, 0.5, 0.8, 0.5,   # middle
    0.0, 0.5, 0.8, 0.5,   # ring
    0.0, 0.5, 0.5, 0.5,   # thumb
])


def move_to(leap_hand, target, steps=50, dt=0.02):
    """Linearly interpolate from current LEAP pos to target (allegro convention)."""
    current_allegro = leap_hand.read_pos() - np.pi
    for i in range(1, steps + 1):
        alpha = i / steps
        leap_hand.set_allegro((1 - alpha) * current_allegro + alpha * target)
        time.sleep(dt)


# ── Mode: basic ────────────────────────────────────────────────────────────────

def run_basic():
    print("Connecting to LEAP hand...")
    leap_hand = LeapNode()
    print("Connected.")

    print("Moving to OPEN position...")
    move_to(leap_hand, OPEN_HAND)
    time.sleep(1.0)

    print("Moving to CURLED position...")
    move_to(leap_hand, CURLED)
    time.sleep(1.0)

    print("Returning to OPEN position...")
    move_to(leap_hand, OPEN_HAND)
    time.sleep(0.5)

    print("Done.")


# ── Mode: live ─────────────────────────────────────────────────────────────────

def run_live(hand_name, ckpt_tag):
    print(f"Loading GeoRT model (ckpt_tag={ckpt_tag})...")
    model = load_model(ckpt_tag)

    print("Connecting to LEAP hand...")
    leap_hand = LeapNode()
    print("Connected.")

    print("Connecting to Manus glove (ZMQ)...")
    mocap = ManusMocap()
    print("Connected. Waiting for glove data...")

    # Move to open before starting
    move_to(leap_hand, OPEN_HAND)

    print("Streaming. Press Ctrl+C to stop.")
    try:
        while True:
            result = mocap.get()
            if result['status'] == 'recording' and result['result'] is not None:
                qpos = model.forward(result['result'])
                leap_hand.set_allegro(qpos)
            time.sleep(0.01)  # ~100 Hz cap
    except KeyboardInterrupt:
        print("\nStopped. Moving to open position...")
        move_to(leap_hand, OPEN_HAND)
        mocap.close()
        print("Done.")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['basic', 'live'], nargs='?', default='basic')
    parser.add_argument('-hand', type=str, default='leap_right_manus')
    parser.add_argument('-ckpt_tag', type=str, default='sriram_1')
    args = parser.parse_args()

    if args.mode == 'basic':
        run_basic()
    elif args.mode == 'live':
        run_live(args.hand, args.ckpt_tag)


if __name__ == '__main__':
    main()
