SPEED = 0.33

is_left = property.getBool('Side')
open_if_mode1 = property.getBool('Open if mode 1')
door_no, door_count = property.getNumber('Door No.'), property.getNumber('Door Count')

function clamp(x, a, b)
	return math.min(math.max(x, a), b)
end

function onTick()
	open = input.getBool(is_left and 9 or 11)
	close = input.getBool(is_left and 10 or 12)
	door_mode = input.getNumber(9)
	doorcut_f = input.getNumber(12)
	doorcut_b = input.getNumber(13)
	d = input.getNumber(32)

	set_on, set_off = false, close
	if open then
		if (open_if_mode1 or door_mode == 0) and (doorcut_f < door_no and door_no <= door_count - doorcut_b) then
			set_on = true
		else
			set_off = true
		end
	end

	open_speed = clamp(SPEED - 2 * (d - 1.1), 0.1, SPEED)
	close_speed = clamp(0.75 * (d - 0.1), 0.1, SPEED)

	output.setBool(1, set_on)
	output.setBool(2, set_off)
	output.setNumber(1, open_speed)
	output.setNumber(2, -close_speed)
end
