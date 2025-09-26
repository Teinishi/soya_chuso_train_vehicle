BRAKE_STEPS = property.getNumber('Brake Steps')
POWER_STEPS = property.getNumber('Power Steps')
BRAKE = {0, 4, 8, 12, 16, 20, 24, 31}
POWER = {0, 1, 2, 3, 4}

min, max = math.min, math.max
function b2i(f)
	return f and 1 or 0
end

function onTick()
	door_interlock = input.getBool(1)
	cut_dynamic_brake = input.getBool(2)
	emergency_run = input.getBool(3)
	atc_brake = input.getBool(4)
	atc_eb = input.getBool(5)
	m = input.getNumber(1)
	reverser = input.getNumber(2)
	direction_switch = input.getNumber(3)
	tasc_brake = input.getNumber(4)
	ato_power = input.getNumber(5)

	eb = m == 0
	brake_step = max(BRAKE_STEPS + 1 - m, 0)
	power_step = max(m - BRAKE_STEPS - 1, 0)
	if m == BRAKE_STEPS + 1 then
		power_step = max(power_step, ato_power)
	end
	if atc_eb or atc_brake then
		brake_step = BRAKE_STEPS
		power_step = 0
		if atc_eb then
			brake_step = BRAKE_STEPS + 1
			eb = true
		end
	end
	if not door_interlock or tasc_brake > 0 then
		power_step = 0
	end

	nits_brake = max(BRAKE[brake_step + 1] or 31, tasc_brake)
	nits_power = POWER[power_step + 1] or 0

	brake_indicator = brake_step
	power_indicator = power_step
	for i, v in ipairs(BRAKE) do
		if tasc_brake <= v then
			brake_indicator = max(brake_indicator, i - 1)
			break
		end
	end

	output.setBool(1, eb)
	output.setBool(2, emergency_run)
	output.setBool(3, m == 0)
	output.setNumber(1, nits_brake)
	output.setNumber(2, nits_power)
	output.setNumber(3, reverser)
	output.setNumber(4, b2i(not cut_dynamic_brake) << 2)
	output.setNumber(5, direction_switch)
	output.setNumber(6, brake_indicator)
	output.setNumber(7, power_indicator)
	output.setNumber(8, BRAKE_STEPS + 1 - m)
	output.setNumber(9, m - BRAKE_STEPS - 1)
end
