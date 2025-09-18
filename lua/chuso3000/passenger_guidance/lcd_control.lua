not4srv = {} -- @require lua/route_data_lua.py lcd not_for_service
idx_tbl = {}  -- @require lua/route_data_lua.py lcd index_table
door_side_tbl = {} -- @require lua/route_data_lua.py lcd door_side_table
jsms_pass = {} -- @require lua/route_data_lua.py jsms_pass_list
jsms_route = {} -- @require lua/route_data_lua.py jsms_route
equal_tracks = {} -- @require lua/route_data_lua.py jsms_track_groups
train_type_tbl = {} -- @require lua/route_data_lua.py lcd_train_type_table

function sta_idx(id)
	if id < 32 then
		return idx_tbl[id] or 0
	end
	return (id - 32) % 4 < 2 and 13 or 9
end
function next_sta_id(id)
	for i = 1, #jsms_route - 1 do
		for _, v in ipairs(jsms_route[i]) do
			if v == id then
				return jsms_route[i + 1][1]
			end
		end
	end
	return 0
end
function includes(arr, target)
	for _, v in ipairs(arr) do
		if v == target then
			return true
		end
	end
end
function track_equals(a, b, c)
	if a == b and b == c then
		return true
	end
	for _, p in ipairs(equal_tracks) do
		if includes(p, a) and includes(p, b) and includes(p, c) then
			return true
		end
	end
end

ROUTE_MAP_N = 5
START_STA = 1
BORDER_STA = 9
END_STA = 12

pN, gB, gN, sB, sN = property.getNumber, input.getBool, input.getNumber, output.setBool, output.setNumber
function gI(c)
	return math.floor(gN(c))
end

is_front_outbound = property.getBool('Direction')
doors_l, doors_r = pN('Left side doors'), pN('Right side doors')

min, max = math.min, math.max
function clamp_range(range, a, b)
	o = min(max(0, a - min(range[1], range[2])), b - max(range[1], range[2]))
	return {range[1] + o, range[2] + o}
end

function onTick()
	op_code_a, op_code_b, loc_code, menu_guidance, doorcut_f, doorcut_b, stop_pattern = gI(3), gI(4), gI(6), gI(7), gI(12), gI(13), gI(15)
	eb, show_menu_guidance = gB(1), gB(2) and menu_guidance ~= 0
	anim = gN(14) % 3

	ttype_a, origin_a, dest_a = op_code_a >> 12 & 15, op_code_a >> 6 & 63, op_code_a & 63
	ttype_b, origin_b, dest_b = op_code_b >> 12 & 15, op_code_b >> 6 & 63, op_code_b & 63
	dir = (loc_code >> 14 & 1) - (loc_code >> 15 & 1)
	sts, id1, id2 = loc_code >> 12 & 3, loc_code >> 6 & 63, loc_code & 63
	is_jsms = id1 >= 32

	backwards = is_front_outbound ~= (dir > 0)
	train_type = train_type_tbl[ttype_a] or 0
	origin, dest = idx_tbl[origin_a] or 0, idx_tbl[dest_a] or 0
	top_msg = ({3, 1, 2})[sts] or 0
	sta_main = sta_idx(sts == 2 and id2 or id1)
	sta1, sta2 = sta_idx(id1), sta_idx(id2)

	is_last = dest == sta_main
	is_out_of_srv = sta_main == 0 or not4srv[id1]

	line_id = sta1 < BORDER_STA and 1 or 2
	if sta1 == BORDER_STA then
		if dir > 0 then
			line_id = BORDER_STA < dest and sts == 1 and 2 or 1
		elseif dir < 0 then
			line_id = dest < BORDER_STA and sts == 1 and 1 or 2
		end
	end

	if is_jsms then
		sta_main = sta_idx(sts == 2 and id2 or id1)
		line_id = 1
		is_last = false
		if sts == 3 and id1 == 40 then
			sta2 = 9
		end
	end

	door_left, door_right = 0, 0
	door_side = dir ~= 0 and door_side_tbl[id1]
	if door_side then
		if dir > 0 then
			door_left, door_right = door_side & 3, door_side >> 2 & 3
		else
			door_left, door_right = door_side >> 4 & 3, door_side >> 6 & 3
		end
	end
	if backwards then
		door_left, door_right = door_right, door_left
	end
	if doors_l - doorcut_f - doorcut_b <= 0 then
		door_left = 4
	end
	if doors_r - doorcut_f - doorcut_b <= 0 then
		door_right = 4
	end

	page = 1 + line_id
	if eb then
		page = 1
	elseif show_menu_guidance then
		page = 8
	elseif is_out_of_srv then
		page = 0
	elseif sts == 1 and is_last then
		page = line_id + 3
	elseif sts == 3 and door_side then
		page = 7
	elseif sts ~= 0 then
		page = is_jsms and 9 or 6
	end

	route_range = clamp_range({sta1, sta1 + (ROUTE_MAP_N - 1) * dir}, START_STA, END_STA)
	if backwards then
		route_range = {route_range[2], route_range[1]}
	end

	route_arrow, route_gray_i, route_gray_o = sta1, 0, 0
	if sts ~= 1 then
		route_arrow = route_arrow - dir / 2
	end

	if dir > 0 then
		stop_pattern = stop_pattern & -1 << (sta1 - 1)
	else
		route_arrow = -route_arrow
		stop_pattern = stop_pattern & (1 << sta1) - 1
	end

	jsms_map_2_id = next_sta_id(id1)
	jsms_map_1 = sta_idx(id1)
	jsms_map_2 = sta_idx(jsms_map_2_id)
	jsms_stop_1 = ttype_a == 5 or not includes(jsms_pass, id1)
	jsms_stop_2 = (track_equals(id1, dest_a, origin_b) and ttype_b or ttype_a) == 5 or not includes(jsms_pass, jsms_map_2_id)
	jsms_arrow_pos = sts == 1 and 2 or 1

	top_train_type, top_dest = train_type, sta_idx(dest_a)
	if is_last then
		top_train_type, top_dest = 0, 0
	end
	if is_last and top_msg ~= 0 then
		top_msg = top_msg + 3
	end
	if is_out_of_srv then
		top_msg, sta_main = 0, 0
	end

	sN(1, anim)
	sN(2, top_train_type)
	sN(3, top_dest)
	sN(4, top_msg)
	sN(5, sta_main)
	sN(6, page)

	sN(7, route_range[is_front_outbound and 2 or 1])
	sN(8, route_arrow)
	sN(9, stop_pattern)
	sN(10, math.min(origin, dest))
	sN(11, math.max(origin, dest))

	sN(12, door_left)
	sN(13, door_right)
	if not is_jsms and page == 7 and not is_last then
		sN(14, sta1)
		sN(15, sta2)
	else
		sN(14, 0)
		sN(15, 0)
	end

	sN(16, page == 8 and menu_guidance or 0)
	sB(16, page == 8)

	if page == 9 then
		sN(17, jsms_map_1)
		sN(18, jsms_map_2)
	else
		sN(17, 0)
		sN(18, 0)
	end
	sN(19, jsms_arrow_pos)
	sB(17, jsms_stop_1)
	sB(18, jsms_stop_2)
end
