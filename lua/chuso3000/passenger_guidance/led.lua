OUT_OF_SRV=1
srv_types={5,6,7,8,9}
link_tbl={{},{2},{1},{3},{2},{5,6},{},{5,6},{3,4},{},{3,4},{7},{6},{8,9},{7},{},{7},{10},{9},{11},{10},{12},{11},{13,14},{12},{},{12},{15},{14},{17},nil,nil,{15},{},nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,{35,36},{},{35,36},{},nil,nil,{37},{},{37},{},{40,41},{},nil,nil,nil,nil,{42},{},{42},{},{44,45,46},{},nil,nil,{},{32,33},{},{},{},{},{},{}}
stop_type_tbl={{5,6,7,8,9},{5,6,7},{5,6,7,8,9},{5,6,7,8,9},{5,6,7,8,9},{5},{5,6,7},{5,6,7},{5,6},{5},{5,6,9},{5,6,7,8,9},{5,6,7,8,9},{5},{5,6,7},nil,{5,6,7,8,9},nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,{5,6,7,8,9},{5,6,7,8,9},{5,6,7,8,9},{5,6,7,8,9},{5},nil,{5},{5},{5,6,7,8,9}}
not4srv={[5]=1,[8]=1,[13]=1}
idx_tbl={1,2,3,3,3,4,5,5,6,7,8,9,9,10,11,nil,12,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,1,1,nil,2,2,3,nil,nil,4,4,5,nil,5,6,6,7}

function led_sta_id(id)
	if id < 32 then
		return id
	end
	return (id - 32) % 4 < 2 and 32 or 12
end

function sel(f, a, b)
	return f and a or b
end

function includes(arr, v)
	for _, w in ipairs(arr) do
		if v == w then
			return true
		end
	end
end

function find_rte(from,to,inb)
	if not link_tbl[from] then return end
	tr,q={[from]=from},{from}
	for _=1,100 do
		for _,v in ipairs(link_tbl[q[1]*2-(inb and 1 or 0)] or {}) do
			if not tr[v] then
				table.insert(q,v)
				tr[v]=q[1]
			end
		end
		table.remove(q,1)
		if #q==0 then break end
	end
	if tr[to] then
		rte={to,inb=inb,outb=not inb}
		for _=1,100 do
			if to==from then break end
			table.insert(rte,1,tr[to])
			to=tr[to]
		end
		return rte
	end
end

sB, sN = output.setBool, output.setNumber
function gI(c)
	return math.floor(input.getNumber(c))
end

prev_op_code_a, prev_op_code_c, prev_loc_code = 0, 0, 0
function onTick()
	op_num = gI(1)
	op_code_a, op_code_c, loc_code = gI(3), gI(5), gI(6)
	updated = op_code_a ~= prev_op_code_a or op_code_c ~= prev_op_code_c or loc_code ~= prev_loc_code
	prev_op_code_a, prev_op_code_c, prev_loc_code = op_code_a, op_code_c, loc_code

	a_train_type, a_origin, a_dest = op_code_a >> 12 & 15, op_code_a >> 6 & 63, op_code_a & 63
	c_train_type, c_auto, c_dest = op_code_c >> 12 & 15, op_code_c >> 6 & 63 == 0, op_code_c & 63
	is_inbound = loc_code >> 15 & 1 ~= 0
	sts, id1, id2 = loc_code >> 12 & 3, loc_code >> 6 & 63, loc_code & 63
	is_jsms = id1 >= 32
	if sts == 0 then
		id1, id2 = 0, 0
	end

	led_train_type = c_train_type
	if a_train_type == c_train_type and a_dest == c_dest and (not4srv[a_dest] and (id1 == a_dest or id2 == a_dest)) and includes(srv_types, led_train_type) then
		led_train_type = OUT_OF_SRV
	end

	led_next_stop = sel(c_auto and not not4srv[id2] and (sts == 1 or sts == 3), id2, 0)

	stop_pattern, led_stop_pattern, lcd_stop_pattern = 0, 0, 0
	if updated then
		rte = find_rte(a_origin, a_dest, is_inbound) or {}
		for _, v in ipairs(rte) do
			if includes(stop_type_tbl[v], a_train_type) then
				stop_pattern = stop_pattern | 1 << (v - 1)
			end
		end

		led_stop_pattern = ~(1 << id1 - 1) & stop_pattern

		for i, v in ipairs(idx_tbl) do
			if stop_pattern >> i - 1 & 1 ~= 0 then
				lcd_stop_pattern = lcd_stop_pattern | 1 << v- 1
			end
		end
	end

	if not is_jsms and led_next_stop ~= 0 and idx_tbl[id1] == idx_tbl[a_origin] then
		led_next_stop = 0
		led_stop_pattern = sel(is_inbound, -led_stop_pattern, led_stop_pattern)
	else
		led_stop_pattern = 0
	end

	sB(1, is_inbound)
	sN(1, led_train_type)
	sN(2, led_sta_id(c_dest))
	sN(3, led_sta_id(led_next_stop))
	sN(4, led_stop_pattern)
	sN(5, op_num)
	sB(32, updated)
	sN(32, lcd_stop_pattern)
end
