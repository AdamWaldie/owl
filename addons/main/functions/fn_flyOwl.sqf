/*
    zom_fnc_flyOwl
    Moves and animates one local owl for one frame.

    Flight: the owl circles its target (the Zeus camera) on a slowly bobbing
    orbit below it. It steers toward its orbit point, so when the camera moves
    it chases at up to maxSpeed, and beyond teleportDistance it simply reappears.
    It banks into turns from its sideways acceleration and keeps clear of terrain.

    Animation (model.cfg in addons/owl): flaps when climbing or chasing, and
    otherwise alternates short flapping and gliding spells. Wingtips trail the
    main stroke, and the head turns toward the camera it is circling.

    Params:
        0: OBJECT - owl (local simple object)
        1: ARRAY  - target position ASL
        2: NUMBER - frame time (s)
*/
params ["_owl", "_target", "_dt"];
(_owl getVariable "zom_state") params ["_ang", "_r", "_vel", "_mode", "_modeUntil", "_seed", "_bank", "_wing", "_tip"];

private _speed = zom_cfg get "speed";
private _clear = zom_cfg get "clearance";
private _p = getPosASL _owl;

// --- Orbit point ---------------------------------------------------------
_ang = (_ang + _dt * (_speed / _r) * 57.2958) mod 360;
private _bob = 0.8 * sin (time * 17 + _seed * 3.6);
private _d = _target vectorAdd [_r * sin _ang, _r * cos _ang, (zom_cfg get "height") + _bob];
private _floor = ((getTerrainHeightASL _d) max 0) + _clear;
if ((_d select 2) < _floor) then { _d set [2, _floor]; };

// --- Steering --------------------------------------------------------------
private _toD = _d vectorDiff _p;
private _accel = [0, 0, 0];
if (vectorMagnitude _toD > (zom_cfg get "teleport")) then {
    _p = +_d;
    _vel = [0, 0, 0];
} else {
    private _tangent = [cos _ang, -(sin _ang), 0] vectorMultiply _speed;
    private _want = _tangent vectorAdd (_toD vectorMultiply 1.2);
    if (vectorMagnitude _want > (zom_cfg get "maxSpeed")) then {
        _want = (vectorNormalized _want) vectorMultiply (zom_cfg get "maxSpeed");
    };
    _accel = (_want vectorDiff _vel) vectorMultiply 2;
    _vel = _vel vectorAdd (_accel vectorMultiply (_dt min 0.5));
    _p = _p vectorAdd (_vel vectorMultiply _dt);
};
private _pFloor = ((getTerrainHeightASL _p) max 0) + _clear * 0.5;
if ((_p select 2) < _pFloor) then { _p set [2, _pFloor]; };
_owl setPosASL _p;

// --- Orientation: face along velocity, limited pitch, bank into turns ---------
private _dir = vectorDir _owl;
if (vectorMagnitude _vel > 0.5) then {
    private _v = vectorNormalized _vel;
    if (abs (_v select 0) + abs (_v select 1) > 0.05) then {
        _dir = vectorNormalized [_v select 0, _v select 1, ((_v select 2) max -0.4) min 0.4];
    };
};
private _right = vectorNormalized (_dir vectorCrossProduct [0, 0, 1]);
private _latG = ((_accel vectorDotProduct _right) / 9.81) max -0.9 min 0.9;
_bank = _bank + (_latG - _bank) * ((_dt * 3) min 1);
private _up = [0, 0, 1] vectorAdd (_right vectorMultiply _bank);
_up = vectorNormalized (_up vectorDiff (_dir vectorMultiply (_up vectorDotProduct _dir)));
_owl setVectorDirAndUp [_dir, _up];

// --- Wing mode -------------------------------------------------------------------
private _chasing = vectorMagnitude _toD > 6;
if ((_vel select 2) > 0.6 || _chasing) then {
    _mode = "flap";
    _modeUntil = time + 1;
} else {
    if (time > _modeUntil) then {
        if (random 1 < (zom_cfg get "glide")) then {
            _mode = "glide";
            _modeUntil = time + 1.5 + random 2.5;
        } else {
            _mode = "flap";
            _modeUntil = time + 1.5 + random 2;
        };
    };
};

// --- Animation (skipped when far from this player's view) ---------------------
if ((positionCameraToWorld [0, 0, 0]) distance (ASLToAGL _p) < 800) then {
    private _freq = (zom_cfg get "flapFreq") * ([1, 1.4] select _chasing);
    private _beat = time * 360 * _freq + _seed * 36;
    private _wingTarget = [0.45, 0.5 + 0.5 * sin _beat] select (_mode == "flap");
    private _tipTarget = [0.45, 0.5 + 0.5 * sin (_beat - 40)] select (_mode == "flap");
    private _blend = (_dt * 12) min 1;
    _wing = _wing + (_wingTarget - _wing) * _blend;
    _tip = _tip + (_tipTarget - _tip) * _blend;
    _owl animate ["wing_flap_l", _wing, true];
    _owl animate ["wing_flap_r", _wing, true];
    _owl animate ["wingtip_flap_l", _tip, true];
    _owl animate ["wingtip_flap_r", _tip, true];

    // Head turns toward the camera it circles (model.cfg range is +-70 deg).
    private _heading = (_dir select 0) atan2 (_dir select 1);
    private _rel = (((_p getDir _target) - _heading) + 540) mod 360 - 180;
    _owl animate ["head_turn", (0.5 + _rel / 140) max 0 min 1, true];
    _owl animate ["body_bank", 0.5, true];
};

_owl setVariable ["zom_state", [_ang, _r, _vel, _mode, _modeUntil, _seed, _bank, _wing, _tip]];
