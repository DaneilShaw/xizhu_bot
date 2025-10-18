# 熙烛bot

本项目是基于 Nonebot 框架开发的南昌大学楹联诗词协会（OC熙烛）bot，旨在为协会QQ群提供诗词楹联相关的功能。
项目集成了诗词楹联查询、飞花令、社群互动等功能。

## 功能特色

- 支持诗词楹联查询与检索
- 支持飞花令功能
- 群聊互动

## 数据来源

本项目借用了以下开源项目的数据：

- [couplet-dataset](https://github.com/wb14123/couplet-dataset)（数据集来自冯重朴_梨味斋散叶_的博客）
- [chinese-poetry-master](https://github.com/chinese-poetry/chinese-poetry)
- [poetry-source-master](https://github.com/chinese-poetry/poetry-source)

## 项目依赖

本项目基于 [Nonebot2](https://github.com/nonebot/nonebot2) 框架开发。

## 文件结构说明

- `src/` 机器人主程序及插件
- `data/` 诗词楹联数据库
- `.env*` 环境配置文件

## 致谢

- [NoneBot2](https://github.com/nonebot/nonebot2)： 插件使用的开发框架。
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)： 基于 NTQQ 的 Bot 协议端实现。
- [couplet-dataset](https://github.com/wb14123/couplet-dataset)： 提供楹联数据。
- [chinese-poetry-master](https://github.com/chinese-poetry/chinese-poetry)： 提供诗词数据。
- [poetry-source-master](https://github.com/chinese-poetry/poetry-source)： 提供诗词数据。

感谢以上项目的贡献者！

## 特别说明

本项目部分功能基于 [NapCat](https://github.com/NapCat/NapCat) 框架实现。  
NapCat 采用混合协议开源，使用和分发 NapCat 相关代码时需遵守以下要求：

- NapCat 相关代码遵循 NapCat 官方协议和要求；
- 未经 NapCat 作者授权，禁止基于 NapCat 代码进行二次开发；
- 使用 NapCat 相关功能时，需遵守当地法律法规；
- 详细许可信息请参考 NapCat 官方仓库说明。

本项目其他部分代码遵循本仓库所声明的开源协议。

---

如有问题或建议，欢迎 issue 或联系维护者。