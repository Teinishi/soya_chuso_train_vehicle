R1,R2=50,400
link_table = {} -- @require lua/route_data_lua.py link_table
stop_type_table = {} -- @require lua/route_data_lua.py stop_type_table
coordinate_table = {} -- @require lua/route_data_lua.py coordinate_table
not_for_service = {} -- @require lua/route_data_lua.py not_for_service

local function b2i(f)
	return f and 1 or 0
end

local function get_rel(id, rel, rte)
	for i, v in ipairs(rte) do
		if v == id then
			return rte[i + rel] or 0
		end
	end
	return 0
end

local function find_route(from, to, inbound)
	if not link_table[from*2 - b2i(inbound)] then return end
	local trace, queue = {[from] = from}, {from}
	for _ = 1, 100 do
		for _, v in ipairs(link_table[queue[1]*2 - b2i(inbound)] or {})do
			if not trace[v] then
				table.insert(queue, v)
				trace[v] = queue[1]
			end
		end
		table.remove(queue,1)
		if #queue == 0 then break end
	end
	if trace[to] then
		local route = {to, inbound = inbound, outbound = not inbound}
		for _ = 1, 100 do
			if to == from then break end
			table.insert(route, 1, trace[to])
			to = trace[to]
		end
		return route
	end
end

local function get_route(origin, destination)
	local rte_in, rte_out = find_route(origin, destination, true), find_route(origin, destination)
	if rte_in and rte_out then
		return #rte_in < #rte_out and rte_in or rte_out
	end
	return rte_in or rte_out or {}
end

local gB, gN, sB, sN = input.getBool, input.getNumber, output.setBool, output.setNumber
local function gI(c)
	return math.floor(gN(c))
end

function onTick()
	local updated = gB(3) or gB(6)
	local set_manual, go_prev, go_next, set_auto, update_auto, attempt_swap, door, stopped, update_nearest = gB(9), gB(10), gB(11), gB(12), gB(13), gB(14), gB(15), gB(16), gB(17)
	local op_code, stby_op_code, loc_code, set_manual_val = gI(3), gI(4), gI(6), gI(9)
	local gps_x, gps_y = gN(10), gN(11)

	local train_type, origin, destination = op_code>>12&15, op_code>>6&63, op_code&63
	local stby_origin, stby_destination = stby_op_code>>6&63, stby_op_code&63
	local is_manual, status, id1 = loc_code>>16&1 ~= 0, loc_code>>12&3, loc_code>>6&63

	local function distance(i, j)
		local a, b = coordinate_table[i], {gps_x,gps_y}
		if j then
			b = coordinate_table[j]
		end
		if a and b then
			return (a[1] - b[1])^2 + (a[2] - b[2])^2
		end
		return math.huge
	end

	local function is_stop(id, rte)
		if rte[1] == id or rte[#rte] == id then
			return true
		end
		for _, v in ipairs(stop_type_table[id] or {}) do
			if v == train_type then
				return true
			end
		end
	end

	local set_location_code = nil
	local function set_location(new_status, new_id1, rte, man)
		local f, nxstp = false, 0
		for _, v in ipairs(rte) do
			f = f or new_status == 2 and v == new_id1
			if f and is_stop(v, rte) then
				nxstp = v
				break
			end
			f = f or v == new_id1
		end
		set_location_code = b2i(man)<<16 | b2i(rte.inbound)<<15 | b2i(rte.outbound)<<14 | (new_status&3)<<12 | (new_id1&63)<<6 | nxstp&63
	end

	local nearest_id = nil
	local function nearest()
		if not nearest_id then
			local nd2 = nil
			for i = 1, #coordinate_table do
				local d2 = distance(i)
				if not nd2 or d2 < nd2 then
					nd2, nearest_id = d2, i
				end
			end
			if nd2 > R1^2 then
				nearest_id=0
			end
		end
		return nearest_id
	end
	if update_nearest then
		nearest()
	end

	local set_prev, swap = nil, false
	if set_manual then
		set_location(1, set_manual_val, get_route(origin, destination), true)

	elseif go_next then
		local route = get_route(origin, destination)
		local nx_trk = get_rel(id1, 1, route)
		local new_status = 0
		if status == 1 then
			new_status = nx_trk == 0 and 1 or 2
		elseif status == 2 then
			new_status = is_stop(id1, route) and 3 or 2
		elseif status == 3 then
			new_status = is_stop(id1, route) and 1 or 2
		end
		set_location(new_status, new_status == 2 and nx_trk or id1, route, is_manual)

	elseif go_prev then
		local route = get_route(origin, destination)
		local new_status, new_id1 = 0, id1
		if status == 1 then
			new_status = get_rel(id1, -1, route) == 0 and 1 or is_stop(id1,route) and 3 or 2
		elseif status == 2 then
			new_id1 = get_rel(id1, -1, route)
			new_status = is_stop(new_id1, route) and 1 or 2
		elseif status == 3 then
			new_status = 2
		end
		set_location(new_status, new_id1, route, is_manual)

	elseif set_auto or (update_auto or attempt_swap or update_nearest) and not is_manual then
		local route = get_route(origin, destination)
		nearest()
		if door and nearest_id ~= 0 or stopped and not_for_service[nearest_id] then
			swap = attempt_swap and nearest_id == destination and nearest_id == stby_origin
			if swap then
				route = get_route(stby_origin, stby_destination)
			end
			set_location(1, nearest_id, route)
		else
			local prev, next = get_rel(id1, -1, route), get_rel(id1, 1, route)
			local passed = false
			if prev ~= 0 and next ~= 0 then
				passed = distance(id1) >= R1^2 and distance(prev) / distance(prev, id1) > distance(next) / distance(next, id1)
			end
			next = (status == 1 or passed) and get_rel(id1, 1, route) or id1
			set_location(distance(next) < R2^2 and is_stop(next, route) and 3 or 2, next, route)
		end
	end

	if updated then
		set_prev = status <= 1 and id1 or get_rel(id1, -1, get_route(origin, destination))
	end

	sB(1, set_location_code ~= nil)
	sN(1, set_location_code or 0)
	sB(2, set_prev ~= nil)
	sN(2, set_prev or 0)
	local coordinate = coordinate_table[id1]
	if coordinate then
		sN(3, coordinate[1] - gps_x)
		sN(4, coordinate[2] - gps_y)
	else
		sN(3, 0)
		sN(4, 0)
	end
	sB(5, nearest_id ~= nil)
	sN(5, nearest_id or 0)
	sB(6, swap)
end
