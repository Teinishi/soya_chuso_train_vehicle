is_outbound = property.getBool('Direction')
doorcut_table = {} -- @require route_data_lua.py doorcut_table

function bit_at(n, i)
	return n >> i & 1 ~= 0
end

gB, sB, sN = input.getBool, output.setBool, output.setNumber
function gI(c)
	return math.floor(input.getNumber(c))
end

function onTick()
	dir_f = gB(30)
	loc_code, nearest = gI(6), gI(30)
	cars_total = gI(31) + gI(32) + 1

	is_loc_man, inbound, outbound = bit_at(loc_code, 16), bit_at(loc_code, 15), bit_at(loc_code, 14)
	sts, id1 = loc_code >> 12 & 3, loc_code >> 6 & 63

	doorcut_id, doorcut_f, doorcut_b = nil, nil, nil

	doorcut_id = (not is_loc_man and nearest ~= 0) and nearest or id1
	data = doorcut_table[doorcut_id]
	if data then
		if inbound then
			data = data[1]
		elseif outbound then
			data = data[2]
		else
			data = nil
		end
	end

	if data and data.m and 6 * cars_total > data.m then
		if data.i then
			doorcut_f, doorcut_b = data.i, 6 * cars_total - data.i - data.m
		elseif data.o then
			doorcut_f, doorcut_b = 6 * cars_total - data.o - data.m, data.o
		end
	end
	if is_outbound then
		doorcut_f, doorcut_b = doorcut_b, doorcut_f
	end

	sB(1, doorcut_f ~= nil)
	sN(1, doorcut_f or 0)
	sN(2, doorcut_b or 0)
	sB(32, doorcut_id ~= nil)
	sN(32, doorcut_id or 0)
end
