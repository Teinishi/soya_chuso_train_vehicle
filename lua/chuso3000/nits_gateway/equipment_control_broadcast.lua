function gI(c)
	return math.floor(input.getNumber(c))
end

function onTick()
	addr1, addr2, val = nil, nil, nil
	for i = 0, 7 do
		if input.getBool(1 + i) then
			addr1 = i
			val = gI(1 + i)
			break
		end
	end
	if input.getBool(9) then
		n9 = gI(9)
		addr1, addr2 = n9 >> 3 & 7, n9 & 7
	end
	output.setBool(1, addr1 ~= nil)
	output.setBool(2, addr2 ~= nil)
	output.setNumber(1, addr1 or 0)
	output.setNumber(2, addr2 or 0)
	output.setNumber(3, val or 0)
end
