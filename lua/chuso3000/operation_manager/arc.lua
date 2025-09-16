link_table = {} -- @require lua/route_data_lua.py link_table
arc_type_table = {} -- @require lua/route_data_lua.py arc_type_table
arc_track_table = {} -- @require lua/route_data_lua.py arc_track_table

function find_rte(from,to,inb)
	if not link_table[from] then return end
	tr,q={[from]=from},{from}
	for _=1,100 do
		for _,v in ipairs(link_table[q[1]*2-(inb and 1 or 0)] or {}) do
			if not tr[v] then
				table.insert(q,v)
				tr[v]=q[1]
			end
		end
		table.remove(q,1)
		if #q==0 then break end
	end
	if tr[to] then
		rte={to,inb=inb,outb=not inb}
		for _=1,100 do
			if to==from then break end
			table.insert(rte,1,tr[to])
			to=tr[to]
		end
		return rte
	end
end

function arc_val(d)
	if d then
		return d.min or d[1] or 0
	end
	return 0
end

function get_arc(op_code)
	ttype, origin, dest = op_code >> 12 & 15, op_code >> 6 & 63, op_code & 63

	arc = 100 * arc_val(arc_type_table[ttype]) + arc_val(arc_track_table[dest])
	if find_rte(origin, dest, false) then
		arc = arc + 20000
	elseif find_rte(origin, dest, true) then
		arc = arc + 10000
	end

	return arc
end

function arc_check(val, data)
	if data == nil then
		return false
	elseif data.min and data.max and data.min <= val and val <= data.max then
		return true
	end
	for _, w in ipairs(data) do
		if w == val then
			return true
		end
	end
end

function arc_find(val, tbl)
	r = 0
	for i, v in pairs(tbl) do
		if (r == 0 or i < r) and arc_check(val, v) then
			r = i
		end
	end
	return r
end

function get_op_code(arc, loc_code)
	origin = loc_code >> 6 & 63
	ttype, dest = arc_find(arc // 100 % 100, arc_type_table), arc_find(arc % 100, arc_track_table)
	return (ttype & 15) << 12 | (origin & 63) << 6 | dest & 63
end

gB, sB, sN = input.getBool, output.setBool, output.setNumber
function gI(c)
	return math.floor(input.getNumber(c))
end

function onTick()
	swap, keypad_to_arc, keypad_to_op_code_a = gB(9), gB(10), gB(11)
	op_code_b, loc_code, keypad = gI(4), gI(6), gI(9)

	set_arc, set_op_code_a = nil, nil

	if swap then
		set_arc = get_arc(op_code_b)
	elseif keypad_to_arc then
		set_arc = keypad
	elseif keypad_to_op_code_a then
		set_op_code_a = get_op_code(keypad, loc_code)
	end

	sB(1, set_arc ~= nil)
	sN(1, set_arc or 0)
	sB(2, set_op_code_a ~= nil)
	sN(2, set_op_code_a or 0)
end
