# 宗弥急行・中宗電鉄 車両ビークルデータ

中宗 3000 系のビークルデータを管理しています。ベースのビークルデータに対し、スクリプトで一定の操作をすることで各種差分ビークルを生成します。build.bat を実行すると、chuso3000/CHUSO3000_TM2_JSMS_base.xml に対して Mc 車と Tc 車それぞれの仕様を適用し、dist/ に出力します。

## フォルダ構成

-   chuso3000: 中宗 3000 系用のビークルデータフォルダ
    -   CHUSO3000_TM2_JSMS_base: 中宗 3000 系のベースビークルの Component Mod フォルダ
    -   CHUSO3000_TM2_JSMS_base.xml: 中宗 3000 系のベースビークル
    -   CHUSO3000_Mc_diff.xml: 中宗 3000 系の Mc 車の車番・床下機器
    -   CHUSO3000_Tc_diff.xml: 中宗 3000 系の Tc 車の車番・床下機器
    -   build.py: 中宗 3000 系のビルドスクリプト
-   dist: 完成品ビークルフォルダ
-   lib: ビークル操作などの Python ライブラリフォルダ
-   lua: ビークルに注入する Lua スクリプトフォルダ
    -   chuso3000: 中宗 3000 系用の Lua スクリプトフォルダ
-   build.bat: ビークルを一括ビルドするバッチファイル
-   extract_lua.py: 既存ビークルから Lua スクリプトを抽出する Python ファイル

## ビークル開発ガイド

### 完成品ビークルを生成

-   build.bat を実行
-   dist/ 以下に生成されたビークル XML と Component Mod フォルダを Stormworks の vehicles/ にコピー

### ビークルを編集

-   ベースビークルとその Component Mod フォルダを Stormworks の vehicles/ にコピー
    -   中宗 3000 系の場合、chuso3000/CHUSO3000_TM2_JSMS_base.xml
-   Stormworks 内でベースビークルを編集
-   ベースビークルとその Component Mod フォルダを Stormworks の vehicles/ からコピー
-   変更を Git コミット

### Lua をビークルから分離

-   必要なら、extract_lua.py を用いてビークルデータから Lua スクリプトをすべて抽出し確認
-   Lua ファイルを lua/{ビークルフォルダ名}/{Lua ファイル名} に作成
-   Stormworks 上で Lua コードの代わりに `-- @use {ビークルフォルダ名}/{Luaファイル名}` と記述
    -   @use がある Lua は Lua ブロック丸ごと置換するため、ベースビークルの Lua も機能するようにしておきたい場合は残してもよい

### Lua の定数等を別ファイルに分離

-   lua/ 以下に、実行すると JSON 文字列を出力する .py ファイルを作成
-   Lua コード内に `{定数名} = {デフォルト値} -- @require {.py ファイル名} {キー}` と記述
    -   .py ファイルを実行し、標準出力を JSON としてパースした値を Lua リテラルに変換したものが、`=` の後に注入される
    -   パースした JSON がオブジェクトや配列ならキーを指定してフィールドを取得可能、キーを `.` 区切りにして深く辿ることも可
    -   デフォルト値は Lua としての構文を成立させてエディタ上でエラーが出ないようにとりあえず書いておくだけで、出力コードには関係ない

### 新規形式を追加

-   新規フォルダを追加 (chuso3000 と同階層)
-   ベースビークルを準備
    -   M 車と T 車で異なる床下機器など、差分パーツは別ビークルとして切り出しておき、ベースビークルはそのための空間を空けておく
        -   ただし、パンタグラフなどロジック配線がある差分パーツはベースビークルに残しておく
-   ベースビークル XML と、Component Mod のフォルダ (ビークルファイルと同名) を置く
-   build.bat に `python -m {ビークルフォルダ名}.build` を追記
-   下記の内容で build.py を作成
    -   別ビークルに切り出した差分パーツは `vehicle.include_vehicle(Vehicle.from_file({差分ビークルファイルパス}))` で統合
        -   現状パーツのボクセル重複検知はできないので、ベースビークルと差分ビークルでボクセルが重複しないよう注意が必要
    -   パンタグラフなどロジック配線がある差分パーツを必要に応じてベースビークルから `vehicle.remove_components(box=(({X1}, {Y1}, {Z1}), ({X2}, {Y2}, {Z2})))` で削除

```python
import os
from lib.vehicle import Vehicle

DIRNAME = os.path.dirname(__file__)
DIST_PATH = os.path.join(os.path.dirname(DIRNAME), "dist")
BASE_VEHICLE = os.path.join(DIRNAME, "{ベースビークルファイル名}")
OUTPUT_PATH = os.path.join(DIST_PATH, "{出力ビークルファイル名}")

vehicle = Vehicle(BASE_VEHICLE)

# ここにベースビークルに対して行う操作を記述

vehicle.resolve_lua()
vehicle.save(OUTPUT_PATH)
```
