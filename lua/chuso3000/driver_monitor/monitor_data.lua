M = math

floor = M.floor
function clamp(x, a, b)
	return M.min(M.max(x, a), b)
end

function as_trk_id(x)
	return clamp(floor(x), 0, 47)
end

function as_type_id(x)
	return clamp(floor(x), 0, 8)
end

function sel(f, a, b)
	return f and a or b
end

gB, sB, sN = input.getBool, output.setBool, output.setNumber
function gI(c)
	return floor(input.getNumber(c))
end

function onTick()
	blink_long, blink_short = gB(1), gB(2)

	op_num, arc_num, op_code_a, op_code_b, op_code_c, loc_code = gI(1), gI(2), gI(3), gI(4), gI(5), gI(6)
	type_a, origin_a, dest_a = op_code_a >> 12 & 15, op_code_a >> 6 & 63, op_code_a & 63
	type_b, origin_b, dest_b = op_code_b >> 12 & 15, op_code_b >> 6 & 63, op_code_b & 63
	type_c, origin_c, dest_c = op_code_c >> 12 & 15, op_code_c >> 6 & 63, op_code_c & 63
	is_loc_man, dir = loc_code >> 16 & 1 ~= 0, (loc_code >> 14 & 3) % 3
	status, loc_id1, loc_id2 = loc_code >> 12 & 3, loc_code >> 6 & 63, loc_code & 63
	stopping, running, approaching = status == 1, status >= 2, status == 3
	stop_or_pass = 0
	if status == 2 and loc_id1 ~= 0 then
		stop_or_pass = sel(loc_id1 == loc_id2, 1, 2)
	elseif status == 3 then
		stop_or_pass = 1
	end

	sN(9, sel(blink_long, 1, 0))

	sN(10, floor(op_num) % 100)

	sN(11, floor(arc_num) % 100)
	sN(12, arc_num // 100 % 1000)

	sN(13, as_type_id(type_a))
	sN(14, as_trk_id(sel(blink_long, dest_a, origin_a)))
	sN(15, as_trk_id(dest_a))

	sN(16, as_type_id(type_b))
	sN(17, as_trk_id(sel(blink_long, dest_b, origin_b)))

	sN(18, as_trk_id(type_c))
	sN(19, as_trk_id(dest_c))
	sB(4, op_code_c >> 6 & 63 ~= 0)

	sN(20, clamp(dir, 0, 2))
	sB(5, stopping)
	sB(6, running)
	sB(7, approaching)
	sB(8, running and not (approaching and blink_short))
	sN(21, as_trk_id(loc_id1))
	sN(22, stop_or_pass)

	sB(9, is_loc_man)
end
