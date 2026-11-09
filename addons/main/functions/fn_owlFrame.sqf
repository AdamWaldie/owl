/*
    zom_fnc_owlFrame
    EachFrame, machines with a player. Keeps one local owl per active curator:
    spawns it when the curator opens Zeus, removes it when they close Zeus or
    leave, and calls zom_fnc_flyOwl to move and animate it.

    A curator counts as active while its "zom_camPos" (shared by
    zom_fnc_shareCamera) is not empty. For this player's own curator, the live
    camera is used directly, so their owl moves without network delay.
*/
if (isNil "zom_cfg") then {
    private _cfg = configFile >> "zom_settings";
    zom_cfg = createHashMapFromArray [
        ["model",     getText   (_cfg >> "model")],
        ["scale",     getNumber (_cfg >> "scale") max 0.1],
        ["rMin",      getNumber (_cfg >> "orbitRadiusMin") max 1],
        ["rMax",      getNumber (_cfg >> "orbitRadiusMax") max 1],
        ["height",    getNumber (_cfg >> "orbitHeight")],
        ["speed",     getNumber (_cfg >> "orbitSpeed") max 1],
        ["maxSpeed",  getNumber (_cfg >> "maxSpeed") max 1],
        ["teleport",  getNumber (_cfg >> "teleportDistance") max 10],
        ["clearance", getNumber (_cfg >> "minClearance") max 0],
        ["flapFreq",  getNumber (_cfg >> "flapFrequency") max 0.5],
        ["glide",     getNumber (_cfg >> "glideChance") min 0.9 max 0]
    ];
};
if (missionNamespace getVariable ["zom_modelMissing", false]) exitWith {};

private _dt = (diag_deltaTime min 0.1) max 0;
if (_dt == 0) exitWith {};

// Active curators and the point each owl should circle.
private _myCurator = getAssignedCuratorLogic player;
private _active = [];
{
    private _target = _x getVariable ["zom_camPos", []];
    if (_x isEqualTo _myCurator && {!isNull curatorCamera}) then { _target = getPosASL curatorCamera; };
    if (_target isNotEqualTo []) then { _active pushBack [_x, _target]; };
} forEach allCurators;

// Drop owls whose curator closed Zeus or left.
zom_owls = zom_owls select {
    _x params ["_curator", "_owl"];
    private _keep = !isNull _curator && {(_active findIf {(_x select 0) isEqualTo _curator}) >= 0};
    if (!_keep) then { deleteVehicle _owl; };
    _keep
};

{
    _x params ["_curator", "_target"];
    private _idx = zom_owls findIf {(_x select 0) isEqualTo _curator};
    private _owl = objNull;
    if (_idx >= 0) then {
        _owl = (zom_owls select _idx) select 1;
    } else {
        // Spawn on its orbit so it doesn't fly in from the map origin.
        private _ang = random 360;
        private _r = (zom_cfg get "rMin") + random (((zom_cfg get "rMax") - (zom_cfg get "rMin")) max 0);
        private _start = _target vectorAdd [_r * sin _ang, _r * cos _ang, zom_cfg get "height"];
        _owl = createSimpleObject [zom_cfg get "model", _start, true];
        if (isNull _owl) then {
            zom_modelMissing = true;
            diag_log format ["[ZOM] Could not create the owl from %1 - is owl.p3d built? Owls disabled.", zom_cfg get "model"];
        } else {
            if ((zom_cfg get "scale") != 1) then { _owl setObjectScale (zom_cfg get "scale"); };
            // [orbit angle, radius, velocity, mode, mode until, seed, bank, wing phase, tip phase]
            _owl setVariable ["zom_state", [_ang, _r, [0, 0, 0], "flap", time + 1, random 100, 0, 0.5, 0.5]];
            zom_owls pushBack [_curator, _owl];
        };
    };
    if (!isNull _owl) then { [_owl, _target, _dt] call zom_fnc_flyOwl; };
} forEach _active;
