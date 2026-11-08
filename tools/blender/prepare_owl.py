"""
Prepare a downloaded, rigged owl (glTF/GLB or FBX) for Arma 3.

Run headless (values shown are the ones for the BarnOwl source model):
    blender --background --factory-startup --python tools/blender/prepare_owl.py -- \
        --input source/owl/owl.glb --output source/owl/owl_prepared.blend \
        --map @tools/blender/owl_barn.map --src-up +y --src-forward +z \
        --scale-to 0.35 --tris 3000

What it does:
  1. Imports the model and bakes every skinned mesh into world space, using the
     same space as the armature's rest-pose joints.
  2. Rotates it to Arma's convention: forward +Y, up +Z, right +X. Blender +Y
     becomes Arma +Z when A3OB exports. --src-up and --src-forward describe the
     imported model; check them in the Blender viewport if unsure.
  3. Scales it so its nose-to-tail length is --scale-to metres. A barn owl is
     about 0.35 m long with a 0.9 m wingspan.
  4. Converts smooth skinning into rigid selections. Arma model.cfg animations
     move whole selections, so each vertex goes to its highest-weight bone, and
     that bone maps onto body / head / wing_l / wingtip_l / wing_r / wingtip_r.
  5. Decimates to --tris triangles if the model is larger.
  6. Builds a Memory object with axis_* point pairs and a box Geometry object.

Export to P3D afterwards with tools/blender/export_p3d.py, which needs the
Arma 3 Object Builder add-on.

Bone mapping: --map "Bone=target,..." (or @file, one per line, '#' comments)
assigns that bone AND all its descendants; a deeper entry wins. The FIRST
entry listed for each target is that part's pivot joint. Unmapped bones fall
back to name heuristics (BONE_RULES), then to "body".
"""

import argparse
import math
import re
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

TARGET_BONES = ("body", "head", "wing_l", "wingtip_l", "wing_r", "wingtip_r")

# (regex on lower-cased bone name, target). First match wins. "{side}" is
# replaced by l/r using the bone's position.
BONE_RULES = [
    (r"head|neck|skull|beak|eye", "head"),
    (r"hand|wrist|finger|tip|primary", "wingtip_{side}"),
    (r"wing|arm|shoulder|clavicle|forearm|feather", "wing_{side}"),
]

AXES = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--tris", type=int, default=4000)
    p.add_argument("--scale-to", type=float, default=0.35, help="Nose-to-tail length in metres")
    p.add_argument("--map", default="", help="Bone=target pairs (comma separated) or @file")
    p.add_argument("--src-up", default="+z", help="Imported model's up axis, e.g. +z or +y")
    p.add_argument("--src-forward", default="-y", help="Imported model's facing axis, e.g. -y or +z")
    p.add_argument("--single-sided", action="store_true", help="Don't add back faces for double-sided materials")
    return p.parse_args(argv)


def axis(spec):
    m = re.fullmatch(r"([+-]?)([xyz])", spec.strip().lower())
    if not m:
        raise SystemExit(f"Bad axis {spec!r}; use e.g. +y or -z")
    return AXES[m.group(2)] * (-1 if m.group(1) == "-" else 1)


