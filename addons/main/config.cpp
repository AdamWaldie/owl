// Zeus Owl - swaps the bird that circles a Zeus (curator) camera for an owl.
//
// How it works: the Game Master module spawns a bird that follows each curator's
// camera and stores it on the curator logic as the "bird" variable. We don't
// replace that bird's class (that would also change every ambient/respawn seagull).
// Instead every client hides that bird locally and attaches a local owl model
// to it, so the owl follows the vanilla flight path without extra network traffic.

class CfgPatches {
    class zom_main {
        name = "Zeus Owl";
        author = "AdamWaldie";
        units[] = {};
        weapons[] = {};
        requiredVersion = 2.18;
        requiredAddons[] = {"A3_Modules_F_Curator", "zom_owl"};
    };
};

class CfgFunctions {
    class zom {
        tag = "zom";
        class main {
            file = "\z\zom\addons\main\functions";
            class init { postInit = 1; };
            class attachOwl {};
            class animateOwl {};
        };
    };
};

// Tunables, read at runtime so other mods / missions can override them.
class zom_settings {
    model = "\z\zom\addons\owl\owl.p3d";
    scale = 1.0;                // owl model is real-world size (barn owl: 0.35 m long, 0.84 m span)
    flapFrequency = 2.4;        // wing beats per second while flapping
    glideChance = 0.35;         // share of time spent gliding with wings held out
    scanInterval = 2;           // seconds between checks for new / replaced curator birds
};
