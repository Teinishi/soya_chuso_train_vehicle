stop_pos = {} -- @require route_data_lua.py stop_position_table

GRAVITY=10
M=math
max,sqrt=M.max,M.sqrt
function clamp(x,a,b)
	return M.min(max(x,a),b)
end

function decel_to_step_range(d)
	return clamp(d//0.125, 0, 31), clamp(d//0.125 + 1, 0, 31)
end
TASC_PATTERNS = {
	{decel = 0.5, offset = -0.1},
	{decel = 1.5, offset = 0.5},
	{decel = 3.0, offset = 4}
}
ATO_DECEL = 2.0

gB, gN, sB, sN = input.getBool, input.getNumber, output.setBool, output.setNumber
function onTick()
	tasc_active, ato_active = gB(1), gB(2)
	speed, tilt = 3.6*gN(9), gN(15)
	k = clamp(15/speed, 0.5, 1)

	ready, stopped = false, false
	ato_latch_on, ato_latch_off = false, true
	decel_t, ato_power, brake_step_a, brake_step_b = -4, 0, 0, 0

	if tasc_active then
		gps_x, gps_y = gN(1), gN(3)
		cars = gN(19) + gN(20) + 1
		loc_code = M.floor(gN(18))
		inb, outb, sts, id1, id2 = loc_code>>15&1~=0, loc_code>>14&1~=0, loc_code>>12&3, loc_code>>6&63, loc_code&63

		trpn = gB(3)
		trpn_distance = gN(21)

		target, distance = nil, nil
		if trpn then
			distance = trpn_distance
			ready = true
		else
			if sts == 2 then
				target = stop_pos[id2]
			elseif sts == 3 then
				target = stop_pos[id1]
			end
			if target then
				if inb then
					target = target[1]
				elseif outb then
					target = target[2]
				else
					target = nil
				end
			end
			if target then
				for _, v in ipairs(target) do
					if v[3] == nil or v[3] >= cars then
						target = v
						break
					end
				end
				ready = true

				distance = sqrt((gps_x - target[1])^2 + (gps_y - target[2])^2) - 5
			end
		end
		if distance then
			decel_t = nil
			for _, p in ipairs(TASC_PATTERNS) do
				v = 3.6*sqrt(max(2*p.decel/3.6*(distance - p.offset),0))
				d = k*(speed - v) + p.decel
				if decel_t == nil or d < decel_t then
					decel_t = d
				end
			end
			decel_t = decel_t or -4

			stopped = distance < 0.5 and speed < 0.5
		end
	end

	if ato_active then
		atc_green, ato_power_latch = gB(4), gB(5)
		atc_notice, atc_aspect = gN(22), gN(23)

		if speed > atc_notice then
			decel_t = max(decel_t, k*(speed - (atc_aspect - 5)) + ATO_DECEL)
			ato_latch_on = speed < atc_aspect - 17
			ato_latch_off = speed > atc_aspect - 10
		else
			ato_latch_on = speed < atc_aspect - 12
			ato_latch_off = speed > atc_aspect - 5
		end

		if not atc_green then
			ato_latch_on = false
		end

		if decel_t > 0 then
			ato_latch_off = true
		elseif ato_power_latch then
			ato_power = 4
		end

		if speed < 0.5 and not ato_power_latch then
			decel_t = max(decel_t, ATO_DECEL)
		end
	end

	if decel_t > 0 then
		brake_step_a, brake_step_b = decel_to_step_range(decel_t - 3.6*GRAVITY*M.sin(tilt*2*M.pi))
	end

	sB(1, tasc_active)
	sB(2, ready)
	sB(3, ato_active)
	sN(2, ato_power)
	sN(3, decel_t)
	sB(30, stopped)
	sB(31, ato_latch_on)
	sB(32, ato_latch_off)
	sN(31, brake_step_a)
	sN(32, brake_step_b)
end
