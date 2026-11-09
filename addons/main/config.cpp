// Zeus Owl - replaces the seagull that circles a Zeus (curator) camera with an owl.
//
// How it works:
//  - The Game Master module keeps a bird near each curator camera, stored on the
//    curator logic as "bird". The server (or the machine that owns the bird)
//    deletes it. Clients without the server running the mod only hide it locally,
//    so the mod never deletes the seagull for players who don't have it.
//  - The curator's machine shares its camera position (a few times a second).
//  - Every client flies its own local owl around that position, with owl-like
//    flight (circling, catching up, banking, flapping and gliding) and animates it.
//    Only the camera position crosses the network.

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
            class removeBirds {};
            class shareCamera {};
            class owlFrame {};
            class flyOwl {};
        };
    };
};

// Tunables, read at runtime so other mods / missions can override them.
class zom_settings {
    model = "\z\zom\addons\owl\owl.p3d";
    scale = 1.0;                // owl model is real-world size (barn owl: 0.35 m long, 0.84 m span)

    // Flight
    orbitRadiusMin = 6;         // metres from the camera the owl circles at
    orbitRadiusMax = 11;
    orbitHeight = -2.5;         // metres relative to the camera (owl flies a little below it)
    orbitSpeed = 7;             // m/s cruising speed while circling (barn owls cruise ~7 m/s)
    maxSpeed = 30;              // m/s cap while chasing a fast-moving camera
    teleportDistance = 300;     // further than this from its target the owl just reappears
    minClearance = 3;           // metres above terrain / sea

    // Animation
    flapFrequency = 2.4;        // wing beats per second while flapping
    glideChance = 0.4;          // chance to glide when cruising level

    // Networking / housekeeping
    cameraShareInterval = 0.25; // seconds between camera position updates from the curator
    birdScanInterval = 0.5;     // seconds between checks for vanilla curator birds
};
