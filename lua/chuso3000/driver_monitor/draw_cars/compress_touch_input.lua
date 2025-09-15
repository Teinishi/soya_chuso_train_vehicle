function b2i(f)return f and 1 or 0 end
function encode(n)
    local x=('f'):unpack(('I3B'):pack(n&16777215,66+128*(n>>29&1)+(n>>24&31)))
    return x
end

gB=input.getBool
function gI(c)return math.floor(input.getNumber(c))end

function onTick()
	pressed1,pressed2=gB(1),gB(2)
	touch1x,touch1y,touch2x,touch2y=gI(3),gI(4),gI(5),gI(6)
	output.setNumber(1,encode(b2i(pressed1)<<29|(touch1x&127)<<22|(touch1y&127)<<15|b2i(pressed2)<<14|(touch2x&127)<<7|(touch2y&127)))
end
