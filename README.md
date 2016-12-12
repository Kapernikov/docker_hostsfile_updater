## Overview

Small python daemon that writes an entry in /etc/hosts for every running docker
container. Goal is to provide a lightweight alternative for service
discovery (like skydns) that also works on the host without having change
DNS configuration.

A script modifying /etc/hosts is only feasible for smaller setups, but it
has the advantage that when the script exits / crashes, resolving DNS names
on the host keeps working.

The script adds `[containerlabel].docker.local` hostnames, but for containers launched using docker-compose, extra hostnames are generated: `[number].[service].[group].docker.local` (see below for an example).

## How to

* make sure you have python 3 (/usr/bin/python3 in most linux distributions). The daemon does not work (yet) on python2, fixing this would be trivial.
* first install the script using python3 setup.py install
* then edit the /etc/hosts file, and add the following 2 lines (the script
  will only touch the section between these lines, and if the lines don't
  exist, the script will not touch /etc/hosts

```
#DOCKER_UPDATE_HOSTS_START
#DOCKER_UPDATE_HOSTS_END

```
## Command line arguments

 * '-n','--no-daemon' : do not run as a daemon but keep running in the foreground
 * '-o','--once' : run once (updating /etc/hosts if needed) and exit (eg for running as a cron job)
 * '-d','--debug' : run in foreground and do not log to syslog but stdout (and be more verbose)
 * '-p','--pidfile' : write a pid file (default: '/tmp/docker_update_hosts.pid')

## Example

running docker_hostsfile_updater with a docker_compose redmine/mariadb like
this:

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
b630dab77b8d        redmine_redmine     "/docker-entrypoint.s"   10 days ago         Up 4 days           0.0.0.0:8080->3000/tcp   redmine_redmine_1
be3079da2e4f        mariadb             "docker-entrypoint.sh"   10 days ago         Up 4 days           3306/tcp                 redmine_db_1
```

will result in the following /etc/hosts:

```
127.0.0.1	localhost

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

#DOCKER_UPDATE_HOSTS_START
172.19.0.2	1.redmine.redmine.docker.local redmine_redmine_1.docker.local
172.19.0.3	1.db.redmine.docker.local redmine_db_1.docker.local
#DOCKER_UPDATE_HOSTS_END

```
