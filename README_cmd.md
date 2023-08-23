# 构建运行环境

## 升级依赖后的操作
```
pipenv requirements > requirements.txt
```

## 构建镜像文件

### 构建开发/回测镜像

开发过程中，使用以下命令构建运行环境，对代码进行测试

```bash
# Apple M1 build command
docker buildx build --platform linux/amd64 -t  galahade/future-trading-dev .
# 使用缓存构建image
docker build --tag galahade/future-trading-dev .
# 不使用缓存，从头构建image
docker build --no-cache --tag galahade/future-trading-dev .
# 构建完成镜像后进行连接测试
docker run -e TZ=Asia/Shanghai --rm -ti galahade/future-trading-dev /bin/bash
docker run --rm -ti galahade/future-trading-dev /bin/bash
# 对镜像打标签
docker tag galahade/future-trading-dev galahade/future-trading-dev:v0.1
docker tag galahade/future-trading-dev galahade/future-trading-test:v0.1
```

### 构建测试镜像

当开发工作完成后，将代码提交到`main`分支，然后构建测试环境，用来监测各品种的开仓情况。

```bash
docker build --tag galahade/future-trading-dev .
docker tag galahade/future-trading-dev galahade/future-trading-test:v0.2
```

### 构建生产镜像

该环境用来进行实盘交易，需要配置交易信息，以实现自动化交易。

```bash
docker build --tag galahade/bottom-trade-prod .
docker tag galahade/bottom-trade-prod galahade/bottom-trade-prod:v0.1
```

### 构建专用环境

当策略为某个专用目的（比如小资金高比例投资）使用时，在开发环境验证完成后，需要对开仓比例等进行专门调整。所以它的使用方式和通用环境有一些区别，具体步骤如下：

1. 构建专用环境的docker镜像，如：`galahade/bottom-trade-young`

   ```bash
   docker build --tag galahade/bottom-trade-young .
   docker tag galahade/bottom-trade-young galahade/bottom-trade-young:v0.1
   ```

2. 将上述镜像打标签并上传至dockerhub

3. 部署该镜像

   ```bash
   docker stack deploy -c docker-compose-young.yml bottom-trade-young
   docker stack rm bottom-trade-young
   ```

## 部署运行环境

运行环境均使用 **Docker Swarm** 进行部署。

在部署前，需要做的准备工作：

### 创建Docker volume

```bash
docker volume create future-trading-log-data
docker volume create ft-log-data
# 查看 volume 内容的命令
docker run -it -v future-trading-log-data:/log --rm bash:4.4
```

### 部署 Docker Image

```bash
# 开发环境
docker stack deploy -c docker-compose.yml future-trading-dev
docker stack rm future-trading-dev

# 调试环境
docker stack deploy -c docker-compose-debug.yml ft-debug
docker stack rm ft-debug

# 回测环境
docker stack deploy -c docker-compose-backtest.yml bottom-trade-backtest
docker stack rm bottom-trade-backtest

# 测试环境
docker stack deploy -c docker-compose-test.yml ft-test
docker stack rm ft-test

# 生产环境
docker stack deploy -c docker-compose-prod.yml bottom-trade
docker stack rm bottom-trade

# 特殊环境
docker stack deploy -c docker-compose-young.yml bottom-trade-young
docker stack rm bottom-trade-young
```

### 回测环境的使用步骤

1. 首先使用`docker-compose-backtest-db.yml`部署回测数据库主机

    ```bash
    docker stack deploy -c docker-compose-backtest-db.yml bottom-backtest-db
    ```

2. 修改`conf/trade_config_backtest.yaml`中需要进行回测的品种的，使用`docker-compose-backtest.yml`加不同名称为每个品种部署回测环境。

    ```bash
    docker stack deploy -c docker-compose-backtest.yml bottom-backtest-1
    ```

3. 在日志中找到并记录每个回测环境使用的数据库名称，使用以下命令将结果导出到excel文件。

    ```bash
    python generate_excel.py -p 26016 -n DB_NAME 
    ```
