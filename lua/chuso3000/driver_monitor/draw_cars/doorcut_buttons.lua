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

show,doorcut_f,doorcut_b,cars_total,door_sel,draw_x,car_width=false,0,0,0,false,0,0
total_width=0
cars_x={}
door_btns={}
function onTick()
	show,ext_mode=gB(1),gB(2)
	n29,n30=gI(29),gI(30)
	doorcut_f,doorcut_b,cars_f,cars_b=n29>>14&15,n29>>10&15,n29>>4&15,n29&15
	cars_total=cars_f+cars_b+1
	door_sel=n30>>7&1~=0
	offset_x=gI(31)
	touches=decode(gN(28))

	function is_touched(x,y,w,h)
		t1x,t1y=touches>>22&127,touches>>15&127
		t2x,t2y=touches>>7&127,touches&127
		return touches>>29&1~=0 and x<=t1x and t1x<x+w and y<=t1y and t1y<y+h or touches>>14&1~=0 and x<=t2x and t2x<x+w and y<=t2y and t2y<y+h
	end

	function add_btn(x,y,d,lst)
		t=is_touched(x,y,5,5)
		table.insert(lst,{x,y,t,d})
		return t
	end

	interval=M.min(M.floor(76/cars_total+0.5),20)
	car_width=interval+(interval>12 and -1 or 1)
	total_width=interval*(cars_total-1)+car_width
	draw_x=offset_x+(96-total_width)//2

	set_doorcut_f,set_doorcut_b=nil,nil

	door_btns={}
	for i=1,cars_total do
		cars_x[i]=draw_x+interval*(i-1)

		if ext_mode and door_sel then
			if i>doorcut_f+1 and add_btn(cars_x[i],13,sel(cars_total-doorcut_b<i,5,4),door_btns) then
				set_doorcut_b=cars_total-i+1
			end
			if i<cars_total-doorcut_b and add_btn(cars_x[i]+car_width-5,13,sel(i<=doorcut_f,3,2),door_btns) then
				set_doorcut_f=i
			end
		end
	end
	if door_sel then
		if add_btn(cars_x[1]-6,13,sel(doorcut_f>0,1,0),door_btns) then
			set_doorcut_f=0
		end
		if add_btn(cars_x[cars_total]+car_width+1,13,sel(doorcut_b>0,1,0),door_btns) then
			set_doorcut_b=0
		end
	end

	sB(1,set_doorcut_f~=nil)
	sB(2,set_doorcut_b~=nil)
	sN(1,(set_doorcut_f or 0)*6)
	sN(2,(set_doorcut_b or 0)*6)
end

clr={
	black={0,0,0},
	white={200,200,200},
	btn={8,17,27},
	p_btn={135,59,6},
	red={200,0,0}
}
function C(c)screen.setColor(c[1],c[2],c[3])end

R=screen.drawRectF
function H(x,y,w)R(x,y,w,1)end
function V(x,y,h)R(x,y,1,h)end
function D(x,y)H(x,y,1)end

function draw_btn_door(x,y,t,d)
	C(sel(t,clr.p_btn,clr.btn))
	R(x,y,5,5)
	C(sel(t,clr.black,sel(d%2~=0,clr.red,clr.white)))
	if d<=1 then
		D(x+1,y+1)D(x+1,y+3)D(x+2,y+2)D(x+3,y+1)D(x+3,y+3)
	else
		V(d>=4 and x+1 or x+3,y+1,3)H(x+1,y+2,3)
	end
end

function onDraw()
	if not show then return end
	if door_sel then
		C(clr.white)
		H(draw_x-1,15,total_width+2)
		C(clr.red)
		H(draw_x-1,15,car_width*doorcut_f)
		H(draw_x+total_width+1,15,-car_width*doorcut_b)
		for i=1,cars_total do
			C(sel(i<=doorcut_f or cars_total-doorcut_b<i,clr.red,clr.white))
			V(cars_x[i]+car_width//2,16,3)
		end
		for _,v in ipairs(door_btns)do
			draw_btn_door(v[1],v[2],v[3],v[4])
		end
	end
end
