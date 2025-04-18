为没有提供本地化方式的 SugarCube2 引擎的开源游戏提供一种粗暴的本地化方式。

配合 SugarCube-2-ModLoader 使用。

目前由 Degrees-of-Lewdity 汉化项目使用。

## 更新本项目代码/子模块代码：
```shell
git submodule update --init --remote --recursive
```

## 可配置项
```dotenv
##### PROJECT #####
# 本项目的名称，脚本运行完成后的提醒会用到
PROJECT_NAME=SugarCube2-Localization
# loguru 库的日志输出显示格式
PROJECT_LOG_FORMAT="<g>{time:HH:mm:ss}</g> | [<lvl>{level}</lvl>] | {message}"

##### PATH #####
# 运行时下载/生成/使用的数据路径
PATH_DATA=data
# 临时文件路径，每次运行清空
PATH_TMP=data/tmp
# 从 Paratranz 下载的数据路径
PATH_PARATRANZ=data/paratranz

##### GITHUB #####
# Github 个人 token，发布汉化用
GITHUB_ACCESS_TOKEN=ghp_xxx

##### PARATRANZ #####
# Paratranz 项目 ID（数字），下载文件用
PARATRANZ_PROJECT_ID=xxxx
# Paratranz 个人 token，下载文件用
PARATRANZ_TOKEN=xxxx
```