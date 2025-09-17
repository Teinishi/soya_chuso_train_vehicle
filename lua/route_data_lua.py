import json
from lib.script_resolver import RequireParams
from lib.lua_literal import to_lua_literal

ROUTE_DATA_PATH = "route_data.json"
ROUTE_DATA_JSMS_PATH = "route_data_jsms.json"

DOOR_OPEN = 1
DOOR_OPPOSITE = 3


def load(path: str):
    with open(path, encoding="utf-8") as f:
        route_data = json.load(f)
    types: list[dict] = route_data.get("types", [])
    stations: list[dict] = route_data.get("stations", [])
    tracks: list[dict] = [
        track for station in stations for track in station.get("tracks", [])]
    return (types, stations, tracks)


def create_link_table(tracks: list[dict]):
    link_table: dict[int, list[int]] = {}
    for track in tracks:
        track_id = track["id"]
        if "inbound" in track:
            link_table[2*track_id - 1] = track["inbound"]
        if "outbound" in track:
            link_table[2*track_id] = track["outbound"]
    return link_table


def create_stop_type_table(stations: list[dict]):
    stop_type_table: dict[int, list[int]] = {}
    for station in stations:
        stop_types = station.get("stopTypes", [])
        for track in station.get("tracks", []):
            stop_type_table[track["id"]] = stop_types
    return stop_type_table


def create_coordinate_table(tracks: list[dict]):
    coordinate_table: dict[int, tuple[float, float]] = {}
    for track in tracks:
        if "coordinate" in track:
            coordinate_table[track["id"]] = (
                track["coordinate"][0], track["coordinate"][1])
    return coordinate_table


def create_not_for_service_table(tracks: list[dict]):
    not_for_service_table: dict[int, int] = {}
    for track in tracks:
        if track.get("notForService", False):
            not_for_service_table[track["id"]] = 1
    return not_for_service_table


def create_index_table(stations: list[dict]):
    index_table: dict[int, int] = {}
    for station in stations:
        station_index: int = station["stationIndex"]
        for track in station.get("tracks"):
            index_table[track["id"]] = station_index
    return index_table


def create_door_side_table(tracks: list[dict]):
    def _door_data(side: str) -> int:
        if side == "left":
            return DOOR_OPEN | DOOR_OPPOSITE << 2
        elif side == "right":
            return DOOR_OPPOSITE | DOOR_OPEN << 2
        return 0

    door_side_table: dict[int, int] = {}
    for track in tracks:
        if "door" in track:
            door_side_table[track["id"]] = \
                _door_data(track["door"].get("outbound", None)) | \
                _door_data(track["door"].get("inbound", None)) << 4
    return door_side_table


def create_arc_type_table(types: list[dict]):
    arc_type_table: dict[int, list[int] | dict[str, int]] = {}
    for train_type in types:
        if "arc" in train_type:
            arc_type_table[train_type["id"]] = train_type["arc"]
    return arc_type_table


def create_arc_track_table(tracks: list[dict]):
    arc_track_table: dict[int, list[int] | dict[str, int]] = {}
    for track in tracks:
        if "arc" in track:
            arc_track_table[track["id"]] = track["arc"]
    return arc_track_table


def create_doorcut_table(tracks: list[dict]):
    def _doorcut_data(data) -> dict[str, int]:
        return {
            "i": data.get("inbound", None),
            "m": data.get("middle", None),
            "o": data.get("outbound", None)
        }

    doorcut_table: dict[int, tuple[dict[str, int], dict[str, int]]] = {}
    for track in tracks:
        if "doorcut" in track:
            doorcut_table[track["id"]] = (
                _doorcut_data(track["doorcut"].get("inbound", {})),
                _doorcut_data(track["doorcut"].get("outbound", {}))
            )
    return doorcut_table


