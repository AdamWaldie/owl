# Zeus Owl

An Arma 3 mod that swaps the seagull circling every Zeus (curator) camera for a realistic, animated owl.

## How it works

The Game Master module spawns a bird that follows each curator camera and stores it on the curator as the `bird` variable. This mod leaves that bird and its class alone, so ambient and respawn seagulls stay unchanged. Instead each client:

1. finds every curator's bird (`addons/main/functions/fn_init.sqf`),
2. hides it locally and attaches a **local** owl simple object to it (`fn_attachOwl.sqf`), so the owl follows the vanilla flight path,
3. drives the owl's `model.cfg` animations every frame (`fn_animateOwl.sqf`): a slow, deep wingbeat with trailing wingtips, glides with the wings held level, banking into turns, and head scanning.

Nothing is synced over the network, and the mod is purely cosmetic. Players without it still see the seagull.

## Layout

| Path | What |
|---|---|
| `addons/main` | Scripts and the `zom_settings` tunables (`config.cpp`) |
| `addons/owl` | `owl.p3d`, textures and `model.cfg` (skeleton and animations) |
| `tools/blender/prepare_owl.py` | Turns a downloaded rigged owl into Arma-ready selections and memory points |
| `source/owl` | The original downloaded model |
| `docs/BUILDING.md` | Full model pipeline and build steps |

## Status

- [x] Mod scaffold, scripts, `model.cfg`, Blender prep script
- [ ] Pick the owl model (realistic, CC0/CC-BY, rigged) and credit it in `CREDITS.md`
- [ ] Run the Blender pipeline, then export `owl.p3d` and the `.paa` textures
- [ ] Test in game (single player and multiplayer)

## Build

```bash
hemtt build
```

For a release build, run `hemtt release` instead. See [docs/BUILDING.md](docs/BUILDING.md).