def load_map(spec):
    if spec.startswith("@"):
        pairs = [line.split("#")[0].strip() for line in open(spec[1:])]
    else:
        pairs = [x.strip() for x in spec.split(",")]
    entries = [tuple(t.strip() for t in x.split("=", 1)) for x in pairs if "=" in x]
    bad = [t for _, t in entries if t not in TARGET_BONES]
    if bad:
        raise SystemExit(f"--map targets must be one of {TARGET_BONES}, got {bad}")
    return entries


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
    entries = load_map(args.map) if args.map else []
    explicit = dict(entries)
    pivot_bone = {}
    for bone, target in entries:
        pivot_bone.setdefault(target, bone)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_model(args.input)
    bpy.context.view_layer.update()

    # Only meshes skinned to an armature; the glTF importer also adds hidden
    # helper meshes (bone display shapes) that must be ignored.
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.find_armature()]
    if not meshes:
        raise SystemExit("Need a rigged model: found no mesh skinned to an armature")
    arm = meshes[0].find_armature()
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()

    # Source space -> Arma space (forward +Y, up +Z, right +X).
    up, fwd = axis(args.src_up), axis(args.src_forward)
    if abs(up.dot(fwd)) > 1e-6:
        raise SystemExit("--src-up and --src-forward must be different axes")
    right = fwd.cross(up)
    to_arma = Matrix((right, fwd, up))  # rows: new x, y, z expressed in source space

    # Bake each mesh into world space, then rotate into Arma space.
    for m in meshes:
        m.data.transform(m.matrix_world)
        m.data.transform(to_arma.to_4x4())
        m.parent = None
        m.matrix_world = Matrix.Identity(4)
    joints = {b.name: to_arma @ (arm.matrix_world @ b.head_local) for b in arm.data.bones}

    # Join into one mesh.
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    mesh.name = "LOD_1"
    for mod in list(mesh.modifiers):
        mesh.modifiers.remove(mod)

    # Scale so nose-to-tail (Y) length is --scale-to, origin at the bounding-box centre.
    lo, hi = bounds([v.co for v in mesh.data.vertices])
    factor = args.scale_to / max(hi.y - lo.y, 1e-6)
    centre = (lo + hi) / 2
    xform = Matrix.Scale(factor, 4) @ Matrix.Translation(-centre)
    mesh.data.transform(xform)
    joints = {n: xform @ p for n, p in joints.items()}

    # Rigid selections from skin weights.
    def map_bone(bone):
        b = bone
        while b is not None:
            if b.name in explicit:
                return explicit[b.name]
            b = b.parent
        n = bone.name.lower()
        for pattern, target in BONE_RULES:
            if re.search(pattern, n):
                return target.format(side="r" if joints[bone.name].x > 0 else "l")
        return "body"

    bone_target = {b.name: map_bone(b) for b in arm.data.bones}
    groups = {g.index: g.name for g in mesh.vertex_groups}
    assignment = {t: [] for t in TARGET_BONES}
    for v in mesh.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        target = bone_target.get(groups.get(best.group), "body") if best else "body"
        assignment[target].append(v.index)

    mesh.vertex_groups.clear()
    for target, idx in assignment.items():
        vg = mesh.vertex_groups.new(name=target)
        if idx:
            vg.add(idx, 1.0, "REPLACE")
    print("Selection sizes:", {t: len(i) for t, i in assignment.items()})
    empty = [t for t, i in assignment.items() if not i and t != "body"]
    if empty:
        print(f"WARNING: no vertices for {empty}. Check --map.")

    # In Arma space the left wing must be on -X.
    for side, sign in (("l", -1), ("r", 1)):
        idx = assignment[f"wing_{side}"]
        if idx:
            mean_x = sum(mesh.data.vertices[i].co.x for i in idx) / len(idx)
            if mean_x * sign < 0:
                print(f"WARNING: wing_{side} is on the wrong side; check --src-up/--src-forward.")

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

    # Arma culls back faces. Thin feather/wing planes from double-sided source
    # materials need a flipped copy or they vanish when seen from the other side.
    two_sided = {i for i, m in enumerate(mesh.data.materials) if m and not m.use_backface_culling}
    if two_sided and not args.single_sided:
        bm = bmesh.new()
        bm.from_mesh(mesh.data)
        faces = [f for f in bm.faces if f.material_index in two_sided]
        dup = bmesh.ops.duplicate(bm, geom=faces)
        new_faces = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
        bmesh.ops.reverse_faces(bm, faces=new_faces)
        bm.to_mesh(mesh.data)
        bm.free()
        print(f"Added {len(new_faces)} back faces for double-sided materials")

    # Memory LOD: two points per axis.
    lo, hi = bounds([v.co for v in mesh.data.vertices])
    mid = (lo + hi) / 2
    half = (hi.y - lo.y) / 2
    along = Vector((0, 0.03, 0))   # wing axes run front to back
    vertical = Vector((0, 0, 0.05))

    def pivot(target):
        if target in pivot_bone:
            return joints[pivot_bone[target]]
        names = [n for n, t in bone_target.items() if t == target and joints[n].length > 1e-6]
        return joints[min(names, key=lambda n: abs(joints[n].x))] if names else None

    axes = {"axis_body": (Vector((0, mid.y + half, mid.z)), Vector((0, mid.y - half, mid.z)))}
    head = pivot("head")
    if head is not None:
        axes["axis_head"] = (head, head + vertical)
    for part in ("wing_l", "wingtip_l", "wing_r", "wingtip_r"):
        p = pivot(part)
        if p is not None:
            axes[f"axis_{part}"] = (p + along, p - along)

    mem_mesh = bpy.data.meshes.new("Memory")
    bm = bmesh.new()
    for a, b in axes.values():
        bm.verts.new(a)
        bm.verts.new(b)
    bm.to_mesh(mem_mesh)
    bm.free()
    mem = bpy.data.objects.new("Memory", mem_mesh)
    bpy.context.collection.objects.link(mem)
    for i, name in enumerate(axes):
        mem.vertex_groups.new(name=name).add([2 * i, 2 * i + 1], 1.0, "REPLACE")
    missing = [f"axis_{t}" for t in TARGET_BONES if t != "body" and f"axis_{t}" not in axes]
    if missing:
        print(f"WARNING: missing memory axes {missing}; place them by hand.")
    for name, (a, _) in axes.items():
        print(f"  {name}: {tuple(round(c, 3) for c in a)}")

    # Geometry LOD: a box around the body selection.
    body_gi = mesh.vertex_groups["body"].index
    body_pts = [v.co for v in mesh.data.vertices if any(g.group == body_gi for g in v.groups)]
    glo, ghi = bounds(body_pts or [v.co for v in mesh.data.vertices])
    gm = bpy.data.meshes.new("Geometry")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((glo.x + (v.co.x + 0.5) * (ghi.x - glo.x),
                       glo.y + (v.co.y + 0.5) * (ghi.y - glo.y),
                       glo.z + (v.co.z + 0.5) * (ghi.z - glo.z)))
    bm.to_mesh(gm)
    bm.free()
    geo = bpy.data.objects.new("Geometry", gm)
    bpy.context.collection.objects.link(geo)

    # Keep only the three LOD objects.
    for obj in list(bpy.data.objects):
        if obj not in (mesh, mem, geo):
            bpy.data.objects.remove(obj, do_unlink=True)

    print("Size (m): span %.3f  length %.3f  height %.3f" % tuple(hi - lo))
    bpy.ops.wm.save_as_mainfile(filepath=args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
