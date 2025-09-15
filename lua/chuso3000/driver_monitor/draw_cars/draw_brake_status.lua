SRV_BIT_POS_MAP={18,17,19}
SRV_OUT_CH_MAP={9,7,11}

M=math
function clamp(x,a,b)return M.min(M.max(x,a),b)end
function sel(f,a,b)return f and a or b end
function bit_at(n,i)return n>>i&1~=0 end
I,O=input,output
gB,gN,sB,sN=I.getBool,I.getNumber,O.setBool,O.setNumber
function gI(c)return M.floor(gN(c))end

srv_stat,brk_stat=false,false
data={}
interval,car_width,total_width,draw_x=0,0,0,0
function onTick()
	show,ext_mode=gB(1),gB(2)
	n29,n30=gI(29),gI(30)
	cars_f,cars_b=n29>>4&15,n29&15
	cars_total=cars_f+cars_b+1
	srv_stat,brk_stat=bit_at(n30,13),bit_at(n30,12)
	offset_x=gI(31)
	for i=0,7 do
		data[i+1]={gI(1+3*i),gI(2+3*i),gI(3+3*i)}
	end

	interval=M.min(M.floor(76/cars_total+0.5),20)
	car_width=interval+(interval>12 and -1 or 1)
	total_width=interval*(cars_total-1)+car_width
	draw_x=offset_x+(96-total_width)//2
end

clr={
	black={0,0,0},
	white={200,200,200},
	bluegray={30,36,44},
	yellow={200,200,0},
	cyan={0,150,150}
}
function C(c,o)screen.setColor(c[1],c[2],c[3],o or 255)end

R=screen.drawRectF
function H(x,y,w)R(x,y,w,1)end
function V(x,y,h)R(x,y,1,h)end
function D(x,y)H(x,y,1)end

function draw_number3(x,y,v,w,c,z,d)
d=d or 0
v=clamp(M.floor(10^d*v+0.5),0,10^w-1)
x=x+4*w-4
for i=1,w do
n=v%10
if i==d then
C(c,127)
D(x-1,y+4)
end
if v~=0 or z or i<=d+1 then
C(c)
if n==2 or n==3 or n==5 or n==7 then H(x,y,2)end
if n==0 or n==6 or 7<n then D(x+1,y)end
if 3<n and n<8 then D(x+2,y)end
if n==1 or 7<n then D(x,y+1)end
if n==0 or 4<n and n<7 then V(x,y+1,2)end
if 1<n and n<4 or 6<n and n<9 then D(x+2,y+1)end
if n==0 or n==4 or n==9 then V(x+2,y+1,3)end
if n==4 then D(x+1,y+1)D(x,y+2)D(x+2,y+4)
elseif 1<n then D(x+1,y+2)end
if n%2==0 then D(x,y+3)end
if n==4 or n==7 then D(x+1,y+3)
elseif 2<n and n<9 then D(x+2,y+3)end
if 0<n and n<4 or n==5 or n==9 then H(x,y+4,sel(n<3,3,2))end
if n==0 or 5<n and n<9 then D(x+1,y+4)end
if n==1 then V(x+1,y,4)end
end
v=v//10
x=x-4
end
end

function draw_bar(x,y,w,h,c)
	y1,y2=y,y+h
	if y1>y2 then y1,y2=y2,y1 end
	y1f,y2f=M.floor(y1),M.floor(y2)
	if y1f==y2f then
		C(c,255*(y2-y1))
		R(x,y1f,w,1)
	else
		C(c,255*(1-y1+y1f))
		R(x,y1f,w,1)
		C(c)
		R(x,y1f+1,w,y2f-y1f-1)
		C(c,255*(y2-y2f))
		R(x,y2f,w,1)
	end
end

function onDraw()
	if not show then return end
	if brk_stat then
		C(clr.black)
		R(draw_x,12,total_width,8)
		for i=0,cars_total-1 do
			if data[i+1]~=nil then
				data_0x43=data[i+1][1]
				pwr_val,brk_val=((data_0x43>>9&1023)+512)%1024-512,(data_0x43&511)*2
				car_cx=draw_x+i*interval+car_width//2
				draw_bar(car_cx-2,20,2,-8*clamp(brk_val/600,0,1),clr.white)
				draw_number3(car_cx-6,21,brk_val,3,clr.white)
				if not ext_mode or data[i+1][2]>>2&3~=0 then
					pwr_clr=clr.white
					if pwr_val>0 then pwr_clr=clr.cyan
					elseif pwr_val<0 then pwr_clr=clr.yellow end
					draw_bar(car_cx+1,20,2,-8*clamp(M.abs(pwr_val)/600,0,1),pwr_clr)
					draw_number3(car_cx-3,27,M.abs(pwr_val),3,pwr_clr)
				end
			end
		end
	elseif srv_stat then
		C(clr.bluegray)
		H(draw_x,22,total_width)
		H(draw_x,28,total_width)
		for i=0,cars_total-1 do
			if ext_mode and data[i+1]~=nil then
				srv_data=data[i+1][3]>>17&7
				car_cx=draw_x+i*interval+car_width//2
				C(sel(bit_at(srv_data,1),clr.yellow,clr.black))
				R(car_cx-1,21,3,3)
				C(sel(bit_at(srv_data,0),clr.yellow,clr.black))
				R(car_cx-1,27,3,3)
			end
		end
	end
end
