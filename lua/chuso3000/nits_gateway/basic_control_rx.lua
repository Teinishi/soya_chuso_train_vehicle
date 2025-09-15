ACCEPT_MODE_ID = {[0x240001] = true}

sB, sN = output.setBool, output.setNumber

function I(c)
	return ('I3B'):unpack(('f'):pack(input.getNumber(c)))
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

function b2i(f)
	return f and 1 or 0
end

function onTick()
	cmn = I(32)
	cars_f = cmn & 15
	cars_b = cmn >> 5 & 15
	cancel_mode_change, reject_mode_change = false, false

	data_1, data_2, data_0x41, data_0x42 = nil, nil, nil, nil

	for i = 1, 31 do
		ns = i > 16
		function add_data_1(v)
			data_1 = (data_1 or 0) | (ns and v or swap_bits(v, 0, 1, 1))
		end
		function add_data_2(v)
			data_2 = (data_2 or 0) | v
		end
		function add_data_0x41(v)
			data_0x41 = ns and v or swap_bits(v, 8, 9, 1)
		end
		function add_data_0x42(v)
			data_0x42 = (data_0x42 or 0) | (ns and v or swap_bits(v, 0, 2, 2))
		end

		cmd_body, cmd_type = I(i)
		is_0x41 = cmd_type == 0x41
		is_0x42 = cmd_type == 0x42
		is_0x43 = cmd_type == 0x43

		if is_0x41 or is_0x42 or is_0x43 then add_data_1(cmd_body >> 19) end
		if is_0x41 or is_0x42 then add_data_2(cmd_body >> 13 & 63) end
		if is_0x41 then add_data_0x41(cmd_body & 8191) end
		if is_0x42 then add_data_0x42(cmd_body & 8191) end

		if cmd_type == 0x47 then
			if cmd_body == 0 then
				cancel_mode_change = true
			elseif not ACCEPT_MODE_ID[cmd_body] then
				reject_mode_change = true
			end
		end
	end

	sB(1, cmn >> 10 & 1 ~= 0)
	sB(2, cmn >> 13 & 1 ~= 0)

	sB(17, data_1 ~= nil)
	sN(17, data_1 or 0)
	sB(18, data_2 ~= nil)
	sN(18, data_2 or 0)
	sB(19, data_0x41 ~= nil)
	sN(19, data_0x41 or 0)
	sB(20, data_0x42 ~= nil)
	sN(20, data_0x42 or 0)

	sB(31, cancel_mode_change)
	sB(32, reject_mode_change)
	sN(31, cars_f)
	sN(32, cars_b)
end
