from lib.vehicle import Vehicle
from lib.script_resolver import ScriptResolver

BASE_VEHICLE = "chuso3000/CHUSO3000_TM2_JSMS_base.xml"
MC_DIFF_VEHICLE = "chuso3000/CHUSO3000_Mc_diff.xml"
TC_DIFF_VEHICLE = "chuso3000/CHUSO3000_Tc_diff.xml"
DEFAULT_DIFF_VEHICLE = "chuso3000/CHUSO3000_default_diff.xml"
JSMS_DIFF_VEHICLE = "chuso3000/CHUSO3000_JSMS_diff.xml"
MC_OUTPUT = "dist/CHUSO3000_TM2_Mc.xml"
TC_OUTPUT = "dist/CHUSO3000_TM2_Tc.xml"
MC_JSMS_OUTPUT = "dist/CHUSO3000_TM2_JSMS_Mc.xml"
TC_JSMS_OUTPUT = "dist/CHUSO3000_TM2_JSMS_Tc.xml"

# ビークルを読み込み
vehicle_mc: Vehicle = Vehicle.from_file(BASE_VEHICLE)
vehicle_tc: Vehicle = vehicle_mc.copy()

# 車体マージのブロック
main_body_position = (0, 1, 0)

# バッテリーの位置をメモ
battery_position = vehicle_mc.get_component(custom_name="hub").get_position()

# Tc車のパンタグラフを削除
vehicle_tc.remove_components(box=((-4, 13, -36), (4, 16, -26)))
vehicle_tc.remove_component(microprocessor_name="Pantograph")

# Tc車のVVVF音を削除
vehicle_tc.remove_component(position=(2, -2, 1))

# 車軸ペインタブルの名前を変更
vehicle_tc.set_custom_name("TRAIN1", custom_name="TRAIN4")
vehicle_tc.set_custom_name("TRAIN2", custom_name="TRAIN3")
# ARCダイヤルの名前を変更
vehicle_tc.set_custom_name("TRAIN1_ARC", custom_name="TRAIN4_ARC")
# キーパッドの名前を変更
vehicle_tc.set_custom_name("TRAIN1_H1", custom_name="TRAIN4_H1")
vehicle_tc.set_custom_name("TRAIN1_H2", custom_name="TRAIN4_H2")
vehicle_tc.set_custom_name("TRAIN1_H3", custom_name="TRAIN4_H3")

# マイコンプロパティ
vehicle_mc.set_microprocessor_property(
    "Motor", "yes", microprocessor_name="ME SiC Sound")
vehicle_tc.set_microprocessor_property(
    "Motor", "no", microprocessor_name="ME SiC Sound")

vehicle_mc.set_microprocessor_property(
    "Car Type", "3001", microprocessor_name="CHUSO 3000 Main Curcit")
vehicle_tc.set_microprocessor_property(
    "Car Type", "3101", microprocessor_name="CHUSO 3000 Main Curcit")

vehicle_mc.set_microprocessor_property(
    "Powered Axle", "Both", microprocessor_name="NITS Gateway")
vehicle_tc.set_microprocessor_property(
    "Powered Axle", "None", microprocessor_name="NITS Gateway")

vehicle_mc.set_microprocessor_property(
    "Rear Pantograph", "Single arm inner", microprocessor_name="NITS Gateway")
vehicle_tc.set_microprocessor_property(
    "Rear Pantograph", "None", microprocessor_name="NITS Gateway")

vehicle_mc.set_microprocessor_property(
    "Car No.", "2", microprocessor_name="NITS Gateway")
vehicle_tc.set_microprocessor_property(
    "Car No.", "1", microprocessor_name="NITS Gateway")

vehicle_mc.set_microprocessor_property(
    "Car Number", "2", microprocessor_name="Passenger Guidance")
vehicle_tc.set_microprocessor_property(
    "Car Number", "1", microprocessor_name="Passenger Guidance")

vehicle_mc.set_microprocessor_property(
    "Direction", "Outbound", microprocessor_name="Passenger Guidance")
vehicle_tc.set_microprocessor_property(
    "Direction", "Inbound", microprocessor_name="Passenger Guidance")

vehicle_mc.set_microprocessor_property(
    "Direction", "Outbound", microprocessor_name="Operation Manager")
vehicle_tc.set_microprocessor_property(
    "Direction", "Inbound", microprocessor_name="Operation Manager")

vehicle_mc.set_microprocessor_property(
    "Direction", "Outbound", microprocessor_name="JSMS Transponder")
