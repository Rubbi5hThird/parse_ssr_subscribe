#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2012-2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from flask import Flask
from flask import request
from urllib.request import urlopen
import base64, requests
import re, os, json, getopt, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
import ssr_dameon, subprocess
import urllib.parse

SSR_PATTERN = re.compile("ssr://(.*)")
# "\(serverHost):\(serverPort):\(ssrProtocol):\(method):\(ssrObfs):"
FIRST_PATTERN = re.compile("(.*):(.*):(.*):(.*):(.*):(.*)/\\?")
# obfsparam={base64(混淆参数(网址))}&protoparam={base64(混淆协议)}
# &remarks={base64(节点名称)}&group={base64(分组名)})
SECOND_PATTERN = re.compile(".*obfsparam=(.*)&protoparam=(.*)&remarks=(.*)&group=(.*)")

HTTP_PATTERN = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

_CONFIG = {}
_CONFIG['subscribe_url'] = 'your_url'
_CONFIG['servers_path'] = '/usr/local/etc/ssr_AXF_servers.json'
_CONFIG['ssr_config_path'] = '/usr/local/etc/ssr_AXF_config.json'
_CONFIG['daemon'] = ''
_CONFIG['pid-file'] = _CONFIG.get('pid-file', "/usr/local/var/run/ssr_AXF.pid")
_CONFIG['log-file'] = _CONFIG.get('log-file', "/usr/local/var/log/ssr_AXF.log")
_CONFIG['server_name'] = 'balabala'
_CONFIG['local_port'] = 2222
_CONFIG['local_address'] = '127.0.0.1'
_CONFIG['timeout'] = 300
_CONFIG['workers'] = 1

def notify(title, text):
    os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format(text, title))

def decode_base64(string):
    pad_n = (4 -  (len(string) % 4)) % 4
    string += '=' * pad_n
    return base64.urlsafe_b64decode(string.encode('ascii')).decode('utf-8')

def get_param(url, config):
    param = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    key = {'obfsparam' : 'obfs_param', 'protoparam' : 'protocol_param', 'remarks' : 'remarks', 'group' : 'group'}
    for k,v in key.items():
        if param.get(k) != None:
            config[v] = decode_base64(param[k][0].replace('-', '+').replace('_', '/'))

def parse_feed(url):
    print("retrive data from url....");
    proxies = {"http": None, "https": None,}

    response = requests.get(url, timeout = 3, proxies = proxies)
    if response.ok:
        print("retrive ok.")
        content = decode_base64(response.text)
    else:
        print("retrive failed.")
        return None
    print("beging parsing....");
    # mock
    servers = content.split("\n");
    config = {}
    config['server'] = ""
    config['server_port'] = ""
    config['protocol'] = ""
    config['method'] = ""
    config['obfs'] = ""
    config['password'] = ""
    config['obfs_param'] = ""
    config['protocol_param'] = ""
    config['remarks'] = url
    config['group'] = ""
    list_config = [config]
    for server in servers:
        if len(server) != 0 :
            match = SSR_PATTERN.match(server)
            if match != None:
                url = decode_base64(match.group(1))
                config = {}
                #TODO use one pattern
                first_match = FIRST_PATTERN.match(url)
                if first_match == None:
                    continue
                config['server'] = first_match.group(1)
                config['server_port'] = first_match.group(2)
                config['protocol'] = first_match.group(3)
                config['method'] = first_match.group(4)
                config['obfs'] = first_match.group(5)
                config['password'] = decode_base64(first_match.group(6))
                get_param(url, config)
                list_config.append(config)
    return list_config


def save_servers_to_json(data, dest):
    if len(data) == 0:
         return False
    try:
        with open(dest, "w") as fp:
            fp.write(json.dumps(data, sort_keys = False, indent = 4, ensure_ascii = False))
            return True
    except IOError as e:
        print("write json file failed. (%s)", e)
    return False

def check_file_exits(conf):
    url = conf['subscribe_url']
    path = conf['servers_path']
    if os.path.exists(path):
        data = None
        try:
            with open(path, "r") as fp:
                data = json.load(fp)
        except ValueError as e:
            print("open json file failed, please check the path " + path + e);
        if len(data) != 0 and data[0]['remarks'] != url:
            data = parse_feed(url);
            if data != None:
                return save_servers_to_json(data, path)
            return False
    else:
        data = parse_feed(url);
        if data != None:
            return save_servers_to_json(data, path)
        return False
    return True

