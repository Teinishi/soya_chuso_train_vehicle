prev = {}

function onTick()
	out = false
	for i = 1, 32 do
		b = input.getBool(i)
		out = out or b and not prev[i]
		prev[i] = b
	end
	output.setBool(1, out)
end
