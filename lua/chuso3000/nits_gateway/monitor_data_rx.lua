CH_MAP = {[0x43] = 1, [0x4a] = 2, [0x4b] = 3}

I, O = input, output
gN, sB, sN = I.getNumber, O.setBool, O.setNumber

function gCmn(s, w, v)
	v = 0
	for i = 0, w - 1 do
		v = v | (I.getBool(1 + s + i) and 1 or 0) << i
	end
	return v
end
function gI(c)
	return math.floor(gN(c))
end
function gC(c)
	return ('I3B'):unpack(('f'):pack(gN(c)))
end

function bit_at(n, i)
	return n >> i & 1 ~= 0
end

function swap_bits(n, a, b, w, k)
	if k then
		return n
	end
	m = (1 << w) - 1
	t = n >> a & m
	n = n ~ (n & m << a) | (n >> b & m) << a
	n = n ~ (n & m << b) | t << b
	return n
end

function onTick()
	i32 = gI(32)
	reset_i = (i32 & 31) + 1
	ext_mode = bit_at(i32, 5)
	cars_f, cars_b = gCmn(0, 4), gCmn(5, 4)

	for i = 0, 15 do
		update_data_1 = false
		val, write_ch = 0, nil

		is_self = i == cars_f
		is_b = i > cars_f
		input_ch = i + 1
		if is_self then
			input_ch = 16
		elseif is_b then
			input_ch = 31 - cars_f - cars_b + i
		end

		cmd_type = 0
		if input_ch <= 31 then
			val, cmd_type = gC(input_ch)
		end
		update_data_1 = 0x41 <= cmd_type and cmd_type <= 0x43
		if cmd_type >= 0x48 and not ext_mode then
			cmd_type, val = 0, 0
		end

		if not is_b then
			function sw(a, b, w)
				val = swap_bits(val, a, b, w)
			end
			if 0x41 <= cmd_type and cmd_type <= 0x43 then
				sw(19, 20, 1)
			elseif cmd_type == 0x4a then
				sw(0, 1, 1)
				sw(2, 3, 1)
				sw(4, 7, 3)
				sw(10, 12, 2)
			elseif cmd_type == 0x4b then
				sw(1, 7, 6)
				sw(13, 15, 2)
				val = val ~ val & 1
			end
		end

		write_ch = CH_MAP[cmd_type]

		sB(2 * i + 1, update_data_1)
		sN(2 * i + 1, val)
		sN(2 * i + 2, write_ch or 32)
	end
end
