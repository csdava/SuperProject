# 智慧社区管理系统 - 项目结构说明

## 技术栈

- **数据库**：SQLite（开发/小型部署，生产可切换 PostgreSQL/MySQL）
- **后端**：Django 6.x
- **前端**：HTML + 模板，后续可接小程序/大屏
- **硬件**：预留 `hardware_interface` 模块，用于门禁、道闸、传感器等对接

## 目录结构

```
DjangoProject333/
├── DjangoProject333/          # 项目配置
│   ├── settings.py            # 主配置（数据库、应用、中文时区等）
│   ├── urls.py                # 根 URL（admin、各业务模块）
│   ├── wsgi.py / asgi.py
│   └── ...
├── community_core/             # 社区基础管理（住户、楼栋）
├── property_fees/              # 物业收费系统
├── repair/                     # 报事报修管理
├── visitor_access/             # 访客与出入管理
├── security/                   # 智慧安防监控
├── life_services/              # 社区生活服务
├── vehicle_mgmt/               # 车辆管理
├── facility_mgmt/              # 设备设施管理
├── hardware_interface/         # 【预留】硬件接口（非 Django 应用）
│   ├── base.py                 # 硬件适配器基类
│   ├── adapters/               # 具体设备适配器（门禁、道闸、传感器等）
│   ├── schemas/                # 设备数据/指令结构
│   └── README.md
├── templates/                  # 全局模板
│   ├── base.html
│   └── community_core/
├── static/                     # 静态资源
│   └── css/
├── media/                      # 用户上传文件（运行时生成）
├── docs/                       # 项目文档
├── manage.py
└── db.sqlite3                  # SQLite 数据库文件（运行 migrate 后生成）
```

## 数据库连接

- 配置位置：`DjangoProject333/settings.py` 中的 `DATABASES`。
- 当前使用 SQLite，文件路径：项目根目录下的 `db.sqlite3`。
- 执行 `python manage.py migrate` 可初始化表结构并确认连接正常。

## 硬件接口预留

- 包路径：`hardware_interface/`（与各 Django 应用平级）。
- 所有设备适配器继承 `hardware_interface.base.BaseHardwareAdapter`，实现 `connect`、`disconnect`、`is_healthy`，按需实现 `read`/`write`。
- 后续可在视图或异步任务中调用，避免阻塞 Web 请求。

## 运行与验证

1. 安装依赖：`pip install django`
2. 迁移数据库：`python manage.py migrate`
3. 创建超级用户：`python manage.py createsuperuser`
4. 启动开发服务器：`python manage.py runserver`
5. 访问首页：http://127.0.0.1:8000/ ；管理后台：http://127.0.0.1:8000/admin/

## 用户角色（后续实现）

- 业主/住户、物业人员、物业经理、系统管理员；权限与菜单可在各 app 中扩展。
