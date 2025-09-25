COMMAND_CYCLE = {0x41, 0x43, 0x4b}
REQUEST_MODE_ID = 0x240001

M, P, I, U = math, property, input, table.unpack

function round(x)
	return M.floor(x + 0.5)
end
function clamp(x, a, b)
	return M.min(M.max(x, a), b)
end

function pI(l)
	return M.floor(P.getNumber(l))
end

gN, gB, sN = I.getNumber, I.getBool, output.setNumber
function gI(c)
	return M.floor(gN(c))
end
function gNf(c, _n)
	-- 数値入力を32bit整数として取得
	_n = ('I4'):unpack(('f'):pack(gN(c)))
	return _n
end
function gNB(c, _v, _n)
	-- 数値入力を長さ32の bool 配列として取得
	_v, _n = {}, gNf(c)
	for i = 0, 31 do _v[1 + i] = _n>>i&1 ~= 0 end
	return _v
end

function sel(f, a, b)
	return f and a or b
end
function bitarr(arr, l, rev, _v)
	-- 長さ l の bool 配列 arr を2進整数に変換、rev が true なら反転
	for i = 1, l do
		_v = (_v or 0) | sel(arr[i], 1, 0)<<sel(rev, i - 1, l - i)
	end
	return _v
end
function filter(arr, fn, _)
	_ = {}
	for i, v in ipairs(arr) do
		if fn(v)then table.insert(_, v)end
	end
	return _
end
function swap(n, a, b, w)
	m = (1<<w) - 1
	t = n>>a&m
	n = n~(n&m<<a) | (n>>b&m)<<a
	n = n~(n&m<<b) | t<<b
	return n
end
function encode(c, p, _)
	_ = ('f'):unpack(('I3B'):pack(p, c))
	return _
end

ndoors_left, ndoors_right = pI('Left side doors'), pI('Right side doors')
payload_0x4a_front = bitarr({P.getBool('Double Decker')}, 1)<<22
	| pI('Front Pantograph')<<12
	| pI('Rear Pantograph')<<10
	| ndoors_left<<7
	| ndoors_right<<4
	| pI('Powered Axle')<<2
	| pI('Cab')
payload_0x4a_back = swap(payload_0x4a_front, 0, 1, 1)
payload_0x4a_back = swap(payload_0x4a_back, 2, 3, 1)
payload_0x4a_back = swap(payload_0x4a_back, 4, 7, 3)
payload_0x4a_back = swap(payload_0x4a_back, 10, 12, 2)