def display_all_server_nodes(conf):
    print("parsing list.")
    if check_file_exits(conf) == False:
        return
    try:
        with open(conf['servers_path'], "r") as fp:
            data = json.load(fp)
    except ValueError as e:
        print("open json file failed" + e);
    for s in data:
        print(s['remarks'])

def gen_json_config_by_server_name(conf):
    name = conf['server_name']
    s_path = conf['servers_path']
    dest = conf['ssr_config_path']
    print('searching ' + name);
    if not check_file_exits(conf):
        return False
    with open(s_path, "r") as fp:
        data = json.load(fp)
    for s in data:
        if (s['remarks'] == name):
            local_json = {}
            local_json['node_name'] = s['group'] + " -> " + s['remarks']
            local_json['server'] = s['server']
            local_json['local_address'] = conf['local_address']
            local_json['local_port'] = conf['local_port']
            local_json['timeout'] = conf['timeout']
            local_json['workers'] = conf['workers']
            local_json['server_port'] = int(s['server_port'])
            local_json['protocol'] = s['protocol']
            local_json['method'] = s['method']
            local_json['obfs'] = s['obfs']
            local_json['password'] = s['password']
            local_json['obfs_param'] = s['obfs_param']
            local_json['protocol_param'] = s['protocol_param']
            s_conf = json.dumps(local_json, sort_keys = False, indent = 4, ensure_ascii = False)
            print(s_conf)
            # try:
            #     with open(dest, "w") as f:
            #         f.write(s_conf)
            #         print('write ' + name + " to " + dest)
            # except ValueError as e:
            #     print("get server name failed. " + e)
            #     return False
            return True
    return False

# you should change by your purchased serve.
def display_server_status_regen_config(conf):
    sub_url = conf['subscribe_url']
    data = parse_feed(sub_url)
    if len(data) >= 2:
        # get first two server remarks.
        state = data[1]['group'] + data[1]['remarks'] + " " + data[2]['remarks']
        notify(data[1]['group'], data[1]['remarks'] + " " + data[2]['remarks'])
        print(state)
        save_servers_to_json(data, conf['servers_path'])
    else:
        notify('Error.', 'check your network and subscript url.')

def run_ss_local_as_daemon(conf):
    if not check_file_exits(conf):
        print('gen config failed. check your network and dir permission.')
    if gen_json_config_by_server_name(conf):
        print('start ss-local dameon.')
        ssr_dameon.daemon_exec(conf)
        subprocess.call("ss-local -c " + conf['ssr_config_path'], shell=True)
        print('end')
    else:
        print('failed to start daemon.');


def print_help():
    print('''usage parse.py -s subscribe_url [OPTION]...
options
-l                  show server list.
-d                  run ss-local as dameon.
-u                  update subscribe.
-p                  local port
-n                  server name
    '''
    )

def main(argv):
    shortopts = 'hlus:d:p:n:'
    try:
       opts, args = getopt.getopt(argv, shortopts, [])
    except getopt.GetoptError:
        print("get opt error")
        print_help()
        sys.exit(2)
    ls = False
    ud = False
    fg = False
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-s"):
            if not re.match(HTTP_PATTERN, arg):
                print("invalid url.")
                sys.exit(2)
            _CONFIG['subscribe_url'] = arg
        elif opt in ("-l"):
            ls = True
        elif opt in ('-u'):
            ud = True
        elif opt in ('-n'):
            _CONFIG['server_name'] = arg
            if len (arg) == 0 or gen_json_config_by_server_name(_CONFIG):
                sys.exit(2)
            fg = True
        elif opt in ('-d'):
            _CONFIG['daemon'] = arg
            if arg != 'restart' and arg != 'stop' and arg != 'start':
                print('invalid daemon args (restart|stop|start)')
                sys.exit()
        elif opt in ('-p'):
            _CONFIG['local_port'] = int(arg)
    if ls:
        display_all_server_nodes(_CONFIG)
        sys.exit()
    if ud:
        display_server_status_regen_config(_CONFIG)
        sys.exit()
    if _CONFIG['daemon'] != '':
        print(_CONFIG['daemon'] + " ss-local daemon")
        run_ss_local_as_daemon(_CONFIG)
    # run ss-local as fg service
    # if fg:
    #     os.system('killall ss-local')
    #     gen_json_config_by_server_name(_CONFIG)
    #     os.system('/usr/local/bin/ss-local -c ' + _CONFIG['ssr_config_path'])
    #     sys.exit(0)


if __name__ == "__main__":
   main(sys.argv[1:])

