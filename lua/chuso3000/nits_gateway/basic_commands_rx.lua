gB, sB, sN = input.getBool, output.setBool, output.setNumber
function gI(c)
	return math.floor(input.getNumber(c))
end

function bit_at(n, i)
	return n >> i & 1 ~= 0
end

function onTick()
	cars_f, cars_b = gI(31), gI(32)
	data_1 = 0
	for i = 1, cars_f + cars_b + 1 do
		data_1 = data_1 | gI(i) >> 19 & 31
	end
	data_2, data_0x41, data_0x42 = gI(18), gI(19), gI(20)

	sB(1, gB(1) or bit_at(data_1, 4))
	sB(2, gB(2))
	for i = 0, 3 do
		sB(3 + i, bit_at(data_1, i))
	end
	for i = 0, 5 do
		sB(7 + i, bit_at(data_2, i))
	end
	sN(1, data_0x41 & 31)
	sN(2, data_0x41 >> 5 & 7)
	sN(3, (data_0x41 >> 8 & 1) - (data_0x41 >> 9 & 1))
	sN(4, data_0x41 >> 10 & 7)
	for i = 0, 7 do
		sB(13 + i, bit_at(data_0x42, 4 + i))
	end
	for i = 21, 32 do
		sB(i, gB(i))
	end
	sN(31, cars_f)
	sN(32, cars_b)
end