def create_stop_position_table(tracks: list[dict]):
    def _format_stop_pos(stop_pos: dict[str, list[float]] | list[float] | None) -> list[list[float]]:
        if stop_pos is None:
            stop_pos = {}
        elif isinstance(stop_pos, list):
            stop_pos = {"default": stop_pos}

        tbl: list[list[float]] = []
        for k in sorted(stop_pos.keys()):
            tbl.append([stop_pos[k][0], stop_pos[k][1],
                        int(k) if k != "default" else None])
        return tbl

    stop_position_table: \
        dict[int, tuple[list[list[float]]], list[list[float]]] = {}
    for track in tracks:
        p = track.get("stopPosition", {})
        p_inbound = p.get("inbound", None)
        p_outbound = p.get("outbound", None)
        if p_inbound is not None or p_outbound is not None:
            stop_position_table[track["id"]] = (
                _format_stop_pos(p_inbound),
                _format_stop_pos(p_outbound)
            )
    return stop_position_table


def create_jsms_pass_list(stations: list[dict]):
    jsms_pass_list: set[int] = set()
    for station in stations:
        if station.get("jsmsPass", False):
            for track in station.get("tracks", []):
                jsms_pass_list.add(track["id"])
    return list(sorted(jsms_pass_list))


def create_jsms_route(stations: list[dict]):
    track_station_index: dict[int, int] = {}
    for i, station in enumerate(stations):
        for track in station.get("tracks", []):
            track_station_index[track["id"]] = i

    station_order: list[int] = []
    primary_tracks: set[int] = set()
    for i, station in enumerate(stations):
        if "jsmsNext" not in station:
            continue
        jsmsNext = station["jsmsNext"]
        primary_tracks.add(jsmsNext)
        j = track_station_index[jsmsNext]
        try:
            station_order.insert(station_order.index(i) + 1, j)
        except ValueError:
            station_order.append(i)
            station_order.append(j)

    jsms_route: list[list[int]] = []
    for i in station_order:
        station = stations[i]
        track_ids = [track["id"] for track in station.get("tracks", [])]
        track_ids.sort(key=lambda t: -9999 if t in primary_tracks else t)
        jsms_route.append(track_ids)
    return jsms_route


def create_track_groups(stations: list[dict]):
    groups: dict[str, set[int]] = {}
    for station in stations:
        group_name = station.get("group")
        if group_name is None:
            continue
        track_ids = {track["id"] for track in station.get("tracks", [])}
        if group_name not in groups:
            groups[group_name] = track_ids
        else:
            groups[group_name].update(track_ids)

    track_groups: list[list[int]] = []
    for station_indices in groups.values():
        if len(station_indices) >= 2:
            track_groups.append(list(sorted(station_indices)))
    return track_groups


types, stations, tracks = load(ROUTE_DATA_PATH)
_, jsms_stations, jsms_tracks = load(ROUTE_DATA_JSMS_PATH)

data = {
    "link_table": create_link_table(tracks),
    "stop_type_table": create_stop_type_table(stations),
    "coordinate_table": create_coordinate_table(tracks),
    "index_table": create_index_table(stations),
    "jsms_index_table": create_index_table(stations + jsms_stations),
    "door_side_table": create_door_side_table(tracks),
    "jsms_door_side_table": create_door_side_table(tracks + jsms_tracks),
    "not_for_service": create_not_for_service_table(tracks),
    "jsms_not_for_service": create_not_for_service_table(tracks + jsms_tracks),
    "arc_type_table": create_arc_type_table(types),
    "arc_track_table": create_arc_track_table(tracks),
    "doorcut_table": create_doorcut_table(tracks),
    "stop_position_table": create_stop_position_table(tracks),
    "jsms_pass_list": create_jsms_pass_list(stations + jsms_stations),
    "jsms_route": create_jsms_route(stations + jsms_stations),
    "jsms_track_groups": create_track_groups(stations + jsms_stations)
}


def require(params: RequireParams):
    is_jsms = params.build_params.get("is_jsms", False)

    w = params.require_param_text.split(" ")
    is_lcd = "lcd" in w
    target = w[-1]

    if is_jsms and is_lcd:
        target = f"jsms_{target}"

    return to_lua_literal(data[target])
