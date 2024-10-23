# api说明文档

所有参数为json格式，所有时间采用iso标准如：`2020-11-14T02:38:10.732108+00:00`

## 环境说明

将为每个用户创建单独的docker network，不同用户(uid)之间的容器不互通；

系统会为每个uid_challengeid新建一个flag目录，并挂载到docker-compose中包含"flag"字样的volume

每30秒回收一次过期的容器环境。

### 常量说明

status字段的含义如下：

```
          -1    # 程序运行出现错误
CREATING = 0    # 容器创建请求提交成功，正在创建环境
CREATED = 1     # 容器环境已创建完毕
ERROR = 2       # 容器环境创建失败
DELETED = 3     # 容器环境已被回收
```
### docker-compose说明

请将docker-compose.yaml放置data/compose目录下

注意docker-compose的创建任务可能会分配到不同节点，因此，不要出现`volumes: \n - ./:/example`，请尽量将所需文件在dockerfile中COPY

运行程序前，确定在每个node节点拥有所有的image镜像，可以在所有节点使用docker-compose build

示例docker-compose

```yaml
version: "3"
services:
  test:
    # container_name:          # 不要指定 container_name
    image: test:1.0.0          # 镜像名必填，要指定版本号
    build: "."
    ports:                     # 一个环境只能有一个暴露的端口
      - target: 80
        protocol: tcp          
        # published            # 不要指定外部端口，由系统随机分配      
    restart: always
    volumes:
      - flag-test-a34c:/flag   # 在容器内部，cat /flag/flag可以获得flag，如果不需要动态flag，该部分可省
  # test2:                     # 可以在一个环境中启动多个容器
    # image: test:1.0.0   
    # restart: always

volumes:
  flag-test-a34c:             # 希望动态生成flag的volume必须包含flag字样，同时保证名称不与其他题目重复 

```

## api说明

### 创建容器环境

URL：`/env/create`

请求方法：`POST`

参数列表

```    
uid = IntegerField([InputRequired()])           # 申请容器用户的uid
challenge = IntegerField([InputRequired()])     # 申请容器的题目id
compose_file = StringField([InputRequired()])   # docker-compose所在目录
flag = StringField()                            # flag，可空，如不为空，将新建flag文件然后挂载至docker-compose中名称包含”flag"的volume
expire = ISODateTimeField()                     # 环境过期时间，可空，若空，默认为当前时间+1小时
```                  

访问示例：

```shell script
curl -X "POST" -H "Content-Type: application/json"                            \
-d '{"uid": "1", "challenge": 11,"compose_file": "test/docker-compose.yaml",' \
' "flag": "flag{test2020}","expire": "2020-11-14T02:38:10.732108+00:00"}'     \
 http://192.168.139.129:5000/env/create
```

返回示例

```json
{"status": 0, "id": 1}
```

`status:0`表示创建请求已提交

`id:1`表示环境id为1，可以根据这id查询容器状态

### 查询容器环境状态
URL：`/env/get/<int:env_id>`

请求方法：`GET`

参数说明：`env_id`是创建得到的容器环境id，类型为整数型

请求示例：

```shell script
curl http://192.168.192.129:5000/env/get/1
```
返回示例（三种不同情况的响应）

正在分配节点
```json
{"expire":"2020-11-14T04:09:49.767094+00:00","id":1,"node_ip":null,"node_port":null,"status":0}
```
已分配节点，正在创建容器
```json
{"expire":"2020-11-14T04:09:49.767094+00:00","id":1,"node_ip":"192.168.193.129","node_port":30000,"status":0}
```
容器创建完成
```json
{"expire":"2020-11-14T04:09:49.767094+00:00","id":1,"node_ip":"192.168.193.129","node_port":30000,"status":1}
```
创建过程中，每次发起请求获得的环境的参数可能会不断更新，直至最后status变为CTEATED = 1

### 环境续期

URL：`/env/renew/<int:env_id>`

请求方法：`POST`

请求示例：
```shell script
curl -X "POST" -H "Content-Type: application/json" \
-d '{"expire":"2020-11-14T04:09:49.767094+00:00"}' \
 http://192.168.192.129:5000/env/renew/1
```

请求参数

```python
expire = ISODateTimeField()                     # 环境过期时间，可空，若空，默认为当前时间+1小时 
```

返回示例：

```json
{"expire":"2020-11-14T04:09:49.767094+00:00","status":1}
```

expire为更新后的返回时间

如果环境状态不正常，则会返回

```json
{"status": -1}
```
### 删除环境

URL：`/env/delete/<int:env_id>`

请求方法：`GET`

请求示例：

```
curl -X "GET" http://192.168.192.129:5000/env/delete/1
```

返回示例

```json
{"status":3}
```

status = 3标识环境状态已切换至DELETED

### 列出所有环境状态

URL：`/env/list`

请求方法：`GET`

请求示例：
```
curl -X "GET" http://192.168.192.129:5000/env/list
```

返回示例
```json
[{"expire":"2020-11-14T04:09:49.767094+00:00","id":1,"node_ip":null,"node_port":null,"status":0}]
```
