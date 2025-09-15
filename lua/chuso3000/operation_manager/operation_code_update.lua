equal_tracks = {{32, 33, 40}, {34, 35}, {38, 39}}
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

gB, sB, sN = input.getBool, output.setBool, output.setNumber
function gI(c)
	return math.floor(input.getNumber(c))
end

function onTick()
	updated = gB(3) or gB(4) or gB(6)
	swap, chk_swap, set_man, set_auto = gB(9) or gB(13), gB(10), gB(11), gB(12)
	op_code_a, op_code_b, op_code_c, loc_code = gI(3), gI(4), gI(5), gI(6)
	type_a, dest_a = op_code_a >> 12 & 15, op_code_a & 63
	type_b, origin_b, dest_b = op_code_b >> 12 & 15, op_code_b >> 6 & 63, op_code_b & 63
	is_man_c = op_code_c >> 6 & 63 ~= 0
	status, loc_id1, loc_id2 = loc_code >> 12 & 3, loc_code >> 6 & 63, loc_code & 63
	type_man, dest_man = gI(9), gI(10)
	is_turn_back = track_equals(loc_id1, dest_a, origin_b) and (status == 3 or status == 1)

	set_op_code_c = nil

	if set_man then
		set_op_code_c = (type_man & 15) << 12 | 1 << 6 | dest_man & 63
	elseif updated and not is_man_c or set_auto then
		new_type, new_dest = 0, 0
		if is_turn_back then
			set_op_code_c = type_b << 12 | dest_b
		else
			set_op_code_c = type_a << 12 | dest_a
		end
	end

	if chk_swap and dest_a ~= 0 and is_turn_back then
		swap = true
	end

	sB(1, set_op_code_c ~= nil)
	sN(1, set_op_code_c or 0)
	sB(2, swap)
	sN(2, swap and 2 << 3 | 3 or 0)
end