vehicle_tc.set_microprocessor_property(
    "Direction", "Inbound", microprocessor_name="JSMS Transponder")

# 車番・床下機器を追加読み込み
vehicle_mc.include_vehicle(Vehicle.from_file(MC_DIFF_VEHICLE))
vehicle_tc.include_vehicle(Vehicle.from_file(TC_DIFF_VEHICLE))

# 側面車番・床下機器をマージ
vehicle_mc.merge_bodies(
    vehicle_mc.get_component(position=(6, 8, -30)),
    vehicle_mc.get_component(position=(6, 7, -30))
)
vehicle_tc.merge_bodies(
    vehicle_tc.get_component(position=(6, 8, -30)),
    vehicle_tc.get_component(position=(6, 7, -30))
)

# 前面車番をマージ
vehicle_mc.merge_bodies(
    vehicle_mc.get_component(position=(4, 4, 33)),
    vehicle_mc.get_component(position=(4, 3, 33))
)
vehicle_tc.merge_bodies(
    vehicle_tc.get_component(position=(4, 4, 33)),
    vehicle_tc.get_component(position=(4, 3, 33))
)

# Mc車のJSMSトランスポンダを削除
vehicle_mc.remove_component(microprocessor_name="JSMS Transponder")
vehicle_mc.remove_components(box=((0, -1, 10), (1, 0, 12)))

# JSMS仕様と分岐
vehicle_mc_jsms = vehicle_mc.copy()
vehicle_tc_jsms = vehicle_tc.copy()

# 非JSMS仕様はTc車のJSMSトランスポンダも削除
vehicle_tc.remove_component(microprocessor_name="JSMS Transponder")
vehicle_tc.remove_components(box=((0, -1, 10), (1, 0, 12)))

# 非JSMS仕様
default_vehicles = [vehicle_mc, vehicle_tc]
default_diff_vehicle: Vehicle = Vehicle.from_file(DEFAULT_DIFF_VEHICLE)
for v in default_vehicles:
    v.include_vehicle(default_diff_vehicle.copy())
    v.merge_bodies(
        v.get_component(position=(2, 5, 32)),
        v.get_component(position=main_body_position)
    )

    # 客室-乗務員室扉の電気配線
    v.add_logic_link("electric", battery_position, (0, 2, 26))
    v.add_logic_link("electric", battery_position, (3, 4, 26))

# JSMS仕様
jsms_vehicles = [vehicle_mc_jsms, vehicle_tc_jsms]
jsms_diff_vehicle: Vehicle = Vehicle.from_file(JSMS_DIFF_VEHICLE)
for v in jsms_vehicles:
    v.include_vehicle(jsms_diff_vehicle.copy())
    jsms_diff_pos = jsms_diff_vehicle.get_components()[0].get_position()
    v.merge_bodies(
        v.get_component(position=jsms_diff_pos),
        v.get_component(position=main_body_position)
    )

# JSMS仕様のTc車の運転台キースイッチをオン
vehicle_tc_jsms.set_attribute("default_state", True, custom_name="Driving")

# JSMS仕様のTc車のマスコン位置をニュートラル、レバーサーを前に
vehicle_tc_jsms.set_microprocessor_property(
    "Default Position", "Neutral", microprocessor_name="Master Controller")
vehicle_tc_jsms.set_microprocessor_property(
    "Reverser Default", "Front", microprocessor_name="Master Controller")

# JSMS仕様のTc車の前後選択スイッチをデフォルト前に
vehicle_tc_jsms.set_microprocessor_property(
    "Default", "Front", microprocessor_name="Direction Switch")

# TODO: Tc車を全選択して180度回転

# 書き出し
resolver = ScriptResolver()
build_params = {"is_jsms": True} # TODO: Luaの非JSMS化対応が完了したらFalseにする
vehicle_mc.resolve_lua_script(build_params, resolver=resolver)
vehicle_tc.resolve_lua_script(build_params, resolver=resolver)
build_params = {"is_jsms": True}
vehicle_mc_jsms.resolve_lua_script(build_params, resolver=resolver)
vehicle_tc_jsms.resolve_lua_script(build_params, resolver=resolver)

vehicle_mc.save(MC_OUTPUT)
vehicle_tc.save(TC_OUTPUT)
vehicle_mc_jsms.save(MC_JSMS_OUTPUT)
vehicle_tc_jsms.save(TC_JSMS_OUTPUT)
