# ManusZMQ

ZMQ publisher for Manus glove raw skeleton data, built on top of the Manus SDK v3.1.1 minimal client.

## Setup

1. Download `ManusSDK_v3.1.1` from Manus and place this folder inside `SDKMinimalClient_Linux/`:
   ```
   SDKMinimalClient_Linux/
     ManusSDK/          ← from Manus
     ClientPlatformSpecific.cpp  ← from Manus
     ClientPlatformSpecific.hpp  ← from Manus
     ClientLogging.hpp           ← from Manus
     ManusZMQ/          ← this repo
   ```

2. Install dependencies:
   ```
   sudo apt install libzmq3-dev libcppzmq-dev
   ```

3. Build:
   ```
   cd ManusZMQ
   make
   ```

4. Run:
   ```
   sudo ./ManusZMQ.out
   ```

## Message format

One ZMQ PUSH message per glove per frame on port **8000**:

```
<gloveId_hex>,<x>,<y>,<z>,<rx>,<ry>,<rz>,<rw>,...
```

One `x,y,z,rx,ry,rz,rw` group per skeleton node (all nodes), positions in meters.
