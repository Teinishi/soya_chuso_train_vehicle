is_outbound = property.getBool('Direction')

function clamp(x, a, b)
	return math.min(math.max(x, a), b)
end

function bit_ones(n)
	return (1 << n) - 1
end

gN = input.getNumber
function onTick()
	loc_code = math.floor(gN(6))
	cars_f, cars_b = gN(31), gN(32)
	doorcut_o, doorcut_i = gN(10), gN(11)
	if not is_outbound then
		doorcut_o, doorcut_i = doorcut_i, doorcut_o
	end

	sts, id1, id2 = loc_code >> 12 & 3, loc_code >> 6 & 63, loc_code & 63
	pass_next = sts == 2 and id1 ~= id2

	door_bit = 0
	for i = 0, cars_f + cars_b do
		j = cars_f + cars_b - i
		door_bit = door_bit << 3 | bit_ones(3 - clamp(doorcut_o - 6 * i, 0, 3)) ~ bit_ones(clamp(doorcut_i - 6 * j, 0, 3))
	end

	output.setBool(1, pass_next)
	output.setNumber(3, cars_f + cars_b + 1)
	output.setNumber(4, door_bit)
end
