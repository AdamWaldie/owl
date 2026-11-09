/*
    zom_fnc_shareCamera
    Loop, machines with a player. While this player is in the Zeus interface,
    publishes the camera position on their curator logic as "zom_camPos" so every
    client can fly an owl around it. Sends only when the camera moved > 2 m
    (or every 3 s as a keep-alive), and [] once when the interface closes.
*/
private _interval = getNumber (configFile >> "zom_settings" >> "cameraShareInterval") max 0.1;
private _last = [];
private _lastTime = -1e9;
private _lastCurator = objNull;

while {true} do {
    private _curator = getAssignedCuratorLogic player;

    // Curator changed (or lost): clear the old one's position.
    if (!(_curator isEqualTo _lastCurator)) then {
        if (!isNull _lastCurator && {_last isNotEqualTo []}) then {
            _lastCurator setVariable ["zom_camPos", [], true];
        };
        _last = [];
        _lastCurator = _curator;
    };

    if (!isNull _curator) then {
        private _cam = curatorCamera;
        if (isNull _cam) then {
            if (_last isNotEqualTo []) then {
                _curator setVariable ["zom_camPos", [], true];
                _last = [];
            };
        } else {
            private _pos = getPosASL _cam;
            if (_last isEqualTo [] || {_pos distance _last > 2} || {time - _lastTime > 3}) then {
                _curator setVariable ["zom_camPos", _pos, true];
                _last = _pos;
                _lastTime = time;
            };
        };
    };
    sleep _interval;
};
