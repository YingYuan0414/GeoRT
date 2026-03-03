import geort
import time
from geort.mocap.manus_mocap import ManusMocap

# Dataset Name
data_output_name = "human_ying" # TODO(): Specify a name for this (e.g. your name)

# Your data collection loop.
mocap = ManusMocap() # TODO(): your mocap system.
                           # Define a mocap.get() method.
                           # Apologies, you still have to do this...
 
data = []

for step in range(5000):       # collect 5000 data points.
    res = mocap.get() # mocap.get() return [N, 3] numpy array.
    if res['status'] == 'recording':
        hand_keypoint = res['result']
        data.append(hand_keypoint)
        print('collected step:', step, "/ 5000")
    else:
        print('no data')
    
    time.sleep(0.01)            # take a short break.

# finish data collection.
geort.save_human_data(data, data_output_name)