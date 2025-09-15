SRV_BIT_POS_MAP={18,17,19}
SRV_OUT_CH_MAP={9,7,11}

M=math
function decode(x)
	local b,a=('I3B'):unpack(('f'):pack(x))
	local v=66<=a and a<=126 or 194<=a and a<=254
	return v and(a-66>>2&32|a-66&31)<<24|b or 0
end
function sel(f,a,b)return f and a or b end
function bit_at(n,i)return n>>i&1~=0 end
I,O=input,output
gB,gN,sB,sN=I.getBool,I.getNumber,O.setBool,O.setNumber
function gI(c)return M.floor(gN(c))end

show,cars_total,eqp,srv,draw_x=false,0,0,0,0
data={}
total_width=0
cars_x={}
eqp_btns,srv_btns={{}},{{},{},{}}
function onTick()
	show,ext_mode=gB(1),gB(2)
	n29,n30=gI(29),gI(30)
	cars_f,cars_b=n29>>4&15,n29&15
	cars_total=cars_f+cars_b+1
	eqp,srv=n30>>8&15,n30>>3&15
	offset_x=gI(31)
	touches=decode(gN(28))
	for i=0,7 do
		data[i+1]={gI(1+3*i),gI(2+3*i),gI(3+3*i)}
	end

	function is_touched(x,y,w,h)
		t1x,t1y=touches>>22&127,touches>>15&127
		t2x,t2y=touches>>7&127,touches&127
		return touches>>29&1~=0 and x<=t1x and t1x<x+w and y<=t1y and t1y<y+h or touches>>14&1~=0 and x<=t2x and t2x<x+w and y<=t2y and t2y<y+h
	end

	function add_btn(x,y,d,lst)
		t=is_touched(x,y,5,5)
		table.insert(lst,{x,y,d,t})
		return t
	end

	interval=M.min(M.floor(76/cars_total+0.5),20)
	car_width=interval+(interval>12 and -1 or 1)
	total_width=interval*(cars_total-1)+car_width
	draw_x=offset_x+(96-total_width)//2

	cmd_tgt,cmd_out_ch=nil,0

	eqp_btns,srv_btns={{}},{{},{},{}}
	for i=1,cars_total do
		rel_i=cars_f+1-i
		cars_x[i]=draw_x+interval*(i-1)

		if ext_mode and data[i]~=nil then
			data_0x4a,data_0x4b=data[i][2],data[i][3]
			if eqp==1 then
				pnt_f=data_0x4a>>12&3
				pnt_b=data_0x4a>>10&3
				pnt_fl=data_0x4b>>15&1~=0
				pnt_bl=data_0x4b>>13&1~=0
				if pnt_f~=0 and add_btn(cars_x[i]+car_width//6-1,11,pnt_fl,eqp_btns[1]) then
					cmd_tgt,cmd_out_ch=rel_i,sel(pnt_fl,5,6)
				end
				if pnt_b~=0 and add_btn(cars_x[i]+car_width-car_width//6-4,11,pnt_bl,eqp_btns[1]) then
					cmd_tgt,cmd_out_ch=rel_i,sel(pnt_bl,3,4)
				end
			elseif srv_btns[srv] then
				srv_stat=bit_at(data_0x4b,SRV_BIT_POS_MAP[srv] or 24)
				if add_btn(cars_x[i]+car_width//2-2,26,srv_stat,srv_btns[srv]) then
					cmd_tgt,cmd_out_ch=rel_i,(SRV_OUT_CH_MAP[srv] or 0)+sel(srv_stat,0,1)
				end
			end
		end
	end

	sB(1,cmd_tgt~=nil and cmd_tgt>0)
	sB(2,cmd_tgt~=nil and cmd_tgt<=0)
	sN(1,M.abs(cmd_tgt or 0))
	for i=3,12 do
		sB(i,cmd_out_ch==i)
	end
end

clr={
	black={0,0,0},
	white={200,200,200},
	bluegray={30,36,44},
	btn={8,17,27},
	p_btn={135,59,6},
	red={200,0,0},
	green={0,200,0}
}
function C(c)screen.setColor(c[1],c[2],c[3])end

R=screen.drawRectF
function H(x,y,w)R(x,y,w,1)end
function V(x,y,h)R(x,y,1,h)end
function D(x,y)H(x,y,1)end

function draw_btn(x,y,f,t,c,flip)
	C(sel(t,clr.p_btn,clr.btn))
	R(x,y,5,5)
	C(c)
	if flip then V(x+2,y-3,3)
	else V(x+2,y+5,3)end
	if t then C(clr.black)end
	if f then D(x+1,y+2)D(x+2,y+1)D(x+2,y+3)D(x+3,y+2)
	else D(x+1,y+1)D(x+1,y+3)D(x+2,y+2)D(x+3,y+1)D(x+3,y+3)end
end

function onDraw()
	if not show then return end
	if eqp_btns[eqp]~=nil then
		C(clr.bluegray)
		H(draw_x,13,total_width)
		for _,v in ipairs(eqp_btns[eqp])do
			draw_btn(v[1],v[2],not v[3],v[4],sel(v[3],clr.red,clr.white))
		end
	elseif srv~=0 then
		C(clr.bluegray)
		H(draw_x,28,total_width)
		for _,v in ipairs(srv_btns[srv])do
			draw_btn(v[1],v[2],v[3],v[4],sel(v[3],clr.green,clr.white),true)
		end
	end
end
