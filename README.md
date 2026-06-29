# 维修商贸一体化管理系统

## 系统概述

维修商贸一体化管理系统是一套完整的商用级管理解决方案，专为维修行业、商贸企业设计。系统涵盖工单管理、进销存、财务管理、客户管理、供应商管理等核心模块，支持私有化部署。

## 技术栈

### 前端
- Vue 3.3.4
- Vite 4.4.9
- Element Plus 2.3.14
- Vue Router 4.2.4
- Pinia 2.1.6
- Axios 1.5.0

### 后端
- Python 3.11
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- Flask-JWT-Extended 4.5.2
- PyMySQL 1.1.0

### 数据库
- MySQL 8.0
- Redis 7

### 部署
- Docker
- Docker Compose

## 功能模块

### 1. 工单管理
- 工单类型自定义（设备安装/维修/维护、网络安装/维修/维护等）
- 工单全流程闭环管理
- 自动派单与申领单生成
- 外修供应商绑定

### 2. 进销存管理
- 采购单、销售单、销售预定单
- 退货单、零售单
- 同价调拨、变价调拨
- 商品组装、拆卸
- 成本调价

### 3. 库存管理
- 实时库存查询
- 库存台账
- 库存盘点
- 库存预警

### 4. 财务管理
- 账户管理
- 收付款管理
- 应收应付往来
- 发票管理
- 电子收据

### 5. 客户管理
- 客户资料管理
- 折扣率设置
- 历史交易记录
- 往来对账

### 6. 供应商管理
- 供应商资料
- 采购记录
- 外修合作记录
- 应付账款

### 7. 商品管理
- 商品编码自动生成
- 条码生成与打印
- 价格管理
- 库存预警

### 8. 系统管理
- 用户管理
- 角色权限管理
- 操作日志
- 数据修改留痕
- 打印模板管理

## 部署指南

### 方式一：Docker Compose 一键部署（推荐）

#### 1. 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 服务器内存建议 4GB+

#### 2. 部署步骤

```bash
# 1. 克隆项目
git clone <项目地址>
cd repair-system

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

#### 3. 访问系统
- 前端地址：http://服务器IP
- 后端API：http://服务器IP:5000
- 默认账号：admin / 123456

#### 4. 停止服务
```bash
docker-compose down
```

#### 5. 数据备份
```bash
# 备份MySQL数据
docker exec repair_system_mysql mysqldump -urepair_user -pRepair@2024 repair_system > backup.sql

# 恢复MySQL数据
docker exec -i repair_system_mysql mysql -urepair_user -pRepair@2024 repair_system < backup.sql
```

### 方式二：手动部署

#### 1. 安装MySQL
```bash
# 安装MySQL 8.0
sudo apt update
sudo apt install mysql-server-8.0

# 创建数据库
mysql -u root -p
CREATE DATABASE repair_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'repair_user'@'%' IDENTIFIED BY 'Repair@2024';
GRANT ALL PRIVILEGES ON repair_system.* TO 'repair_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

#### 2. 安装Redis
```bash
sudo apt install redis-server
```

#### 3. 部署后端
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
flask db init
flask db migrate
flask db upgrade

# 启动服务
python app.py
```

#### 4. 部署前端
```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

## 飞牛NAS Docker部署详细教程

### 1. 准备工作

登录飞牛NAS管理界面，确保已安装Docker套件。

### 2. 上传项目文件

将项目文件上传到NAS的共享文件夹，例如：`/volume1/docker/repair-system`

### 3. 创建Docker网络

```bash
# SSH登录NAS
ssh admin@你的NAS_IP

# 创建专用网络
docker network create repair_network
```

### 4. 启动MySQL容器

```bash
docker run -d \
  --name repair_system_mysql \
  --network repair_network \
  -e MYSQL_ROOT_PASSWORD=Repair@2024 \
  -e MYSQL_DATABASE=repair_system \
  -e MYSQL_USER=repair_user \
  -e MYSQL_PASSWORD=Repair@2024 \
  -v /volume1/docker/repair-system/mysql_data:/var/lib/mysql \
  -v /volume1/docker/repair-system/backend/database/init.sql:/docker-entrypoint-initdb.d/init.sql \
  -p 3306:3306 \
  --restart always \
  mysql:8.0 \
  --default-authentication-plugin=mysql_native_password \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

### 5. 启动Redis容器

```bash
docker run -d \
  --name repair_system_redis \
  --network repair_network \
  -v /volume1/docker/repair-system/redis_data:/data \
  --restart always \
  redis:7-alpine
```

### 6. 构建并启动后端

```bash
# 进入后端目录
cd /volume1/docker/repair-system/backend

# 构建镜像
docker build -t repair_system_backend .

# 启动容器
docker run -d \
  --name repair_system_backend \
  --network repair_network \
  -e FLASK_ENV=production \
  -e DATABASE_URL=mysql+pymysql://repair_user:Repair@2024@repair_system_mysql:3306/repair_system \
  -e REDIS_URL=redis://repair_system_redis:6379/0 \
  -e JWT_SECRET_KEY=RepairSystemSecretKey2024 \
  -v /volume1/docker/repair-system/backend:/app \
  -v /volume1/docker/repair-system/uploads:/app/uploads \
  -p 5000:5000 \
  --restart always \
  repair_system_backend
```

### 7. 构建并启动前端

```bash
# 进入前端目录
cd /volume1/docker/repair-system/frontend

# 构建镜像
docker build -t repair_system_frontend .

# 启动容器
docker run -d \
  --name repair_system_frontend \
  --network repair_network \
  -p 80:80 \
  --restart always \
  repair_system_frontend
```

### 8. 验证部署

- 打开浏览器访问：`http://你的NAS_IP`
- 使用默认账号登录：admin / 123456

### 9. 设置开机自启

在飞牛NAS的Docker管理界面中，设置所有容器为自动启动。

## 目录结构

```
repair-system/
├── docker-compose.yml          # Docker Compose配置
├── README.md                   # 项目说明
├── backend/                    # 后端代码
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                  # 主应用
│   └── database/
│       └── init.sql            # 数据库初始化脚本
└── frontend/                   # 前端代码
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/
        ├── stores/
        ├── api/
        ├── views/
        └── styles/
```

## 默认账号

- 用户名：admin
- 密码：123456

## 注意事项

1. **生产环境部署前请修改默认密码**
2. **定期备份数据库**
3. **建议使用HTTPS部署**
4. **配置防火墙规则，仅开放必要端口**

## 技术支持

如有问题，请查看日志或联系技术支持。

```bash
# 查看后端日志
docker logs -f repair_system_backend

# 查看前端日志
docker logs -f repair_system_frontend

# 查看MySQL日志
docker logs -f repair_system_mysql
```

## 许可证

本项目仅供学习和内部使用。
