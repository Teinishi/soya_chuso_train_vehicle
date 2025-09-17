# 宗弥急行・中宗電鉄 車両ビークルデータ

Stormworks の複雑なビークルの管理を目的としています。

-   差分を Python スクリプトで記述し、1 つのベースビークルからバリエーションを生成
-   マイコンの Lua スクリプトを個別ファイルに分離し、生成時に埋め込み

現在は、中宗 3000 系のビークルデータを管理しています。

## ビルド

build.bat を実行すると、dist/ 以下にビークルとそのコンポーネント Mod フォルダが生成されます。これを Stormworks の vehicles フォルダにコピーすると、ゲーム内から開くことができます。

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

## ビルドスクリプトについて

新規ビークルを追加するときは、次のようなビルドスクリプトを作成し、build.bat に追記してください。ファイルパスはプロジェクトルートからの相対パスにしてください。このビルドスクリプトはベースビークルをそのまま出力します。`vehicle` に対して行うことができる操作については、lib/vehicle.py を参照してください。

```python
from lib.vehicle import Vehicle

BASE_VEHICLE = "{ビークルフォルダ名}/{ベースビークルファイル名}"
OUTPUT_PATH = "dist/{出力ビークルファイル名}"

vehicle = Vehicle(BASE_VEHICLE)

# ここにベースビークルに対して行う操作を記述

vehicle.resolve_lua_script()
vehicle.save(OUTPUT_PATH)
```

## Lua の生成・埋め込みについて

ビークルファイルと Lua ファイルを分離し、ビルド時に結合することができます。build.py で、`vehicle.resolve_lua_script()` とするとベースビークルに自動的に Lua を埋め込みます。複数のビークルを出力するときは次のように共通の `ScriptResolver` を使うと一部処理のキャッシュが効きます。

```python
from lib.script_resolver import ScriptResolver

# (略)

resolver = ScriptResolver()
vehicle1.resolve_lua_script(resolver=resolver)
vehicle2.resolve_lua_script(resolver=resolver)
```

#### ビルドパラメーター

ビルドスクリプトから Lua に関するパラメーターを渡すことができます。次のようにして dict を渡すと **build_params** として、Lua ファイル内の `@if` や、Lua スクリプトを生成するための Python スクリプト、`@require` で呼び出された Python スクリプトから参照することができます。

```python
vehicle.resolve_lua_script({"I am": "Build Parameter"})
```

### ベースビークルの書式

#### `@use` マーカー

次のような行を含むマイコン Lua ブロックを対象として、個別ファイルの Lua スクリプトを埋め込むことができます。Stormworks 上でベースビークルを編集し、マイコンの Lua ブロックにスクリプトの代わりに次のように記述してください。

```lua
-- @use lua/{.lua ファイルまたは .py ファイルへのパス} {任意のパラメータ}
```

例えば、次のように記述すると lua/hoge.lua がその Lua ブロックに埋め込まれます。

```lua
--- @use lua/hoge.lua
```

##### use パラメーター

