import argparse
import xml.etree.ElementTree as ET

import numpy as np
import rerun as rr
from pathlib import Path
from scipy.spatial.transform import Rotation

from geort import load_model, get_config
from geort.env.hand import HandKinematicModel
from geort.utils.path import get_package_root

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
    rr.set_time("frame", sequence=frame_idx)

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
    rr.set_time("frame", sequence=0)
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


def parse_urdf_visuals(urdf_path):
    """Parse URDF and return dict: link_name -> (mesh_filename, xyz, rpy)."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    link_visuals = {}
    for link in root.findall("link"):
        name = link.get("name")
        visual = link.find("visual")
        if visual is None:
            continue
        geom = visual.find("geometry")
        mesh_elem = geom.find("mesh") if geom is not None else None
        if mesh_elem is None:
            continue
        mesh_file = mesh_elem.get("filename")
        origin = visual.find("origin")
        if origin is not None:
            xyz = [float(v) for v in origin.get("xyz", "0 0 0").split()]
            rpy = [float(v) for v in origin.get("rpy", "0 0 0").split()]
        else:
            xyz = [0.0, 0.0, 0.0]
            rpy = [0.0, 0.0, 0.0]
        link_visuals[name] = (mesh_file, xyz, rpy)
    return link_visuals


def log_robot_meshes_static(hand_model, urdf_path, entity_prefix):
    """Log static STL meshes for each robot link under entity_prefix/{link_name}/visual/mesh."""
    urdf_dir = Path(urdf_path).parent
    link_visuals = parse_urdf_visuals(urdf_path)

    for link in hand_model.hand.get_links():
        name = link.name
        if name not in link_visuals:
            continue
        mesh_file, vis_xyz, vis_rpy = link_visuals[name]
        mesh_path = urdf_dir / mesh_file
        if not mesh_path.exists():
            print(f"  [warn] mesh not found: {mesh_path}")
            continue
        # Visual origin as a static child transform
        vis_mat = Rotation.from_euler("xyz", vis_rpy).as_matrix()
        rr.log(
            f"{entity_prefix}/{name}/visual",
            rr.Transform3D(
                translation=vis_xyz,
                mat3x3=vis_mat,
            ),
            static=True,
        )
        rr.log(
            f"{entity_prefix}/{name}/visual/mesh",
            rr.Asset3D(path=str(mesh_path)),
            static=True,
        )


def log_robot_frame(hand_model, qpos, frame_idx, entity_prefix, y_offset=0.0, z_offset=0.0):
    """Run FK on qpos and log each link's transform relative to base_link."""
    qpos_clipped = np.clip(
        qpos,
        hand_model.joint_lower_limit + 1e-3,
        hand_model.joint_upper_limit - 1e-3,
    )
    qpos_sim = hand_model.convert_user_order_to_sim_order(qpos_clipped)
    hand_model.pmodel.compute_forward_kinematics(qpos_sim)

    rr.set_time("frame", sequence=frame_idx)

    base_pose = hand_model.pmodel.get_link_pose(hand_model.base_link_idx)
    for i, link in enumerate(hand_model.hand.get_links()):
        abs_pose = hand_model.pmodel.get_link_pose(i)
        rel_pose = base_pose.inv() * abs_pose
        # sapien q = [w, x, y, z]; convert to rotation matrix via scipy (xyzw order)
        rot_mat = Rotation.from_quat(
            [rel_pose.q[1], rel_pose.q[2], rel_pose.q[3], rel_pose.q[0]]
        ).as_matrix()
        rr.log(
            f"{entity_prefix}/{link.name}",
            rr.Transform3D(
                translation=rel_pose.p + np.array([0.0, y_offset, z_offset]),
                mat3x3=rot_mat,
            ),
        )


def main():
    parser = argparse.ArgumentParser(description="Visualize mocap datasets + robot retargeting in Rerun.")
    parser.add_argument("--step", type=int, default=1, help="Frame step size (default: 1)")
    parser.add_argument("-hand", type=str, default="leap_right", help="Hand config name")
    parser.add_argument("-ckpt_tag", type=str, default="sriram", help="Checkpoint tag for GeoRT model")
    parser.add_argument("-data", type=str, default="sriram", help="Dataset name to retarget to robot")
    args = parser.parse_args()

    rr.init("visualize_mocap", spawn=True)
    log_axes()

    # Load human datasets
    datasets = []
    for path, name, color in DATASETS:
        data = np.load(path, allow_pickle=True)
        print(f"Loaded {path}: shape={data.shape}")
        datasets.append((name, data, color))

    # Load GeoRT retargeting model
    print(f"Loading GeoRT model (tag={args.ckpt_tag})...")
    model = load_model(args.ckpt_tag)

    # Build hand kinematic model (no renderer — FK only)
    print(f"Building hand kinematic model ({args.hand})...")
    config = get_config(args.hand)
    hand = HandKinematicModel.build_from_config(config, render=False)

    # Resolve URDF path and log static link meshes
    package_root = get_package_root()
    urdf_path = Path(package_root) / config["urdf_path"]
    print(f"Logging robot meshes from {urdf_path}...")
    log_robot_meshes_static(hand, urdf_path, entity_prefix="robot")

    # Pick the dataset to retarget
    retarget_data = next(
        (data for name, data, _ in datasets if args.data in name),
        datasets[0][1],
    )
    retarget_stepped = retarget_data[:: args.step]

    max_frames = max(len(d[:: args.step]) for _, d, _ in datasets)

    for frame_idx in range(max_frames):
        # Log human hand point clouds
        for ds_idx, (name, data, color) in enumerate(datasets):
            stepped = data[:: args.step]
            actual_idx = min(frame_idx, len(stepped) - 1)
            log_hand(name, stepped[actual_idx], frame_idx, x_offset=ds_idx * X_OFFSET, base_color=color)

        # Robot retargeting: GeoRT forward pass → FK → rerun
        actual_idx = min(frame_idx, len(retarget_stepped) - 1)
        qpos = model.forward(retarget_stepped[actual_idx])
        log_robot_frame(hand, qpos, frame_idx, entity_prefix="robot", y_offset=0.3, z_offset=0.1)

    print("Done.")


if __name__ == "__main__":
    main()
