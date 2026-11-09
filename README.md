# Zeus Owl

An Arma 3 mod that swaps the seagull circling every Zeus (curator) camera for a realistic, animated owl.

## How it works

The Game Master module keeps a seagull near each curator camera and stores it on the curator as the `bird` variable. This mod **removes that seagull and flies an owl in its place**:

1. **Remove** (`fn_removeBirds.sqf`, every machine): the server deletes the vanilla bird, and so does the machine that owns it, which covers birds that exist only on the curator's PC. Ambient and respawn seagulls are untouched.
2. **Share** (`fn_shareCamera.sqf`): while a player has Zeus open, their machine shares the camera position a few times a second, and only when it moves.
3. **Fly** (`fn_owlFrame.sqf`, `fn_flyOwl.sqf`, every player): each client flies its own local owl around that position. It circles a little below the camera, chases it when it moves, banks into turns and keeps clear of terrain. It flaps when climbing or chasing, glides in between, and turns its head toward the camera.

Only the camera position crosses the network. All flight and animation is local.

**The server must run the mod** for the seagull to be deleted. If only some clients have it, those clients hide the seagull locally and still see the owl, while everyone else keeps seeing the seagull. The mod never deletes the seagull for players who can't see the owl.

## Layout

| Path | What |
|---|---|
| `addons/main` | Scripts and the `zom_settings` tunables (`config.cpp`) |
| `addons/owl` | `owl.p3d`, textures and `model.cfg` (skeleton and animations) |
| `tools/blender/prepare_owl.py` | Turns a downloaded rigged owl into Arma-ready selections and memory points |
| `tools/blender/export_p3d.py` | Sets LODs and materials, then exports `owl.p3d` through A3OB |
| `tools/blender/owl_barn.map` | Bone-to-selection mapping for the barn owl rig |
| `source/owl` | The original downloaded model |
| `docs/BUILDING.md` | Full model pipeline and build steps |

## Status

- [x] Mod scaffold, scripts, `model.cfg`, Blender prep script
- [x] Owl model chosen: "BarnOwl" by BloodTigerWolfSketchF (Sketchfab Free Standard), see `CREDITS.md`
- [x] Owl source downloaded (kept local, git-ignored)
- [x] Blender prep pipeline run and checked (selections, pivots, scale, back faces)
- [ ] Export `owl.p3d` (needs the A3OB add-on) and convert textures to `.paa` (ImageToPAA)
- [ ] Test in game (single player and multiplayer)

## Build

```bash
hemtt build
```

For a release build, run `hemtt release` instead. See [docs/BUILDING.md](docs/BUILDING.md).
