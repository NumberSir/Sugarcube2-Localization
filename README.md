# <center><b>===== WIP =====</b></center>

为没有提供本地化方式的 SugarCube2 引擎的开源游戏提供一种粗暴的本地化方式。

配合 SugarCube-2-ModLoader 使用。

目前由 Degrees-of-Lewdity 汉化项目使用。

# 项目结构
```text
📁root
┣━ 📁data
┃  ┣━ 📁database
┃  ┣━ 📁log
┃  ┗━ 📁tmp
┣━ 📁repositories
┃  ┣━ 📁degrees-of-lewdity
┃  ┣━ 📁degrees-of-lewdity-plus
┃  ┣━ 📁sugarcube-2
┃  ┗━ 📁sugarcube-2-vrelnir
┣━ 📁resource
┃  ┗━ 📁img
┣━ 📁src
┣━ 📁tests
┣━ ⚙️.env
┣━ ⚙️.env.template
┣━ ⚙️.gitmodules
┣━ ⚙️.python-version
┣━ 📄LICENSE
┣━ 🐍main.py
┣━ ⚙️pyproject.toml
┣━ 📄README.md
┗━ ⚙️uv.lock
```

# 使用说明

## 更新本项目代码/子模块代码：
```shell
git pull
```
```shell
git submodule update --init --remote --recursive
```

## 使用前
1. 你的电脑上需要有 [Python][Python] 3.10 环境

## 初始化本项目项目环境
- 安装 [uv](https://docs.astral.sh/uv/#installation)
  - Windows:
    ```shell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
  - macOS / Linux:
    ```shell
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- 使用 uv 安装项目依赖
  ```shell
  uv sync
  ```

## 环境变量配置
- 创建 `.env` 文件，在其中填写 `.env.template` 中示例的环境变量
```dotenv
# 不要直接修改 `.env.template`，而是重新在项目根目录下创建一个新的 `.env` 文件再做修改
# 必填字段均已标注出来，未标注的均是有默认值的可选字段，若不进行改动可以删除字段
# 模板文件中已填写字段的值均为默认值
# 值有空格时需用引号 " 或 ' 包裹

# name, version, username 和 email 为构建 `User-Agent` 时用
# 格式: `User-Agent: <PROJECT_USERNAME>/<PROJECT_NAME>/<PROJECT_VERSION> (<PROJECT_EMAIL>)`
# 本项目的名称，脚本运行完成后的提醒会用到
PROJECT_NAME=Sugarcube2-Localization
PROJECT_VERSION=0.0.1
PROJECT_USERNAME=Anonymous
PROJECT_EMAIL=anonymous@email.com
# 可改为 `DEBUG`, `WARN` 等
# "extra[project_name]" 与 `PROJECT_NAME` 的值一致
PROJECT_LOG_FORMAT="<g>{time:HH:mm:ss}</g> | [<lvl>{level:^7}</lvl>] | {extra[project_name]}{message:<35}{extra[filepath]}"

##### PATH #####
# 所有路径均相对于本项目的根目录
PATH_DATA=data
# 存储自动生成的日志文件
PATH_LOG=data/log
PATH_PARATRANZ=data/paratranz
# 项目所需大文件/脚本自动生成的游戏文件存放处
PATH_RESOURCE=resource
# 临时文件存放处，如下载文件、临时生成数据文件等
# tmp 会在每次运行脚本时自动清理/重建
PATH_TMP=data/tmp

##### GITHUB #####
# !!!必填字段!!!
# Github 个人 token，发布用
GITHUB_ACCESS_TOKEN=

##### PARATRANZ #####
# !!!必填字段!!!
# Paratranz 项目 ID，下载文件用
PARATRANZ_PROJECT_ID=
# !!!必填字段!!!
# Paratranz 个人 token，下载文件用
PARATRANZ_TOKEN=

```

## 运行项目
```shell
uv run main.py
```

## 工作原理
1. 获取当前版本游戏文件路径
2. 获取当前版本 .twee 文件所有段落信息
3. 获取当前版本 .twee 文件所有基本元素信息(位置)
4. TODO: 获取当前版本 .js 文件 ...
5. 下载旧版汉化文件 (旧版英文-汉化映射)
6. TODO: 比对旧版英文 - 当前版本英文 
  - 未改变的: 直接映射 
  - 新添加的: 
  - 新删除的: 
7. TODO: 导出新版未汉化映射
8. TODO: 导出新版已汉化部分