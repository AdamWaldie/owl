/*
    zom_fnc_init (postInit)
    Starts the three parts of the seagull replacement:
      - zom_fnc_removeBirds  every machine: deletes (or, if the server lacks the mod, hides) vanilla curator birds
      - zom_fnc_shareCamera  machines with a player: shares this player's Zeus camera position
      - zom_fnc_owlFrame     machines with a player: flies and animates the local owls each frame
*/
if (isServer) then {
    // Tells clients the server runs the mod, so deleting the vanilla bird is safe:
    // everyone who still sees a bird then also has the owl.
    missionNamespace setVariable ["zom_serverActive", true, true];
};

[] spawn zom_fnc_removeBirds;

if (hasInterface) then {
    zom_owls = [];   // [[curatorLogic, owl], ...] - local owls this client renders
    [] spawn zom_fnc_shareCamera;
    addMissionEventHandler ["EachFrame", { call zom_fnc_owlFrame }];
};
