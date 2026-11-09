/*
    zom_fnc_removeBirds
    Loop, every machine. Removes the vanilla bird the Game Master module keeps
    near each curator camera (stored on the curator logic as "bird").

    - Server running the mod: the server deletes global birds, and the machine that
      owns a bird deletes it too (covers birds that only exist on the curator's PC).
    - Server NOT running the mod: never delete for everyone; just hide it on this
      client, so players without the mod still see their seagull.

    If the module keeps re-creating its bird, deleting would make it flicker, so
    after repeated re-creations for one curator we switch to hiding it instead.
*/
private _interval = getNumber (configFile >> "zom_settings" >> "birdScanInterval") max 0.1;
private _maxDeletes = 10;

while {true} do {
    private _serverActive = missionNamespace getVariable ["zom_serverActive", false];
    {
        private _curator = _x;
        private _bird = _curator getVariable ["bird", objNull];
        if (!isNull _bird && {!(_bird getVariable ["zom_handled", false])}) then {
            _bird setVariable ["zom_handled", true];
            private _deletes = _curator getVariable ["zom_birdDeletes", 0];
            private _mayDelete = _serverActive && {isServer || {local _bird}} && {_deletes < _maxDeletes};
            if (_mayDelete) then {
                _curator setVariable ["zom_birdDeletes", _deletes + 1];
                deleteVehicle _bird;
                if (_deletes + 1 == _maxDeletes) then {
                    diag_log format ["[ZOM] Curator %1 keeps re-creating its bird; hiding new ones instead of deleting.", _curator];
                };
            } else {
                _bird hideObject true;
                _bird enableSimulation false;
            };
        };
    } forEach allCurators;
    sleep _interval;
};
