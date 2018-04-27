
import requests
import json
import queue
import random


def get_ip_port_queue():
    r = requests.get('http://127.0.0.1:8000/?count=30')
    ip_ports = json.loads(r.text)
    # print(ip_ports)
    ip_port_queue = queue.Queue(30)
    for each in ip_ports:
        ip_port_queue.put(each[0] + ':' + str(each[1]))
    return ip_port_queue


def get_ip_port_tag_list():
    r = requests.get('http://127.0.0.1:8000/?count=40')
    ip_port = json.loads(r.text)
    ip_port_list = []
    for each in ip_port:
        ip_port_list.append(each[0] + ':' + str(each[1]))
    return ip_port_list


def get_ip_port_list():
    r = requests.get('http://127.0.0.1:8000/?count=40')
    ip_port = json.loads(r.text)
    ip_port_list = []
    for each in ip_port:
        ip_port = each[0] + ':' + str(each[1])
        tag = 0
        ip_port_list.append([ip_port, tag])
    # ip_port_list.append('')  # 这个空字符串是为了使用本机代理
    return ip_port_list


if __name__ == '__main__':
    get_ip_port_list()
