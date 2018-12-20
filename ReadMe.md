# 解析 SSR 订阅地址内容
## 基本功能
```
usage parse.py -s subscribe_url [OPTION]...
options
-l                  show server list. 显示服务器节点
-d                  run ss-local as dameon. 以 daemon 运行 ss-local
-u                  update subscribe. 更新订阅
-p                  local port	设置端口 (仅在 ss-local) 运行下有效
-n                  server name  查找指定节点 生成 json
```

自定义配置 ( parse.py 中修改地址)

```python
_CONFIG = {}
_CONFIG['subscribe_url'] = '机场订阅地址'
```

默认所有服务器的 json 会保存在
```python
_CONFIG['servers_path'] = '/usr/local/etc/ssr_AXF_servers.json'
```

### 显示服务器所有节点
```shell
rt@dell parse.py -l
parsing list.
http://bala.bala.bala
剩余流量：99.52% 1.33TB
过期时间：2019-2-21 00:37:13
V3-深圳香港CN2
...
```

### 生成某一个服务器节点的 json
```
rt@dell parse.py -n V3-深圳香港CN2
searching V3-深圳香港CN2
{
    "node_name": "xxx",
    "server": "xxx",
    "local_address": "xx",
    "local_port": xx,
    "timeout": x,
    "workers": x,
    "server_port": x,
    "protocol": "x",
    "method": "x",
    "obfs": "x",
    "password": "x",
    "obfs_param": "x",
    "protocol_param": "x"
}
```

### 更新订阅内容
```shell
rt@dell parse.py -u
retrive data from url....
retrive ok.
beging parsing....
剩余流量：99.52% 9.33TB 过期时间：2011-11-21 00:37:13
```
