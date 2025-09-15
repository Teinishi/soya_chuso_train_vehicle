M=math
function b2i(f)return f and 1 or 0 end
gB,gN,sB,sN=input.getBool,input.getNumber,output.setBool,output.setNumber
function gI(c)return M.floor(gN(c))end

function onTick()
	touches,page_id,dir,cars_f,cars_b,doorcut_f,doorcut_b=gN(25),gI(26),gI(27),gI(28),gI(29),gI(30)//6,gI(31)//6
	cars_total=cars_f+cars_b+1

	show,ext_mode,pwr_detail,brk_stat,srv_stat,door_sel=not gB(1),gB(2),false,false,false,false
	eqp,srv,door_detail,cars_draw_x,cars_draw_y=0,0,0,0,0

	if page_id==10100 then
		pwr_detail,door_detail,cars_draw_y=true,1,23

	elseif page_id==10200 then
		eqp,cars_draw_y=1,23

	elseif page_id==10400 then
		brk_stat,pwr_detail,cars_draw_x,cars_draw_y=true,true,4,3

	elseif page_id==20100 then
		srv_stat,door_detail,cars_draw_x,cars_draw_y=true,2,4,6

	elseif page_id==20200 then
		door_sel,cars_draw_y=true,23

	elseif 20601<=page_id and page_id<=20603 then
		srv,cars_draw_y=page_id-20600,13

	else
		show=false
	end

	for i=1,24 do
		sN(i,gN(i))
	end
	sB(1,show)
	sB(2,ext_mode)
	sN(28,touches)
	sN(29,(doorcut_f&15)<<14|(doorcut_b&15)<<10|b2i(dir<0)<<9|b2i(dir>0)<<8|(cars_f&15)<<4|(cars_b&15))
	sN(30,b2i(srv_stat)<<13|b2i(brk_stat)<<12|(eqp&15)<<8|b2i(door_sel)<<7|(srv&15)<<3|b2i(pwr_detail)<<2|door_detail&3)
	sN(31,cars_draw_x)
	sN(32,cars_draw_y)
end
