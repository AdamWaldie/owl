"""
Prepare a downloaded, rigged owl (glTF/GLB or FBX) for Arma 3.

Run headless:
    blender --background --python tools/blender/prepare_owl.py -- \
        --input source/owl/owl.glb --output source/owl/owl_prepared.blend \
        [--tris 4000] [--scale-to 0.6]

What it does:
  1. Imports the model and joins its meshes into one.
  2. Scales it so the body length is --scale-to metres (a real owl is ~0.5-0.65 m).
  3. Converts smooth skinning into rigid bone selections. Arma model.cfg
     animations move whole selections, so each vertex goes to the single
     bone with the highest weight, then that bone is mapped onto one of
     body / head / wing_l / wingtip_l / wing_r / wingtip_r.
  4. Decimates to --tris triangles (Arma ambient objects should stay small).
  5. Builds a Memory LOD mesh with the axis_* point pairs from the rig's
     joint positions, and a simple box Geometry LOD.

Export to P3D afterwards with the Arma 3 Object Builder add-on
(see docs/BUILDING.md). This script deliberately does not touch that add-on's
properties, so it works whichever add-on version you have.

Bone-name mapping is heuristic. If your rig uses unusual names, edit BONE_RULES
or pass --map "SourceBone=wing_l,OtherBone=head".
"""

import argparse
import re
import sys

import bpy
import bmesh
from mathutils import Vector

TARGET_BONES = ("body", "head", "wing_l", "wingtip_l", "wing_r", "wingtip_r")

# (regex on lower-cased bone name, target). First match wins. Side is detected
# separately and substituted for "{side}".
BONE_RULES = [
    (r"head|neck|skull|beak|eye", "head"),
    (r"hand|wrist|finger|tip|primary", "wingtip_{side}"),
    (r"wing|arm|shoulder|clavicle|forearm|feather", "wing_{side}"),
]


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--tris", type=int, default=4000)
    p.add_argument("--scale-to", type=float, default=0.6)
    p.add_argument("--map", default="", help="Explicit SourceBone=target pairs, comma separated")
    return p.parse_args(argv)


def side_of(name, head_x):
    n = name.lower()
    if re.search(r"(^|[._\-\s])l$|(^|[._\-\s])l[._\-\s]|left", n):
        return "l"
    if re.search(r"(^|[._\-\s])r$|(^|[._\-\s])r[._\-\s]|right", n):
        return "r"
    # Fall back to position. With the glTF importer the model faces -Y,
    # so +X is the owl's left.
    return "l" if head_x > 0 else "r"


def map_bone(bone, explicit):
    if bone.name in explicit:
        return explicit[bone.name]
    n = bone.name.lower()
    for pattern, target in BONE_RULES:
        if re.search(pattern, n):
            return target.format(side=side_of(bone.name, bone.head_local.x))
    return "body"


def import_model(path):
    lower = path.lower()
    if lower.endswith((".glb", ".gltf")):
        bpy.ops.import_scene.gltf(filepath=path)
    elif lower.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise SystemExit(f"Unsupported format: {path}")


def bounds(points):
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def main():
    args = parse_args()
    explicit = dict(pair.split("=", 1) for pair in args.map.split(",") if "=" in pair)
    bad = [t for t in explicit.values() if t not in TARGET_BONES]
    if bad:
        raise SystemExit(f"--map targets must be one of {TARGET_BONES}, got {bad}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_model(args.input)

    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not armatures or not meshes:
        raise SystemExit("Need a rigged model: found no armature or no mesh")
    arm = armatures[0]

    # Rest pose so joint positions match the bind pose.
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()

    # Unparent meshes keeping their transforms, then join them.
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    mesh.name = "LOD_1"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Joint positions in world space, before anything moves.
    joints = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}

    # Scale mesh and joints so the body length (front-back, Y) is --scale-to.
    lo, hi = bounds([v.co for v in mesh.data.vertices])
    factor = args.scale_to / max(hi.y - lo.y, 1e-6)
    for v in mesh.data.vertices:
        v.co *= factor
    joints = {n: p * factor for n, p in joints.items()}

    # Rigid selections from skin weights.
    bone_target = {b.name: map_bone(b, explicit) for b in arm.data.bones}
    groups = {g.index: g.name for g in mesh.vertex_groups}
    assignment = {t: [] for t in TARGET_BONES}
    for v in mesh.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        target = bone_target.get(groups.get(best.group), "body") if best else "body"
        assignment[target].append(v.index)

    for mod in list(mesh.modifiers):
        mesh.modifiers.remove(mod)
    mesh.vertex_groups.clear()
    for target, idx in assignment.items():
        vg = mesh.vertex_groups.new(name=target)
        if idx:
            vg.add(idx, 1.0, "REPLACE")
    print("Selection sizes:", {t: len(i) for t, i in assignment.items()})
    empty = [t for t, i in assignment.items() if not i and t != "body"]
    if empty:
        print(f"WARNING: no vertices for {empty}. Check bone names or pass --map.")

    # Decimate (vertex groups survive the collapse decimator).
    tri_count = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    if tri_count > args.tris:
        dec = mesh.modifiers.new("decimate", "DECIMATE")
        dec.ratio = args.tris / tri_count
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Memory LOD: two points per axis.
    lo, hi = bounds([v.co for v in mesh.data.vertices])
    centre = (lo + hi) / 2
    half_len = (hi.y - lo.y) / 2
    fwd = Vector((0, 0.04, 0))  # wing axes run front to back

    def joint_for(target, key):
        names = [n for n, t in bone_target.items() if t == target]
        return joints[min(names, key=key)] if names else None

    axes = {"axis_body": (centre - Vector((0, half_len, 0)), centre + Vector((0, half_len, 0)))}
    neck = joint_for("head", key=lambda n: joints[n].z)            # lowest head bone = neck
    if neck is not None:
        axes["axis_head"] = (neck, neck + Vector((0, 0, 0.1)))
    for side in ("l", "r"):
        for part in ("wing", "wingtip"):
            j = joint_for(f"{part}_{side}", key=lambda n: abs(joints[n].x))  # innermost joint
            if j is not None:
                axes[f"axis_{part}_{side}"] = (j - fwd, j + fwd)

    mem_mesh = bpy.data.meshes.new("Memory")
    bm = bmesh.new()
    order = []
    for name, (a, b) in axes.items():
        bm.verts.new(a)
        bm.verts.new(b)
        order.append(name)
    bm.to_mesh(mem_mesh)
    bm.free()
    mem = bpy.data.objects.new("Memory", mem_mesh)
    bpy.context.collection.objects.link(mem)
    for i, name in enumerate(order):
        mem.vertex_groups.new(name=name).add([2 * i, 2 * i + 1], 1.0, "REPLACE")
    missing = [n for n in ("axis_head", "axis_wing_l", "axis_wing_r", "axis_wingtip_l", "axis_wingtip_r")
               if n not in axes]
    if missing:
        print(f"WARNING: missing memory axes {missing}; place them by hand.")

    # Geometry LOD: a box around the body selection.
    # Read membership from the vertex group: decimation renumbered the vertices.
    body_gi = mesh.vertex_groups["body"].index
    body_pts = [v.co for v in mesh.data.vertices if any(g.group == body_gi for g in v.groups)]
    glo, ghi = bounds(body_pts or [v.co for v in mesh.data.vertices])
    bpy.ops.mesh.primitive_cube_add(location=(glo + ghi) / 2)
    geo = bpy.context.active_object
    geo.name = "Geometry"
    geo.dimensions = ghi - glo
    bpy.ops.object.transform_apply(scale=True)

    bpy.data.objects.remove(arm, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
