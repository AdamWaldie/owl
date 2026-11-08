# Building

## Tools

- [HEMTT](https://github.com/BrettMayson/HEMTT) to pack and sign the PBOs (Windows/Linux)
- [Blender](https://www.blender.org/) 4.x with the [Arma 3 Object Builder add-on](https://github.com/MrClock8163/Arma3ObjectBuilder) (A3OB) for P3D export
- Arma 3 Tools (Steam) for **ImageToPAA**/TexView2 to convert textures to `.paa` (Windows), and optionally to binarize the P3D

## 1. Owl source

"BarnOwl" by BloodTigerWolfSketchF (Sketchfab Free Standard, see `CREDITS.md`). Download
the glTF from Sketchfab and put `owl.glb` in `source/owl/`, with the textures in
`source/owl/textures/`. These files are git-ignored.

## 2. Prepare in Blender

```bash
blender --background --factory-startup --python tools/blender/prepare_owl.py -- --input source/owl/owl.glb --output source/owl/owl_prepared.blend --map @tools/blender/owl_barn.map --src-up +y --src-forward +z --scale-to 0.35 --tris 3000
```

Expected output, checked with Blender 4.4.3:

```
Selection sizes: {'body': 948, 'head': 537, 'wing_l': 301, 'wingtip_l': 244, 'wing_r': 301, 'wingtip_r': 245}
Added 2840 back faces for double-sided materials
Size (m): span 0.841  length 0.350  height 0.174
```

The result faces Arma forward (+Y in Blender) with the left wing on -X. The selections
split at the shoulder and wrist joints, and the memory axes sit on those joints.
The back faces matter because Arma culls back faces, so without them the thin feather
planes would vanish when seen from the other side.

## 3. Export P3D with A3OB

Install the **Arma 3 Object Builder** extension in Blender 4.2 or later
(Edit > Preferences > Get Extensions). Then:

```bash
blender --background source/owl/owl_prepared.blend --python tools/blender/export_p3d.py -- --output addons/owl/owl.p3d
```

The export script sets the LOD types (Resolution 1 and 2, Memory, and Geometry with 0.5 kg
mass), points the materials at the paths below and exports the P3D.

Convert the textures with **ImageToPAA** (Arma 3 Tools):

| Source | Output |
|---|---|
| `source/owl/textures/gltf_embedded_0.png` (FeatherAndFur) | `addons/owl/data/owl_feathers_co.paa` |
| `source/owl/textures/gltf_embedded_1.png` (BakedBarnOwl) | `addons/owl/data/owl_body_co.paa` |

`addons/owl/data/owl.rvmat` is a matte, non-shiny feather material.

## 4. Build and test

```bash
hemtt dev
```

Launch Arma 3 with `@zom` from `.hemttout/dev`, open the editor, place a player, a **Game Master** module and the owner set to the player, then preview and press `Y`. Have a second client (or `switchCamera` from a debug console) look at the camera position to see the owl.

Tunables live in `class zom_settings` in `addons/main/config.cpp`: model path, scale, wingbeat frequency, glide share and scan interval.

## Known unknowns

These are untested assumptions, so check them first in game:
- The curator bird is read from `curatorLogic getVariable "bird"`, as the Game Master module documents. If a game update changes this, `fn_init.sqf` is the only file to change.
- `animate [..., true]` on a local simple object updates every frame. If it doesn't, switch `createSimpleObject` to `createVehicleLocal` with a small `thingX` class.
