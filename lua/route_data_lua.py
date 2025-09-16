import json

ROUTE_DATA_PATH = "route_data.json"
ROUTE_DATA_JSMS_PATH = "route_data_jsms.json"

DOOR_OPEN = 1
DOOR_OPPOSITE = 3


def door_data(side: str) -> int:
    if side == "left":
        return DOOR_OPEN | DOOR_OPPOSITE << 2
    elif side == "right":
        return DOOR_OPPOSITE | DOOR_OPEN << 2
    return 0


def doorcut_data(data):
    return {
        "i": data.get("inbound", None),
        "m": data.get("middle", None),
        "o": data.get("outbound", None)
    }


def format_stop_pos(stop_pos: dict[str, list[float]] | list[float] | None) -> list[list[float]]:
    if stop_pos is None:
        stop_pos = {}
    elif isinstance(stop_pos, list):
        stop_pos = {"default": stop_pos}

    tbl: list[list[float]] = []
    for k in sorted(stop_pos.keys()):
        tbl.append([stop_pos[k][0], stop_pos[k][1],
                    int(k) if k != "default" else None])
    return tbl


def generate_lua_tables(types: list[dict], stations: list[dict]):
    link_table = {}
    stop_type_table = {}
    coordinate_table = {}
    not_for_service_table = {}
    index_table = {}
    door_side_table = {}
    arc_type_table = {}
    arc_trk_table = {}
    doorcut_table = {}
    stop_position_table = {}

    for train_type in types:
        type_id = train_type["id"]

        arc_type_table[type_id] = train_type.get("arc", None)

    for station_idx, station in enumerate(stations):
        stop_types = station.get("stopTypes", [])

        for track in station.get("tracks", []):
            track_id = track["id"]
            not_for_service = track.get("notForService", False)
            outbound = track.get("outbound", None)
            inbound = track.get("inbound", None)
            coordinate = track.get("coordinate", None)
            stop_position = track.get("stopPosition", {})

            link_table[2*track_id - 1] = inbound
            link_table[2*track_id] = outbound
            stop_type_table[track_id] = stop_types
            if coordinate is not None:
                coordinate_table[track_id] = [coordinate[0], coordinate[1]]

            if not_for_service:
                not_for_service_table[track_id] = 1
            index_table[track_id] = station.get("lcdIndex", station_idx + 1)

            door_side = track.get("door", None)
            if door_side:
                door_side_table[track_id] = \
                    door_data(door_side.get("outbound", None)) | \
                    door_data(door_side.get("inbound", None)) << 4
            else:
                door_side_table[track_id] = None

            arc_trk_table[track_id] = track.get("arc", None)

            if "doorcut" in track:
                doorcut = track.get("doorcut", {})
                doorcut_table[track_id] = [
                    doorcut_data(doorcut.get("inbound", {})),
                    doorcut_data(doorcut.get("outbound", {}))
                ]

            stop_position_inbound = stop_position.get("inbound", None)
            stop_position_outbound = stop_position.get("outbound", None)

            if stop_position_inbound is not None or stop_position_outbound is not None:
                stop_position_table[track_id] = [
                    format_stop_pos(stop_position_inbound),
                    format_stop_pos(stop_position_outbound)
                ]

    return {
        "link_table": link_table,
        "stop_type_table": stop_type_table,
        "coordinate_table": coordinate_table,
        "index_table": index_table,
        "door_side_table": door_side_table,
        "not_for_service": not_for_service_table,
        "arc_type_table": arc_type_table,
        "arc_track_table": arc_trk_table,
        "doorcut_table": doorcut_table,
        "stop_position_table": stop_position_table
    }


def main(jsms: bool, target: str):
    with open(ROUTE_DATA_PATH, encoding="utf-8") as f:
        route_data = json.load(f)
        types = route_data.get("types", [])
        stations = route_data.get("stations", [])

    if jsms:
        with open(ROUTE_DATA_JSMS_PATH, encoding="utf-8") as f:
            route_data = json.load(f)
            types += route_data.get("types", [])
            stations += route_data.get("stations", [])

    data = generate_lua_tables(types, stations)
    print(json.dumps(data[target]))


if __name__ == "__main__":
    params = json.loads(input())
    is_jsms = params.get("build_params", {}).get("is_jsms", False)
    require_params: list[str] = params["require_param_text"].split(" ")
    is_lcd = "lcd" in require_params
    target = require_params[-1]
    main(is_jsms and is_lcd, target)
