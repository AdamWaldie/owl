"""
Export the prepared owl to an Arma 3 MLOD P3D.

Needs the Arma 3 Object Builder (A3OB) Blender extension, v2.5+, installed and
enabled: Blender > Edit > Preferences > Get Extensions > "Arma 3 Object Builder".

Run headless:
    blender --background source/owl/owl_prepared.blend --python tools/blender/export_p3d.py -- \
        --output addons/owl/owl.p3d

Input: the .blend written by prepare_owl.py (objects LOD_1, Memory, Geometry).
Output: owl.p3d with
  - Resolution 1 (LOD_1) and Resolution 2 (a reduced copy, --lod2-tris)
  - Memory LOD with the axis_* points model.cfg uses
  - Geometry LOD (box, --mass kg, one component)
Texture paths are written as Arma paths (TEXTURES below); convert the source
PNGs to those .paa files separately (docs/BUILDING.md).
"""

import argparse
import sys

import bpy
import bmesh

# Source material name -> (texture, rvmat) Arma paths.
TEXTURES = {
    "FeatherAndFur": (r"z\zom\addons\owl\data\owl_feathers_co.paa", r"z\zom\addons\owl\data\owl.rvmat"),
    "BakedBarnOwl": (r"z\zom\addons\owl\data\owl_body_co.paa", r"z\zom\addons\owl\data\owl.rvmat"),
}

# A3OB LOD type ids (Arma3ObjectBuilder/io/data_p3d.py: P3D_LOD_Resolution).
LOD_VISUAL, LOD_GEOMETRY, LOD_MEMORY = "0", "6", "9"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--lod2-tris", type=int, default=1200)
    p.add_argument("--mass", type=float, default=0.5, help="Total mass in kg (a barn owl is ~0.5 kg)")
    return p.parse_args(argv)


def set_lod(obj, lod, resolution=1):
    props = obj.a3ob_properties_object
    props.is_a3_lod = True
    props.lod = lod
    props.resolution = resolution


def main():
    args = parse_args()
    if not hasattr(bpy.types.Object, "a3ob_properties_object"):
        raise SystemExit("Arma 3 Object Builder add-on is not enabled in this Blender.")
    if not hasattr(bpy.ops.a3ob, "export_p3d"):
        raise SystemExit("A3OB export operator not found; update the add-on.")

    lod1 = bpy.data.objects["LOD_1"]
    mem = bpy.data.objects["Memory"]
    geo = bpy.data.objects["Geometry"]

    # Materials -> Arma texture/rvmat paths.
    for mat in lod1.data.materials:
        if mat is None:
            continue
        tex, rvmat = TEXTURES.get(mat.name, (None, None))
        if tex is None:
            print(f"WARNING: no texture mapping for material {mat.name}")
            continue
        mp = mat.a3ob_properties_material
        mp.texture_type = "TEX"
        mp.texture_path = tex
        mp.material_path = rvmat

    # Resolution 2: reduced copy for distance.
    lod2 = lod1.copy()
    lod2.data = lod1.data.copy()
    lod2.name = "LOD_2"
    bpy.context.collection.objects.link(lod2)
    tris = len(lod2.data.polygons)
    if tris > args.lod2_tris:
        dec = lod2.modifiers.new("decimate", "DECIMATE")
        dec.ratio = args.lod2_tris / tris
        dec.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = lod2
        bpy.ops.object.modifier_apply(modifier=dec.name)

    set_lod(lod1, LOD_VISUAL, 1)
    set_lod(lod2, LOD_VISUAL, 2)
    set_lod(mem, LOD_MEMORY)
    set_lod(geo, LOD_GEOMETRY)

    # Geometry: one convex component and per-vertex mass (A3OB reads "a3ob_mass").
    if "Component01" not in geo.vertex_groups:
        geo.vertex_groups.new(name="Component01").add([v.index for v in geo.data.vertices], 1.0, "REPLACE")
    bm = bmesh.new()
    bm.from_mesh(geo.data)
    layer = bm.verts.layers.float.get("a3ob_mass") or bm.verts.layers.float.new("a3ob_mass")
    for v in bm.verts:
        v[layer] = args.mass / len(bm.verts)
    bm.to_mesh(geo.data)
    bm.free()

    result = bpy.ops.a3ob.export_p3d(
        filepath=bpy.path.abspath(args.output),
        use_selection=False,
        visible_only=False,
        apply_transforms=True,
        apply_modifiers=True,
        validate_meshes=True,
    )
    print("Export result:", result)
    if "FINISHED" not in result:
        raise SystemExit("P3D export failed; see the A3OB log above.")


if __name__ == "__main__":
    main()
