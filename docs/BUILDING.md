# Building

## Tools

- [HEMTT](https://github.com/BrettMayson/HEMTT) to pack and sign the PBOs (Windows/Linux)
- [Blender](https://www.blender.org/) 4.x with the [Arma 3 Object Builder add-on](https://github.com/MrClock8163/Arma3ObjectBuilder) (A3OB) for P3D export
- Arma 3 Tools (Steam) for **ImageToPAA**/TexView2 to convert textures to `.paa` (Windows), and optionally to binarize the P3D

## 1. Choose the owl

Requirements:
- **Realistic** look that matches Arma 3's grounded, military-sim style. No cartoon or low-poly owls.
- Real-world size, natural plumage (barn, tawny or eagle owl), with roughly 2k textures at most.
- Licence **CC0 or CC-BY** so it can be redistributed. Fill in `CREDITS.md`.
- Rigged with separate wing bones. Baked animations aren't used, because Arma drives the wings through `model.cfg`.

Save it as `source/owl/owl.glb` (or `.fbx`).

## 2. Prepare in Blender

```bash
blender --background --python tools/blender/prepare_owl.py -- --input source/owl/owl.glb --output source/owl/owl_prepared.blend
```

Check the printed selection sizes. If a wing or the head is empty, pass explicit mappings, for example `--map "Bone.012=wing_l,Bone.020=head"`.

Open `owl_prepared.blend` and check that:
- vertex groups `body`, `head`, `wing_l`, `wingtip_l`, `wing_r`, `wingtip_r` cover the right parts,
- the `Memory` object's `axis_*` point pairs sit on the shoulder, wrist and neck joints and run front to back (or vertically for the head).

## 3. Export P3D with A3OB

In the A3OB object properties:
- `LOD_1`: **Is P3D LOD**, type *Resolution*, value 1. Add a lower LOD (for example decimated to 1000 tris, resolution 2) for distance.
- `Memory`: **Is P3D LOD**, type *Memory*.
- `Geometry`: **Is P3D LOD**, type *Geometry*, total mass about 2 kg.
- Materials: point the texture at `z\zom\addons\owl\data\owl_co.paa`, the normal map at `owl_nohq.paa`, and use `\a3\data_f\default.rvmat` or a custom feather rvmat.

**File → Export → Arma 3 model (.p3d)** to `addons/owl/owl.p3d`.

Convert the textures with ImageToPAA: `owl_co.png` becomes `addons/owl/data/owl_co.paa`, and `owl_nohq.png` becomes `addons/owl/data/owl_nohq.paa`. Keep the `_co` and `_nohq` suffixes, because Arma uses them to choose compression.

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
