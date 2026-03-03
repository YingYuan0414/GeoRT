# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import zmq
import numpy as np
import threading 

left_glove_sn = "6fb94ce0"
right_glove_sn = "cd9db816"


def parse_full_skeleton(data):
    if data[0] == left_glove_sn:
        print("Left glove data found. Right glove data expected.")
    elif data[0] == right_glove_sn:
        data = np.array(list(map(float, data[1:]))).reshape(-1, 7)
        T = np.array([
            [0,  -1, 0],
            [-1, 0, 0],
            [0,  0, 1]
        ])
        points_transformed = data[:, :3] @ T.T
        return points_transformed
    else:
        print("Serial Number not found: " + str(data[0]))


class ManusMocap:
    '''
    Applies to any ZMQ-broadcasted mocap data with fixed shape (21,3) and dtype float32.
    Runs a background thread to continuously receive and update latest data.
    '''
    def __init__(self, port=8000):
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        socket.setsockopt(zmq.CONFLATE, True)     
        socket.connect(f"tcp://localhost:8000")
        self.socket = socket

        self._latest_data = None
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _recv_loop(self):
        while self._running:
            try:
                msg = self.socket.recv(flags=zmq.NOBLOCK)
                msg = msg.decode('utf-8')
                data = msg.split(",")
                if len(data) == 176:
                    arr = parse_full_skeleton(data)
                    assert arr.shape == (25, 3)
                    # arr = np.frombuffer(msg, dtype=np.float32).reshape(21, 3)
                    with self._lock:
                        self._latest_data = arr
            except zmq.Again:
                import time
                time.sleep(0.001)

    def get(self):
        with self._lock:
            if self._latest_data is not None:
                return {"result": self._latest_data.copy(), "status": "recording"}
            else:
                return {"result": None, "status": "no data"}

    def close(self):
        self._running = False
        self._thread.join()
        self.socket.close()