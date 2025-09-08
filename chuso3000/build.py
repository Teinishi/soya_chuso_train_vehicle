import os
from lib.vehicle import Vehicle

DIRNAME = os.path.dirname(__file__)
DIST_PATH = os.path.join(os.path.dirname(DIRNAME), "dist")
BASE_VEHICLE = os.path.join(DIRNAME, "CHUSO3000_TM2_JSMS_base.xml")
MC_DIFF_VEHICLE = os.path.join(DIRNAME, "CHUSO3000_Mc_diff.xml")
TC_DIFF_VEHICLE = os.path.join(DIRNAME, "CHUSO3000_Tc_diff.xml")
MC_OUTPUT = os.path.join(DIST_PATH, "CHUSO3000_TM2_JSMS_Mc.xml")
TC_OUTPUT = os.path.join(DIST_PATH, "CHUSO3000_TM2_JSMS_Tc.xml")

# ビークルを読み込み
vehicle_mc = Vehicle.from_file(BASE_VEHICLE)
vehicle_tc = Vehicle.from_file(BASE_VEHICLE)

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
    "Powered Axle", "Both", microprocessor_name="Train")
vehicle_tc.set_microprocessor_property(
    "Powered Axle", "None", microprocessor_name="Train")

vehicle_mc.set_microprocessor_property(
    "Rear Pantograph", "Single arm inner", microprocessor_name="Train")
vehicle_tc.set_microprocessor_property(
    "Rear Pantograph", "None", microprocessor_name="Train")

vehicle_mc.set_microprocessor_property(
    "Car No.", "2", microprocessor_name="Train")
vehicle_tc.set_microprocessor_property(
    "Car No.", "1", microprocessor_name="Train")

vehicle_mc.set_microprocessor_property(
    "Car Number", "2", microprocessor_name="Passenger Guidance")
vehicle_tc.set_microprocessor_property(
    "Car Number", "1", microprocessor_name="Passenger Guidance")

vehicle_mc.set_microprocessor_property(
    "Direction", "Outbound", microprocessor_name="Passenger Guidance")
vehicle_tc.set_microprocessor_property(
    "Direction", "Inbound", microprocessor_name="Passenger Guidance")

vehicle_mc.set_microprocessor_property(
    "Direction", "Outbound", microprocessor_name="Driver Monitor")
vehicle_tc.set_microprocessor_property(
    "Direction", "Inbound", microprocessor_name="Driver Monitor")

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


# Tc車の運転台キースイッチをオン
vehicle_tc.set_attribute("default_state", True, custom_name="Driving")

# Tc車のマスコン位置をニュートラル、レバーサーを前に
vehicle_tc.set_microprocessor_property(
    "Default Position", "Neutral", microprocessor_name="Master Controller")
vehicle_tc.set_microprocessor_property(
    "Reverser Default", "Front", microprocessor_name="Master Controller")

# TODO: Tc車の前後選択スイッチをデフォルト前に

# TODO: Tc車を全選択して180度回転

# 書き出し
vehicle_mc.save(MC_OUTPUT)
vehicle_tc.save(TC_OUTPUT)
exit(0)
