# 认识Pyjepsen

欢迎使用本分布式测试框架，本框架是对Jepsen测试框架的一个Python语言的翻译版本
Jepsen测试框架源代码仓库: https://github.com/jepsen-io/jepsen

## 本项目基本结构
本项目以pyjepsen.py为项目的主入口
本项目的特性控制主要依靠配置文件进行实现
```
│ pyjepsen.py # 本项目主入口
│ config.yaml # 本项目配置文件
│ README.md # 本项目介绍
│ requirements.txt # 本项目依赖
├─bin # 可执行文件，用于checker调用
├─checker # checker模块，检验运行结果
├─client # client模块，控制对服务器操作
├─db # db模块，控制数据库操作
├─doc # 相关文档
├─generator # generator模块，生成操作
├─histories # 保存记录操作历史的文件
├─logger # logger模块，负责日志和文件读写功能
├─logs # 保存日志文件
├─nemesis # nemesis模块，为数据库操作注入错误
├─util # 公用方法

```