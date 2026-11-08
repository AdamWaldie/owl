/*
    zom_fnc_init (postInit)
    Runs on every machine with an interface. Watches all curators and puts a
    local owl on each curator bird. Dedicated servers and headless clients skip
    this because they render nothing.
*/
if (!hasInterface) exitWith {};

[] spawn {
    private _interval = getNumber (configFile >> "zom_settings" >> "scanInterval") max 0.5;
    while {true} do {
        {
            private _bird = _x getVariable ["bird", objNull];
            if (!isNull _bird && {isNull (_bird getVariable ["zom_owl", objNull])}) then {
                [_bird] call zom_fnc_attachOwl;
            };
        } forEach allCurators;
        sleep _interval;
    };
};
