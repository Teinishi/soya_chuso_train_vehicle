-- @if inline_param_text == 'left'
flip = property.getBool('Direction')
-- @else
flip = not property.getBool('Direction')
-- @end

SECTIONS = {
	{1, 3, {255, 82, 7}, {48, 38, 4}},
	{3, 9, {7, 19, 58}, {0, 7, 32}},
	{9, 12, {13, 95, 46}, {7, 40, 27}}
}
SECTION_GRAY = {SECTIONS[1][1], SECTIONS[#SECTIONS][2], {95, 95, 95}, {21, 21, 21}}

abs = math.abs
function sgn(x)
	return x > 0 and 1 or x < 0 and -1 or 0
end
gN = input.getNumber

page, front_sta, arrow_pos, stop_pattern, dir, range1_i, range1_o, range2_i, range2_o = 0, 0, 0, 0, 0, 0, 0, 0, 0

function onTick()
	page, front_sta, arrow_pos, stop_pattern, range1_i, range1_o = gN(6), gN(7), gN(8), gN(9) // 1, gN(10), gN(11)
	dir, arrow_pos = arrow_pos > 0 and 1 or arrow_pos < 0 and -1 or 0, abs(arrow_pos)
	range2_i = dir > 0 and arrow_pos or range1_i
	range2_o = dir < 0 and arrow_pos or range1_o
end

colors = {
	white = {200, 200, 200},
	arrow = {255, 0, 28}
}

S = screen
function R(x, y, w, h)
	if flip then
		x, w = 96 - x, -w
	end
	S.drawRectF(x, y, w, h)
end
function Ra(x1, y1, x2, y2)
	R(x1, y1, x2 - x1, y2 - y1)
end
function C(c)
	S.setColor(c[1], c[2], c[3])
end

function get_x(i)
	i = i - front_sta - 1
	return -16 * i
end

function draw_route_line(sec, ex_i, ex_o)
	x1, x2 = get_x(sec[1]) + (ex_i and 6 or 0), get_x(sec[2]) - (ex_o and 6 or 0)
	C(sec[3])
	Ra(x1, 53, x2, 55)
	C(sec[4])
	Ra(x1, 55, x2, 58)
end

function draw_arrow(i, f)
	f = f and -1 or 1
	x0 = get_x(i)
	function r(x, y, w, h)
		R(x0 + f * x, y, f * w, h)
	end
	C(colors.white)
	r(-2, 53, 5, 5)
	r(-3, 54, 1, 3)
	C(colors.arrow)
	for j = 0, 3 do
		r(1 - j, 52 + j, 1, 7 - 2 * j)
	end
end

function onDraw()
	if page ~= 6 then return end

	draw_route_line(SECTION_GRAY, true, true)
	f = false
	for _, sec in ipairs(SECTIONS) do
		sec_i = math.max(sec[1], range2_i)
		sec_o = math.min(sec[2], range2_o)
		if sec[2] > range1_i and sec[1] < range1_o and sec_i <= sec_o then
			draw_route_line({sec_i, sec_o, sec[3], sec[4]}, not f and dir <= 0, dir >= 0)
			f = true
		else
			f = false
		end
	end

	C(colors.white)
	for i = front_sta - 4, front_sta do
		if range2_i <= i and i <= range2_o then
			if stop_pattern >> i - 1 & 1 ~= 0 then
				R(get_x(i) - 3, 54, 6, 3)
			else
				for j = -1, 1 do
					R(get_x(i) + (dir > 0 and abs(j) - 1 or -abs(j) + 2), 55 + j, 2 * dir, 1)
				end
			end
		end
	end

	C(colors.white)
	for i = -3, 3 do
		if dir > 0 then
			R(0, 55 + i, 4 + abs(i), 1)
		else
			R(96, 55 + i, -4 - abs(i), 1)
		end
	end

	if arrow_pos ~= 0 then
		draw_arrow(arrow_pos, dir < 0)
	end

	C(colors.white)
	Ra(0, 52, 3, 59)
	Ra(96, 52, 93, 59)
end
