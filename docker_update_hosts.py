#!/usr/bin/python3


import docker
client = docker.from_env()
import platform
import json
import re
import io

def parse_hostsfile(path='/etc/hosts'):
    f = open(path,'r')
    r = f.readline()
    hosts_by_ip = {}
    while r != '':
        if not re.match("^\s*#",r):
            chunks = re.split("\s+",r.replace("\n","").replace("\r",""))
            ip = chunks[0]
            if ip != "":
                hosts = []
                if ip in hosts_by_ip.keys():
                    hosts = hosts_by_ip[ip]
                hosts_by_ip[ip] = hosts + chunks[1:]
        r = f.readline()
    f.close()
    return hosts_by_ip

def write_hostsfile(hostmapping, path='/etc/hosts'):
    f = open(path,'r')
    fn = open(path + "-docker-update-hosts", 'w')
    r= f.readline()
    in_chunk = False
    chunk_found = False
    while r != "":
        if not in_chunk:
            fn.write(r)
            if re.match("\s*#DOCKER_UPDATE_HOSTS_START",r):
                in_chunk = True
                fn.write(format_for_hostsfile(hostmapping))
                chunk_found = True
        if in_chunk:
            if re.match("\s*#DOCKER_UPDATE_HOSTS_END",r):
                in_chunk = False
                fn.write(r)
        r= f.readline()
    f.close()
    fn.close()
    if not chunk_found:
        print("not updating hostsfile, i did not find the two necessary commpents #DOCKER_UPDATE_HOSTS_START and #DOCKER_UPDATE_HOSTS_END")
    else:
        import shutil
        shutil.move(path+"-docker-update-hosts",path)
        print("updated")


def hostmapping_ipbyhost(hostbyip):
    ip_by_host = {}
    for k,v in hostbyip.items():
        for h in v:
            ip_by_host[h] = k
    return ip_by_host


def format_for_hostsfile(dockermapping):
    it = list(dockermapping.items())
    it.sort(key=lambda x: x[0])
    res = ""
    for k,v in it:
        res += "%s\t%s\n" % (k, " ".join(v))
    return res

def has_missing_data(tobe_mapping,asis_mapping):
    asis_inv = hostmapping_ipbyhost(asis_mapping)
    tobe_inv  = hostmapping_ipbyhost(tobe_mapping)
    for h in tobe_inv.keys():
        if not h in asis_inv.keys():
            return "missing host %s" % h
        if tobe_inv[h] != asis_inv[h]:
            return "wrong mapping %s => %s instead of %s" % (h, asis_inv[h], tobe_inv[h])
    return False


def get_hosts(client,suffix='docker.local'):
    hosts_by_ip = {}
    res = ""
    for k in client.containers():
        id = k['Id']
        hostlist = []
        #hostlist.append("%s.%s" % (id, suffix))
        hostconfig = k['HostConfig']['NetworkMode']
        if not hostconfig in k['NetworkSettings']['Networks'] and not 'bridge' in k['NetworkSettings']['Networks']:
            continue
        if 'bridge' in k['NetworkSettings']['Networks']:
            hostconfig='bridge'
        net = k['NetworkSettings']['Networks'][hostconfig]
        ip = net['IPAddress']
        labels = k['Labels']
        if 'com.docker.compose.service' in labels:
            lc = labels['com.docker.compose.container-number']
            ls = labels['com.docker.compose.service']
            lp = labels['com.docker.compose.project']
            hostlist.append('%s.%s.%s.%s' % (lc,ls,lp,suffix))
        for zn in k['Names']:
            n = zn.replace('/','')
            hostlist.append(n + '.' + suffix)
        hosts_by_ip[ip] = hostlist
    return hosts_by_ip
        
def update_hostsfile(tobe):
    asis = parse_hostsfile()
    if has_missing_data(tobe,asis):
        print(has_missing_data(tobe,asis))
        print()
        print(format_for_hostsfile(tobe))
        write_hostsfile(tobe)

update_hostsfile(get_hosts(client))

for k in client.events():
    dct = json.loads(k.decode('UTF-8'))
    if not dct['Type'] == 'container':
        continue
    if not 'status' in dct or not dct['status'] in ('start','stop','die'):
        continue
    print("got event %s\n\n" % dct)
    
    update_hostsfile(get_hosts(client))
    
    