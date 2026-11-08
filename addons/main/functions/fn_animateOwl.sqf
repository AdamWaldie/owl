/*
    zom_fnc_animateOwl
    Drives the owl's model.cfg animations locally: alternates between flapping
    and gliding, banks into turns, and turns the head slightly. Animation names
    match addons/owl/model.cfg.

    Params:
        0: OBJECT - owl (local simple object)
        1: OBJECT - curator bird it is attached to
*/
params ["_owl", "_bird"];

private _cfg = configFile >> "zom_settings";
_owl setVariable ["zom_freq", getNumber (_cfg >> "flapFrequency") max 0.5];
_owl setVariable ["zom_glideChance", getNumber (_cfg >> "glideChance") min 0.9 max 0];
_owl setVariable ["zom_bird", _bird];
_owl setVariable ["zom_mode", "flap"];
_owl setVariable ["zom_modeUntil", time + 2];
_owl setVariable ["zom_lastDir", getDir _bird];

private _id = addMissionEventHandler ["EachFrame", {
    _thisArgs params ["_owl"];
    if (isNull _owl) exitWith { removeMissionEventHandler ["EachFrame", _thisEventHandler]; };

    // Skip the work when the owl is too far away to see properly.
    if ((positionCameraToWorld [0,0,0]) distance _owl > 600) exitWith {};

    private _bird = _owl getVariable "zom_bird";
    private _t = time;

    // Switch between flapping and gliding every few seconds.
    if (_t > (_owl getVariable "zom_modeUntil")) then {
        private _glide = random 1 < (_owl getVariable "zom_glideChance");
        _owl setVariable ["zom_mode", ["flap", "glide"] select _glide];
        _owl setVariable ["zom_modeUntil", _t + ([2 + random 3, 1.5 + random 2.5] select _glide)];
    };

    private _flapPhase = if ((_owl getVariable "zom_mode") == "flap") then {
        // 0 = wings up, 1 = wings down. Owls have a slow, deep, quiet stroke.
        0.5 + 0.5 * sin (_t * 360 * (_owl getVariable "zom_freq"))
    } else {
        0.45                                // wings held level for the glide
    };
    // Tips trail the main wing slightly for a less mechanical stroke.
    private _tipPhase = if ((_owl getVariable "zom_mode") == "flap") then {
        0.5 + 0.5 * sin (_t * 360 * (_owl getVariable "zom_freq") - 40)
    } else { 0.45 };
    {
        _owl animate [_x select 0, _x select 1, true];
    } forEach [
        ["wing_flap_l", _flapPhase], ["wing_flap_r", _flapPhase],
        ["wingtip_flap_l", _tipPhase], ["wingtip_flap_r", _tipPhase]
    ];

    // Bank into turns based on the bird's change of heading.
    private _dir = getDir _bird;
    private _turn = ((_dir - (_owl getVariable "zom_lastDir") + 540) % 360) - 180;
    _owl setVariable ["zom_lastDir", _dir];
    private _bank = ((_turn / (diag_deltaTime max 0.001)) / 90) max -1 min 1;  // ~90 deg/s = full bank
    _owl animate ["body_bank", 0.5 + 0.5 * _bank, true];

    // Slow scanning head turn.
    _owl animate ["head_turn", 0.5 + 0.35 * sin (_t * 25), true];
}, [_owl]];

_owl setVariable ["zom_frameEH", _id];
