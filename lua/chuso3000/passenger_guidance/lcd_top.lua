train_type_colors = {} -- @require lua/route_data_lua.py lcd_train_type_color_table

car_no = property.getNumber('Car Number')

train_type = 0
function onTick()
    train_type = input.getNumber(2)
end

S=screen
C,R=S.setColor,S.drawRectF
function V(x,y,h)R(x,y,1,h)end
function H(x,y,w)R(x,y,w,1)end
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
if 0<n and n<4 or n==5 or n==9 then H(x,y+4,n<3 and 3 or 2)end
if n==0 or 5<n and n<9 then D(x+1,y+4)end
if n==1 then V(x+1,y,4)end
end

function onDraw()
	C(5,5,5)R(0,0,96,64)
	C(2,2,2)R(0,8,96,56)
	C(200,200,200)R(0,24,96,40)R(88,2,7,5)R(89,1,5,7)
	C(0,0,0)draw_number(90,2,car_no)

	c = train_type_colors[train_type]
	if c then
		C(c[1], c[2], c[3])
		R(0, 0, 96, 1)
		R(0, 0, 24, 8)
	end
end
