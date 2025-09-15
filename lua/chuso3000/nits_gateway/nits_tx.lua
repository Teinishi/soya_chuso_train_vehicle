CMD_CYCLE={0x41,0x43,0x4b}
REQ_MODE_ID=0x240001

M,P,I,U=math,property,input,table.unpack
function round(x)return M.floor(x+0.5)end
function clamp(x,a,b)return M.min(M.max(x,a),b)end
function pI(l)return M.floor(P.getNumber(l))end
gN,gB,sN=I.getNumber,I.getBool,output.setNumber
function gI(c)return M.floor(gN(c))end
function gNf(c,_n)
	_n=('I4'):unpack(('f'):pack(gN(c)))
	return _n
end
function gNB(c,_v,_n)
	_v,_n={},gNf(c)
	for i=0,31 do _v[1+i]=_n>>i&1~=0 end
	return _v
end

function sel(f,a,b)return f and a or b end
function bitarr(arr,l,rev,_v)
	for i=1,l do _v=(_v or 0)|sel(arr[i],1,0)<<sel(rev,i-1,l-i)end
	return _v
end
function filter(arr,fn,_)
	_={}
	for i,v in ipairs(arr) do
		if fn(v)then table.insert(_,v)end
	end
	return _
end
function swap(n,a,b,w)
	m=(1<<w)-1
	t=n>>a&m
	n=n~(n&m<<a)|(n>>b&m)<<a
	n=n~(n&m<<b)|t<<b
	return n
end
function encode(c,p,_)
	_=('f'):unpack(('I3B'):pack(p,c))
	return _
end

doors_l,doors_r=pI('Left side doors'),pI('Right side doors')
to_f_0x4a=bitarr({P.getBool('Double Decker')},1)<<22|pI('Car No.')<<18|pI('Front Pantograph')<<12|pI('Rear Pantograph')<<10|doors_l<<7|doors_r<<4|pI('Powered Axle')<<2|pI('Cab')

function onTick()
	eqp_uni_f,eqp_uni_b,write_0x4c,swap_0x4c=gB(6),gB(7),gB(8),gB(9)
	send_0x4a,deny_mode_chg,req_mode_chg,control,ext_mode=gB(28),gB(29),gB(30),gB(31),gB(32)

	brk_cmd,pwr_cmd,rvs,dyn_brk=gI(1),gI(2),gI(3),gI(4)
	brk_val,pwr_val=gN(5),gN(6)
	eqp_stat,eqp_brd,door_mode,doorcut_f,doorcut_b,addr1,addr2,mem_val=gNB(7),gNf(8),gI(9),gI(10),gI(11),gI(12),gI(13),gI(14)

	door_stat_l,door_stat_r={U(eqp_stat,1,doors_l)},{U(eqp_stat,7,6+doors_r)}
	in_data_2,in_data_0x42=eqp_brd&63,eqp_brd>>6&4095
	door_open=in_data_0x42>>2&2|in_data_0x42>>1&1
	door_upd=(eqp_brd>>18&1)<<18|(eqp_brd>>19&1)<<10|(eqp_brd>>20&1)<<2
	eqp_uni_data=gNf(15)>>2&1023

	eqp_uni_car_count=gI(16)
	cycle_i=gI(32)

	cycle=filter(CMD_CYCLE,function(m)
		if m==0x41 then return control
		elseif m>=0x48 then return ext_mode end
		return true
	end)

	door_open_l,door_open_r=false,false
	for i=1,doors_l do
		door_open_l=door_open_l or door_stat_l[i]
	end
	for i=1,doors_r do
		door_open_r=door_open_r or door_stat_r[i]
	end

	data_1=bitarr({gB(1),gB(2),gB(3),door_open_l,door_open_r},5)<<19
	data_2=data_1|in_data_2<<13

	cmd_type=nil
	if #cycle>0 then cmd_type=cycle[cycle_i%#cycle+1]end
	to_f,to_b=0,0

	if deny_mode_chg then
		cmd_type=0x47
	elseif req_mode_chg then
		cmd_type=0x47
		to_f=REQ_MODE_ID
		to_b=REQ_MODE_ID
	elseif (door_open~=0 or door_upd~=0) and ext_mode then
		cmd_type=0x48
	elseif in_data_0x42~=0 or in_data_2~=0 and cmd_type~=0x41 then
		cmd_type=0x42
	elseif send_0x4a and ext_mode then
		cmd_type=0x4a
	elseif (eqp_uni_f or eqp_uni_b) and ext_mode then
		cmd_type=0x49
	elseif (write_0x4c or swap_0x4c) and ext_mode then
		cmd_type=0x4c
	end

	if cmd_type==0x41 then
		to_f=data_2|(dyn_brk&7)<<10|bitarr({rvs < 0,rvs > 0},2)<<8|(pwr_cmd&7)<<5|brk_cmd&31
		to_b=swap(swap(to_f,8,9,1),19,20,1)
	elseif cmd_type==0x42 then
		to_f=data_2|in_data_0x42
		to_b=swap(swap(to_f,0,2,2),19,20,1)
	elseif cmd_type==0x43 then
		to_f=data_1|(clamp(round(pwr_val),-512,511)&1023)<<9|clamp(round(brk_val/2),0,511)
		to_b=swap(to_f,19,20,1)
	elseif cmd_type==0x48 then
		to_f=door_upd|(door_mode&15)<<19|(doorcut_f&127)<<11|(doorcut_b&127)<<3|door_open
		to_b=swap(swap(to_f,2,10,8),0,1,1)
	elseif cmd_type==0x49 then
		to_f=bitarr({eqp_uni_b},1)<<23|(eqp_uni_car_count&15)<<19|eqp_uni_data
		to_b=swap(to_f~1<<23,0,2,2)
	elseif cmd_type==0x4a then
		to_f=to_f_0x4a
		to_b=swap(swap(swap(swap(to_f,0,1,1),2,3,1),4,7,3),10,12,2)
	elseif cmd_type==0x4b then
		to_f=bitarr({eqp_stat[21],eqp_stat[20],false,false,eqp_stat[19],eqp_stat[18],eqp_stat[17]},7)<<17|bitarr({U(eqp_stat,13,16)},4)<<13|bitarr(door_stat_l,doors_l)<<7|bitarr(door_stat_r,doors_r)<<1
		to_b=swap(swap(to_f|1,1,7,6),13,15,2)
	elseif cmd_type==0x4c then
		to_f=sel(swap_0x4c,1,0)<<23|(addr1&7)<<20|sel(swap_0x4c,addr2,mem_val)&0xFFFFF
		to_b=to_f
	end

	sN(1,sel(cmd_type,encode(cmd_type,to_b),0))
	sN(2,sel(cmd_type,encode(cmd_type,to_f),0))
	sN(3,cmd_type or 0)
end
