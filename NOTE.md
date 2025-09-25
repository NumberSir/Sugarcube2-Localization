# 写项目时的一些心路历程和吐槽

## 神人代码
> repositories/sugarcube-2/src/extensions/ecmascript-extensions.js
- 研究源码时总有些地方怪怪的，有时候看上文是 String 看下文又能 splice，原来作者改过内置类函数，给 String 加了 splice 函数。

> repositories/degrees-of-lewdity/game/00-framework-tools/03-Patcher/dol-widget.js
- 找了半天，终于找到 DoL 里的 `$_` 开头的变量从哪儿来的了，原来是自己改了 SugarCube2 内置的 `<<widget>>` 复用函数。
- 不过在汉化脚本中无需做特殊处理。本质上这些变量仍然同 `$`，即 `State.variables`，只不过在 DoL 中额外做了处理。

> repositories/sugarcube-2/src/sugarcube.js
- SugarCube2 的代码入口
