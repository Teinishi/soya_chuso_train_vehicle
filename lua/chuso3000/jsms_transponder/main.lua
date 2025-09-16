TENJIJO = {
	{33, 32},
	{0, 36},
	{0, 40}
}
SHIONAGIHAMA = {
	{34, 35},
	{38, 39},
	{34, 35}
}
function get_track(pos, count, door_side)
	count = clamp(math.floor(count), 0, 2)
	if math.abs(pos) < 10 then
		if door_side == 0 then
			door_side = 2
		end
		return TENJIJO[count + 1][door_side] or 0
	elseif math.abs(pos - 530) < 10 then
		if door_side == 0 then
			door_side = counter == 1 and 1 or 2
		end
		return SHIONAGIHAMA[count + 1][door_side] or 0
	end
	return 0
end
function get_rel(id, rel, rte)
	for i, v in ipairs(rte) do
		if v == id then
			return rte[i+rel] or 0
		end
	end
	return 0
end
function get_next(id)
	return ({
		[32] = 35,
		[33] = 35,
		[34] = 36,
		[35] = 36,
		[36] = 38,
		[38] = 40,
		[39] = 40,
		[40] = 43,
		[42] = 36,
		[43] = 36
	})[id] or 0
end

function clamp(x, a, b)
	return math.min(math.max(x, a), b)
end

gB, gN = input.getBool, input.getNumber

function onTick()
	passed_pulse, door_open_pulse, after_door_open_pulse, door_close_pulse = gB(26), gB(27), gB(28), gB(29)
	cars, counter, pulse = gN(28), gN(29), gN(30) ~= 0
	ttype = math.floor(gN(32)) >> 12 & 15

	tasc, platform_door, distance_enabled = gB(1), gB(2), gB(3)
	ato_active, jsms_latch, blink_pulse, blink_counter = gB(30), gB(31), gB(32), gN(31)
	distance = gN(cars <= 1 and 10 or 9)
	transponder_pos, door_side = gN(11), gN(12)

	new_sts, new_id1 = nil, nil
	set_jsms_latch_on, set_jsms_latch_off = false, false

	set_menu_guidance = nil
	if jsms_latch and blink_pulse then
		if blink_counter == 0 and not ato_active then
			set_menu_guidance = 15
		else
			set_menu_guidance = 9 + blink_counter
		end
	end

	if (door_open_pulse or after_door_open_pulse) and platform_door then
		new_sts = 1
		new_id1 = get_track(transponder_pos, after_door_open_pulse and counter or (counter - 1) % 2 + 1, door_side)

	elseif door_close_pulse and platform_door then
		new_sts = 2
		new_id1 = get_next(get_track(transponder_pos, counter, door_side))
		set_jsms_latch_on = new_id1 == TENJIJO[2][2]

	elseif pulse and tasc and distance_enabled then
		new_id1 = get_track(transponder_pos + distance, (counter - 1) % 2 + 1, door_side)
		if new_id1 ~= 0 then
			new_sts = counter == 1 and ttype ~= 5 and 2 or 3
		end
		if new_sts == 3 then
			set_menu_guidance = 0
			set_jsms_latch_off = true
		end

	elseif passed_pulse and platform_door then
		new_sts = 2
		new_id1 = get_next(get_track(transponder_pos, counter, door_side))
	end

	loc_set = nil
	if new_sts ~= nil then
		loc_set = new_sts << 6 | (new_id1 or 0)
	end

	output.setBool(1, loc_set ~= nil)
	output.setNumber(1, loc_set or 0)
	output.setBool(2, set_jsms_latch_on)
	output.setBool(3, set_jsms_latch_off)
	output.setBool(20, set_menu_guidance ~= nil)
	output.setNumber(20, set_menu_guidance or 0)
end
