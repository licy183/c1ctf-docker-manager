# c1tf-docker-manager

## 快速部署

1. 修改config.py的相关配置
```
    DISK_IP = '192.168.193.129'                         # 存储服务器的ip地址
    DB_URL = 'sqlite://:memory:'                        # 数据库地址
    NODE_MAP = {
        'xxxxx': '192.168.193.129'  # docker节点的ip对应关系
    }
```

2. 上传整个项目至服务器，假设上传至/opt/docker-manager

3. 上传项目需要的docker-compose文件至/opt/docker-manager/data/compose，同时在各个节点build所有需要的Dockerfile

### 测试环境是否正常

4. 构建测试镜像

```
    cd /opt/docker-manager/data/compose/test
    docker-compose build
```

5. 测试环境是否正常

```
    docker-compose run --rm --entrypoint python3 c1ctf-docker-manager /docker-manager/test.py
```
等待一段时间，如果看到如下提示时，可以访问对应网址，确认能否查看对应的flag，例如访问http://192.168.193.129:30008/test.php，确定能否看到flag

6. 启动服务
```
    docker-compose up 
```
