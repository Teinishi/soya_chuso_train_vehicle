M=math
function sel(f,a,b)return f and a or b end
function bit_at(n,i)return n>>i&1~=0 end
gB=input.getBool
function gI(c)return M.floor(input.getNumber(c))end

show,ext_mode,cars_f,cars_total,dir,detail,offset_x,offset_y=false,false,0,0,0,0,0,0
data={}
function onTick()
	show,ext_mode=gB(1),gB(2)
	n29=gI(29)
	cars_f=n29>>4&15
	dir,cars_total=-(n29>>9&1)+(n29>>8&1),cars_f+(n29&15)+1
	detail,offset_x,offset_y=gI(30)&7,gI(31),gI(32)
	for i=0,7 do
		data[i+1]={gI(1+3*i),gI(2+3*i),gI(3+3*i)}
	end
end

clr={
	black={0,0,0},
	white={200,200,200},
	red={200,0,0},
	yellow={200,200,0},
	cyan={0,150,150}
}
function C(c)
	screen.setColor(c[1],c[2],c[3])
end

R=screen.drawRectF
function H(x,y,w)R(x,y,w,1)end
function V(x,y,h)R(x,y,1,h)end
function D(x,y)H(x,y,1)end

function draw_number(x,y,n)
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

function draw_door_ind(x,y,n,s,inv,w,l)
	if n~=0 then
		w=sel(n<3,n+2,n)
		l=(2*x-w)//2+1
		C(clr.white)
		V(l-1,y,2)
		V(l+w,y,2)
		for i=1,n do
			C(sel(bit_at(s,sel(inv,i-1,n-i)),clr.yellow,clr.black))
			R(l+w/n*(i-1),y,w/n,2)
		end
	end
end

function draw_axle(x,y,p)
	H(x,y,sel(p,2,1))
	D(x+1,y+1)
	D(x+2,y)
end

function draw_pnt(x,y,flip,type,up)
	if type~=0 then
		if up then
			C(clr.white)
			D(x+sel(flip,-2,1),y)
			D(x+sel(flip,-2,1),y+2)
			if type&1~=0 then
				D(sel(flip,x-1,x),y+1)
			end
			if type&2~=0 then
				D(sel(flip,x-3,x+2),y+1)
			end
		else
			C(clr.yellow)
			H(sel(flip,x-2,x),y+2,2)
		end
	end
end

function draw_car(x,y,w,h,d_0x43,d_0x4a,d_0x4b,is_self)
	if not ext_mode then d_0x4a,d_0x4b=0,0 end
	car_no=d_0x4a>>18&15
	show_car_no=car_no~=0 and 9<w
	regen=bit_at(d_0x4b,22)
	cab_l,cab_r=d_0x4a>>1&1,d_0x4a&1
	ax_p_l,ax_p_r=bit_at(d_0x4a,3),bit_at(d_0x4a,2)

	C(clr.white)
	if detail&4~=0 and (regen or bit_at(d_0x4b,23))and(ax_p_l or ax_p_r) then
		C(regen and clr.yellow or clr.cyan)
		if ax_p_l then R(x+1,y+1,w//2,h-2)end
		if ax_p_r then R(x+w-1,y+1,-w//2,h-2)end
		if show_car_no then
			if car_no>=10 then R(x+w//2-3,y+1,7,5)
			else R(x+w//2-1,y+1,3,5)end
		end
		C(clr.black)
	end

	if show_car_no then
		if car_no>=10 then draw_number(x+w//2-3,y+1,1)end
		draw_number(x+w//2+sel(car_no<10,-1,1),y+1,car_no%10)
	end

	door_inv=bit_at(d_0x4b,0)
	if detail&3==1 then
		draw_door_ind(x+w//2,y-5,3,sel(d_0x43>>19&3~=0,63,0),door_inv)
	elseif detail&3==2 then
		draw_door_ind(x+w//2,y-5,sel(ext_mode,d_0x4a>>4&7,3),sel(ext_mode,d_0x4b>>1&63,(d_0x43>>19&1)*63),door_inv)
		draw_door_ind(x+w//2,y+h+3,sel(ext_mode,d_0x4a>>7&7,3),sel(ext_mode,d_0x4b>>7&63,(d_0x43>>20&1)*63),door_inv)
	end

	C(sel(bit_at(d_0x43,21),clr.red,clr.white))
	if is_self then V(x+1,y+1,5)end
	V(x,y+h,cab_l*2-h)
	D(x+1,y+cab_l)
	V(x+w-1,y+h,cab_r*2-h)
	D(x+w-2,y+cab_r)
	H(x+2,y,w-4)
	H(x,y+h-1,w)
	draw_axle(x+w//8,y+h,ax_p_l)
	draw_axle(x+w-w//8-3,y+h,ax_p_r)
	draw_pnt(x+w//6,y-3,false,d_0x4a>>12&3,bit_at(d_0x4b,16))
	draw_pnt(x+w-w//6,y-3,true,d_0x4a>>10&3,bit_at(d_0x4b,14))
end

function onDraw()
	if show then
		interval=M.min(M.floor(76/cars_total+0.5),20)
		car_width=interval+(interval>12 and -1 or 1)
		total_width=interval*(cars_total-1)+car_width
		draw_x,draw_y=offset_x+(96-total_width)//2,offset_y

		for i=1,cars_total do
			if data[i]~=nil then
				draw_car(
					draw_x+interval*(i-1),draw_y,car_width,7,
					data[i][1],data[i][2],data[i][3],i==cars_f+1
				)
			end
		end

		C(clr.white)
		if dir>0 then
			for i=0,2 do V(draw_x-5+i,draw_y+3-i,2*i+1)end
		elseif dir<0 then
			for i=0,2 do V(draw_x+total_width+4-i,draw_y+3-i,2*i+1)end
		end
	end
end
