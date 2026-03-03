# LEAP Hand Setup Notes for GeoRT

Original URDF sourced from: https://github.com/leap-hand/LEAP_Hand_Sim/tree/master/assets

## URDF Modifications (`robot.urdf`)

### 1. Numeric Precision Fix
The original URDF had numbers with excessive precision (22+ significant digits) and near-zero values that underflow float range (e.g. `1.6e-46`). These caused SAPIEN's URDF parser to fail with `stof` (string-to-float) errors.
- Truncated all floats to 10 significant digits
- Replaced values with magnitude < 1e-10 with `0`

### 2. Collision Meshes Removed
All `<collision>` elements were removed. SAPIEN physics simulation was unstable with the complex `.stl` collision meshes, causing jittering during replay evaluation. Per the GeoRT README, collision meshes should be simple convex shapes or removed entirely.

### 3. Virtual Base Link Added
The LEAP hand's native frame (`palm_lower`) has:
- +Y: palm center to thumb
- +Z: palm center to middle fingertip
- +X: palm surface normal

GeoRT's actual working convention (matching Allegro) is:
- +Y: palm center to thumb
- -X: palm center to middle fingertip
- +Z: palm surface normal

A virtual `base_link` was added with a fixed joint rotating -90 degrees around Y to align the LEAP frame to GeoRT's convention:
```xml
<link name="base_link">...</link>
<joint name="base_to_palm" type="fixed">
  <parent link="base_link"/>
  <child link="palm_lower"/>
  <origin xyz="0 0 0" rpy="0 -1.5707963268 0"/>
</joint>
```

### 4. Joint Limits Constrained
Original LEAP hand limits were too wide for natural human-like motion. GeoRT assumes robot fingertip motion range resembles human hands. Limits were tightened using Allegro as a reference:

| Joint | Function | Original | Constrained |
|-------|----------|----------|-------------|
| 0, 4, 8 | MCP abduction | [-1.05, 1.05] | [-0.2, 0.2] |
| 1, 5, 9 | MCP flexion | [-0.31, 2.23] | [-0.2, 1.61] |
| 2, 6, 10 | PIP flexion | [-0.51, 1.89] | [-0.2, 1.71] |
| 3, 7, 11 | DIP flexion | [-0.37, 2.04] | [-0.2, 1.62] |
| 12 | Thumb base rotation | [-0.35, 2.09] | [0.0, 1.6] |
| 13 | Thumb MCP | [-0.47, 2.44] | [-0.1, 1.2] |
| 14 | Thumb PIP | [-1.20, 1.90] | [-0.2, 1.65] |
| 15 | Thumb DIP | [-1.34, 1.88] | [-0.2, 1.72] |

## Config (`geort/config/leap_hand.json`)

### Kinematic Chains
Joint chains per finger follow the URDF parent-child tree (base to tip):
- Index: `1 -> 0 -> 2 -> 3` (palm_lower -> mcp_joint -> pip -> dip -> fingertip)
- Middle: `5 -> 4 -> 6 -> 7` (palm_lower -> mcp_joint_2 -> pip_2 -> dip_2 -> fingertip_2)
- Ring: `9 -> 8 -> 10 -> 11` (palm_lower -> mcp_joint_3 -> pip_3 -> dip_3 -> fingertip_3)
- Thumb: `12 -> 13 -> 14 -> 15` (palm_lower -> pip_4 -> thumb_pip -> thumb_dip -> thumb_fingertip)

### Center Offsets
Set to `[0.0, -0.005, 0.0]` for all fingertips (offset along -Y in the fingertip link frame).

### Human Hand IDs
MediaPipe convention: index=8, middle=12, ring=16, thumb=4.
