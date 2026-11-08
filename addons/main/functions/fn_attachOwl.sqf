/*
    zom_fnc_attachOwl
    Hides a curator bird on this client and attaches a local owl in its place.

    Params:
        0: OBJECT - the curator bird

    Returns: OBJECT - the owl (objNull on failure)
*/
params [["_bird", objNull, [objNull]]];
if (isNull _bird) exitWith {objNull};

private _cfg = configFile >> "zom_settings";
private _model = getText (_cfg >> "model");

// Local simple object: no simulation, no network sync, supports model.cfg animations.
private _owl = createSimpleObject [_model, getPosASL _bird, true];
if (isNull _owl) exitWith {
    diag_log format ["[ZOM] Could not create owl from model %1", _model];
    objNull
};

_owl setObjectScale (getNumber (_cfg >> "scale") max 0.1);
_owl attachTo [_bird, [0, 0, 0]];
_bird hideObject true;                     // local only - other clients do the same
_bird setVariable ["zom_owl", _owl];

// Clean up when the vanilla bird goes away (curator leaves, module deleted, etc).
_bird addEventHandler ["Deleted", {
    params ["_bird"];
    deleteVehicle (_bird getVariable ["zom_owl", objNull]);
}];

[_owl, _bird] call zom_fnc_animateOwl;
_owl