また、複数の Lua ブロックでわずかに異なるような Lua スクリプトを使う場合などのために、パラメーターを渡すことができます。**use_param_text** でそのままの文字列が、**use_params** で JSON としてパースした値を参照できます。詳細は [Lua ファイル内での書式](#lua-ファイル内での書式) を参照してください。

```lua
--- @use lua/hoge.lua foo
--- @use lua/hoge.lua {"I am": "Use Parameter"}
```

##### .py ファイルを `@use` で呼び出す

.lua ファイルだけでなく、.py ファイルを指定することもできます。その場合、その Python スクリプトを実行し、標準出力を Lua スクリプトとして埋め込みます。パラメーターは、ビルドパラメーターを合わせて JSON 化して標準入力で渡されます。

```lua
--- @use lua/fuga.py {"I am": "Use Parameter"}
```

```json
{
    "build_params": { "I am": "Build Parameter" },
    "use_param_text": "{\"I am\": \"Use Parameter\"}",
    "use_params": { "I am": "Use Parameter" }
}
```

### Lua ファイル内の書式

.lua ファイルでは基本的に マイコン Lua ブロックの Lua スクリプトをそのまま個別のファイルとして書くことができます。非 ASCII 文字は埋め込み時にスキップされるため、日本語のコメントを書くことができます。

#### `@if`、`@elif`、`@else`、`@end` マーカー

複数の Lua ブロックでわずかに異なるような Lua スクリプトを使う場合などのために、条件分岐でスクリプトの内容を一部切り替えることができます。Python に近い構文で、次のように記述してください。Python と異なる点として、辞書のキーが文字列なら、`.` で繋ぐことで取得できます。

```lua
-- @if use_params.hoge == "fuga"
value = 123
-- @elif use_params.hoge == "piyo"
value = 456
-- @else
value = 789
-- @end
```

条件式では次のキーワードが利用できます。

-   **build_params**: ビルドスクリプトからのパラメーター
-   **use_param_text**: `@use` からのパラメーターの文字列
-   **use_params**: `@use` からのパラメーターを JSON としてパースした値

#### `@require` マーカー

複数の Lua スクリプトの間で共通の定数を使う場合などに、Python スクリプトから定数を生成して Lua スクリプトに埋め込むことができます。次のように記述してください。

```lua
-- @require {.py ファイルへのパス} {任意のパラメーター}
```

例えば、次のように記述すると lua/constants.py に対し、下の JSON を標準入力に渡して実行します。

```lua
-- @require lua/constants.py { "I am": "Require Parameter" }
```

```json
{
    "build_params": { "I am": "Build Parameter" },
    "use_param_text": "{\"I am\": \"Use Parameter\"}",
    "use_params": { "I am": "Use Parameter" },
    "require_param_text": "{\"I am\": \"Require Parameter\"}",
    "require_params": { "I am": "Require Parameter" }
}
```

標準出力に Lua リテラルの文字列を出力してください。Python の dict や list でも、次のようにして Lua リテラルに変換することができます。(TODO: 現状まだ import できないので直す)

```python
from lib.lua_literal import to_lua_literal

to_lua_literal([8, 6, 7, 3, 2]) # -> '{8,6,7,3,2}'
```

## ビークル開発ガイド

### ビークルを編集

-   ベースビークルとその Component Mod フォルダを Stormworks の vehicles/ にコピー
    -   中宗 3000 系の場合、chuso3000/CHUSO3000_TM2_JSMS_base.xml
-   Stormworks 内でベースビークルを編集
-   ベースビークルとその Component Mod フォルダを Stormworks の vehicles/ からコピー
-   変更を Git コミット

### Lua をビークルから分離

-   必要なら、extract_lua.py を用いてビークルデータから Lua スクリプトをすべて抽出し確認
-   Lua ファイルを lua/{ビークルフォルダ名}/{Lua ファイル名} に作成
-   Stormworks 上で Lua コードの代わりに `-- @use lua/{ビークルフォルダ名}/{Luaファイル名}` と記述
    -   @use がある Lua は Lua ブロック丸ごと置換するため、ベースビークルの Lua も機能するようにしておきたい場合は残してもよい

### Lua の定数等を別ファイルに分離

-   lua/ 以下に、実行すると JSON 文字列を出力する .py ファイルを作成
-   Lua コード内に `{定数名} = {デフォルト値} -- @require lua/{.py ファイル名} {キー}` と記述
    -   .py ファイルを実行し、標準出力を JSON としてパースした値を Lua リテラルに変換したものが、`=` の後に注入される
    -   パースした JSON がオブジェクトや配列ならキーを指定してフィールドを取得可能、キーを `.` 区切りにして深く辿ることも可
    -   デフォルト値は Lua としての構文を成立させてエディタ上でエラーが出ないようにとりあえず書いておくだけで、出力コードには関係ない

### 新規形式を追加

-   新規フォルダを追加 (chuso3000 と同階層)
-   ベースビークルを準備
    -   M 車と T 車で異なる床下機器など、差分パーツは別ビークルとして切り出しておき、ベースビークルにはそのための空間を空けてください。
        -   ただし、パンタグラフなどロジック配線がある差分パーツはベースビークルに残してください。
-   ベースビークル XML と、Component Mod のフォルダ (ビークルファイルと同名) を配置
-   build.bat に `python -m {ビークルフォルダ名}.build` を追記
-   上記 [ビルドスクリプトについて](#ビルドスクリプトについて) を参考に、build.py を作成
    -   別ビークルに切り出した差分パーツは `vehicle.include_vehicle(Vehicle.from_file({差分ビークルファイルパス}))` で統合できます。
        -   現状パーツのボクセル重複検知はできないので、ベースビークルと差分ビークルでボクセルが重複しないよう注意が必要です。
    -   パンタグラフなどロジック配線がある差分パーツは、必要に応じてベースビークルから `vehicle.remove_components(box=(({X1}, {Y1}, {Z1}), ({X2}, {Y2}, {Z2})))` で削除できます。