function onTick()
	sos_button = gB(3)
	equipment_unicast_front, equipment_unicast_back, write_0x4c, swap_0x4c = gB(6), gB(7), gB(8), gB(9)
	send_0x4a, deny_mode_change, request_mode_change, control, extension_mode = gB(28), gB(29), gB(30), gB(31), gB(32)

	brake_command, power_command, reverser, dynamic_brake = gI(1), gI(2), gI(3), gI(4)
	brake_value, power_value = gN(5), gN(6)
	equipment_status, equipment_broadcast, door_mode, doorcut_front, doorcut_back, addr1, addr2, memory_value = gNB(7), gNf(8), gI(9), gI(10), gI(11), gI(12), gI(13), gI(14)

	door_status_left, door_status_right = {U(equipment_status, 1, ndoors_left)}, {U(equipment_status, 7, 6 + ndoors_right)}
	data_2_input, data_0x42_input = equipment_broadcast&63, equipment_broadcast>>6&4095
	door_open = data_0x42_input>>2&2 | data_0x42_input>>1&1
	door_update = (equipment_broadcast>>18&1)<<18 | (equipment_broadcast>>19&1)<<10 | (equipment_broadcast>>20&1)<<2
	equipment_unicast_data = gNf(15)>>2&1023

	equipment_unicast_car_count = gI(16)
	doorcut_sf, doorcut_sb = gI(17), gI(18)
	doorcut_status = M.max(ndoors_left, ndoors_right) - doorcut_sf - doorcut_sb <= 0
	car_number = clamp(gI(19), 0, 15)
	cycle_i = gI(32)

	cycle = filter(COMMAND_CYCLE, function(m)
		if m == 0x41 then return control
		elseif m >= 0x48 then return extension_mode end
		return true
	end)

	door_open_left, door_open_right = false, false
	for i = 1, ndoors_left do
		if door_status_left[i] then
			door_open_left = true
			break
		end
	end
	for i = 1, ndoors_right do
		if door_status_right[i] then
			door_open_right = true
			break
		end
	end

	data_1 = bitarr({gB(1), gB(2), sos_button, door_open_left, door_open_right}, 5)<<19
	data_2 = data_1 | data_2_input<<13

	command_type = nil
	if #cycle > 0 then command_type = cycle[cycle_i % #cycle + 1]end
	to_front, to_back = 0, 0

	if deny_mode_change then
		command_type = 0x47
	elseif request_mode_change then
		command_type = 0x47
		to_front = REQUEST_MODE_ID
		to_back = REQUEST_MODE_ID
	elseif (door_open ~= 0 or door_update ~= 0) and extension_mode then
		command_type = 0x48
	elseif data_0x42_input ~= 0 or data_2_input ~= 0 and command_type ~= 0x41 then
		command_type = 0x42
	elseif send_0x4a and extension_mode then
		command_type = 0x4a
	elseif (equipment_unicast_front or equipment_unicast_back) and extension_mode then
		command_type = 0x49
	elseif (write_0x4c or swap_0x4c) and extension_mode then
		command_type = 0x4c
	end

	if command_type == 0x41 then
		to_front = data_2 | (dynamic_brake&7)<<10 | bitarr({reverser < 0, reverser > 0}, 2)<<8 | (power_command&7)<<5 | brake_command&31
		to_back = swap(swap(to_front, 8, 9, 1), 19, 20, 1)
	elseif command_type == 0x42 then
		to_front = data_2 | data_0x42_input
		to_back = swap(swap(to_front, 0, 2, 2), 19, 20, 1)
	elseif command_type == 0x43 then
		to_front = data_1 | (clamp(round(power_value), -512, 511)&1023)<<9 | clamp(round(brake_value/2), 0, 511)
		to_back = swap(to_front, 19, 20, 1)
	elseif command_type == 0x48 then
		to_front = door_update | (door_mode&15)<<19 | (doorcut_front&127)<<11 | (doorcut_back&127)<<3 | door_open
		to_back = swap(swap(to_front, 2, 10, 8), 0, 1, 1)
	elseif command_type == 0x49 then
		to_front = bitarr({equipment_unicast_back}, 1)<<23 | (equipment_unicast_car_count&15)<<19 | equipment_unicast_data
		to_back = swap(to_front~1<<23, 0, 2, 2)
	elseif command_type == 0x4a then
		to_front = payload_0x4a_front | car_number<<18
		to_back = payload_0x4a_back | car_number<<18
	elseif command_type == 0x4b then
		to_front = bitarr({equipment_status[21], equipment_status[20], sos_button, doorcut_status, equipment_status[19], equipment_status[18], equipment_status[17]}, 7)<<17
			| bitarr({U(equipment_status, 13, 16)}, 4)<<13
			| bitarr(door_status_left, ndoors_left)<<7
			| bitarr(door_status_right, ndoors_right)<<1
		to_back = swap(swap(to_front | 1, 1, 7, 6), 13, 15, 2)
	elseif command_type == 0x4c then
		to_front = sel(swap_0x4c, 1, 0)<<23 | (addr1&7)<<20 | sel(swap_0x4c, addr2, memory_value)&0xFFFFF
		to_back = to_front
	end

	sN(1, sel(command_type, encode(command_type, to_back), 0))
	sN(2, sel(command_type, encode(command_type, to_front), 0))
	sN(3, command_type or 0)
end
