# 项目代码结构与运行指南 (Code Architecture)

本目录包含上下文转移范式 (CHP) 的完整源码、演示程序及自动化测试。

## 代码结构

```
code/
├── chp/
│   ├── __init__.py
│   ├── protocol.py       # 上下文快照、认知模型与数据定义
│   ├── storage.py        # 状态中继引擎与带 TTL 的分布式租约锁
│   ├── executor.py       # 断点感知执行引擎 Worker (支持优雅挂起与恢复)
│   ├── handover.py       # 高层语义交接便签生成器
│   └── mock_env.py       # 远程 VPS 运维排障解耦环境模拟器
├── demo_laptop.py        # 模拟笔记本发起长程任务并中途 Handoff
├── demo_desktop.py       # 模拟台式机接管任务并无缝执行完毕
├── web_demo.py           # 零依赖双设备协同可视化 Web 仪表盘
└── test_chp.py           # 自动化单元与端到端测试套件
```

## 运行方式

### 1. 运行单元测试
```powershell
python code/test_chp.py
```

### 2. 模拟双设备接力演示
- 终端 A（笔记本端执行前两步并挂起）：
  ```powershell
  python code/demo_laptop.py
  ```
- 终端 B（台式机端一键接管并完成剩余三步）：
  ```powershell
  python code/demo_desktop.py
  ```

### 3. 启动交互式 Web 仪表盘
```powershell
python code/web_demo.py
```
浏览器访问 `http://localhost:8765` 体验可视化三列接力。
