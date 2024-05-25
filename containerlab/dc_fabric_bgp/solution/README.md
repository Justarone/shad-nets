# Лабораторная работа 4: Конфигурация IP-фабрики в ЦОД на основе протокола BGP

## по заданию

> 1. Подготовить файлы конфигурации

подготовил

> 2. Настроить на всех устройствах IP-адреса согласно схеме. Router ID - RID, - это адрес lo интерфейса.

сразу делал скрипт, отлаживая руками расхождения на отдельных контейнерах

в этой лабораторной я сделал настройку IP-адресов через маппинг в конфиге:

```json
{
    ...
    "ips": {
        "PC1": {
            "lo": "10.0.254.7",
            "eth1": "172.16.11.1"
        },
        "PC2": {
            "lo": "10.0.254.8",
            "eth1": "172.16.22.1"
        },
        "leaf1": {
            "lo": "10.0.254.5",
            "eth1": "172.16.112.2",
            "eth2": "172.16.111.2",
            "eth3": "172.16.11.2",
            "eth4": "172.16.113.2",
            "eth5": "172.16.114.2"
        },
        ...
    }
    ...
}
```

далее скрипт генерирует для присваивания адресов интерфейсам команды вида:

```
! interface = {lo, ethX}
int {interface}
! для lo - subnet=32
ip addr X.X.X.X/30
exit
```

> 3. Проверить IP-связность между всеми парами устройств через прямые линки. Пинг должен быть успешным везде.

в конфиге добавил настройку `only_direct`, прямые пинги работают на соответствующие интерфейсы соседа, на `lo` не работает
```
RUNNING ping: from=spine2, to=leaf1 (172.16.112.2)
success!
RUNNING ping: from=spine1, to=leaf1 (172.16.111.2)
success!
RUNNING ping: from=spine3, to=leaf1 (172.16.113.2)
success!
RUNNING ping: from=spine4, to=leaf1 (172.16.114.2)
success!
RUNNING ping: from=PC1, to=leaf1 (172.16.11.2)
success!
RUNNING ping: from=leaf1, to=spine2 (172.16.112.1)
success!
RUNNING ping: from=leaf2, to=spine2 (172.16.222.1)
success!
RUNNING ping: from=leaf1, to=spine1 (172.16.111.1)
success!
RUNNING ping: from=leaf2, to=spine1 (172.16.221.1)
success!
RUNNING ping: from=leaf1, to=spine3 (172.16.113.1)
success!
RUNNING ping: from=leaf2, to=spine3 (172.16.223.1)
success!
RUNNING ping: from=leaf1, to=spine4 (172.16.114.1)
success!
RUNNING ping: from=leaf2, to=spine4 (172.16.224.1)
success!
RUNNING ping: from=spine2, to=leaf2 (172.16.222.2)
success!
RUNNING ping: from=spine1, to=leaf2 (172.16.221.2)
success!
RUNNING ping: from=spine3, to=leaf2 (172.16.223.2)
success!
RUNNING ping: from=spine4, to=leaf2 (172.16.224.2)
success!
RUNNING ping: from=PC2, to=leaf2 (172.16.22.2)
success!
RUNNING ping: from=leaf1, to=PC1 (172.16.11.1)
success!
RUNNING ping: from=leaf2, to=PC2 (172.16.22.1)
success!
```

> 4. Убедиться, что на устройствах нет ни статической, ни динамической (ISIS) маршрутизации

проверим текущее состояние таблиц маршрутизации на нодах:
```
RUNNING NODE=leaf1, VTYSH COMMAND="sh ip route".....
K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:08:45
C>* 10.0.254.5/32 is directly connected, lo, 00:08:26
C>* 172.16.11.0/30 is directly connected, eth3, 00:08:26
C>* 172.16.111.0/30 is directly connected, eth2, 00:08:26
C>* 172.16.112.0/30 is directly connected, eth1, 00:08:26
C>* 172.16.113.0/30 is directly connected, eth4, 00:08:26
C>* 172.16.114.0/30 is directly connected, eth5, 00:08:26
C>* 172.20.20.0/24 is directly connected, eth0, 00:08:45
RUNNING NODE=spine2, VTYSH COMMAND="sh ip route".....
K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:08:44
C>* 10.0.254.2/32 is directly connected, lo, 00:08:26
C>* 172.16.112.0/30 is directly connected, eth1, 00:08:26
C>* 172.16.222.0/30 is directly connected, eth2, 00:08:26
C>* 172.20.20.0/24 is directly connected, eth0, 00:08:45
RUNNING NODE=PC1, VTYSH COMMAND="sh ip route".....
K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:08:44
C>* 10.0.254.7/32 is directly connected, lo, 00:08:25
C>* 172.16.11.0/30 is directly connected, eth1, 00:08:25
C>* 172.20.20.0/24 is directly connected, eth0, 00:08:44
...
```

пс: вывод сокращен по 1 на каждый тип устройств - в остальных устройствах присутствуют тоже только Kernel и Connected пути, статической и динамической маршрутизации нет

> 5. Настроить маршрутизацию по протоколу eBGP (IPv4 Unicast AFI), используя номера ASN со схемы и схему пиринга, каждое устройство должно анонсировать в eBGP только свою локальную подсеть (lo интерфейс)

шаблон конфига для настройки маршрутизации:

```
! permit-filter по префиксу (https://docs.frrouting.org/en/latest/filter.html#ip-prefix-list)
ip prefix-list DC_LOCAL_SUBNET seq 5 permit 172.16.0.0/16 le 32
ip prefix-list DC_LOCAL_SUBNET seq 10 permit 10.0.254.0/24 le 32
! route-map - в нашем случае permit префиксов адресов нашей фабрики (https://docs.frrouting.org/en/latest/routemap.html#route-map-command)
! этот route-map будет использоваться для фильтрации адресов, которые мы будем распространять в BGP от других протоколов
route-map ACCEPT_DC_LOCAL permit 10
match ip address prefix-list DC_LOCAL_SUBNET
exit
! пустой route-map permit позволяет разрешает все на вход и все на выход
route-map PERMIT_EBGP permit 10
exit
! https://docs.frrouting.org/en/latest/bgp.html
router bgp ASN
    ! если не задать, то выберется автоматически, как
    ! наибольший ip адрес ноды, если zebra доступна, 0.0.0.0 иначе, не рекомендуется
    bgp router-id LO-IP
    ! создание группы для общей конфигурации
    neighbor FABRIC peer-group
    ! добавляем все интерфейсы в группу FABRIC для более простой конфигураци
    neighbor {interface} interface peer-group FABRIC
    ! все соседи из группы по eBGP (если ASN будет совпадать - ошибка)
    neighbor FABRIC remote-as external
    address-family ipv4 unicast
        ! "Redistribute routes from other protocols into BGP."
        ! только connected адреса, удовлетворящие фильтру route-map ACCEPT_DC_LOCAL
        ! если это не задать - то нечем будет обмениваться (у нас изначально только C/K, см. выше)
        redistribute connected route-map ACCEPT_DC_LOCAL
        ! если не настроить политики, то по умолчанию deny, я проверил
        ! при этом если сделать route-map, в котором только loopback адреса, 
        ! и задать в этих строчках, то распространятся только они
        neighbor FABRIC route-map PERMIT_EBGP in
        neighbor FABRIC route-map PERMIT_EBGP out
    exit-address-family
exit
```

примечание: эта конфигурация делает больше, чем нужно - потому что в распространяются не только lo адреса, но еще и другие, которые подходят под `DC_LOCAL_SUBNET`. я оставил такую конфигурацию, чтобы проще было проверять пинги на все возможные адреса полным перебором, можно модифицировать эту конфигурацию и получить распространение по eBGP только lo адресов, достаточно сделать 1 из 3 действий (желательно все 3, чтобы явно обозначить намерение):
* пусть есть фильтр `ip prefix-list LO_ONLY seq 10 permit 10.0.254.0/24 le 32` и соответствующий ему `match ip ... permit` route-map
1. можно добавить этот route-map (с фильтром `LO_ONLY`) в redistribute секцию, тогда не lo адреса не будут использоваться для распространения в BGP в принципе
2. можно в `PERMIT_EBGP in` (или `out` - это 3ий вариант) политике задать такой route-map (с фильтром `LO_ONLY`), тогда не lo-адреса не будут приниматься (отдаваться)

> 6. Проверить IP-связность между lo интерфейсами РС1 и РС2

проверяем связность:
```
PC1# ping 10.0.254.8
PING 10.0.254.8 (10.0.254.8): 56 data bytes
64 bytes from 10.0.254.8: seq=0 ttl=61 time=0.127 ms
64 bytes from 10.0.254.8: seq=1 ttl=61 time=0.226 ms
PC1# traceroute 10.0.254.8
traceroute to 10.0.254.8 (10.0.254.8), 30 hops max, 46 byte packets
 1  172.16.11.2 (172.16.11.2)  0.010 ms  0.012 ms  0.003 ms
 2  172.16.111.1 (172.16.111.1)  0.002 ms  0.015 ms  0.003 ms
 3  172.16.222.2 (172.16.222.2)  0.003 ms  0.014 ms  0.003 ms
 4  10.0.254.8 (10.0.254.8)  0.003 ms  0.011 ms  0.003 ms
```

посмотрим таблицу маршрутизации:
```
PC1# sh ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:05:09
B>* 10.0.254.1/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 10.0.254.2/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 10.0.254.3/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 10.0.254.4/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 10.0.254.5/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 10.0.254.6/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:40
C>* 10.0.254.7/32 is directly connected, lo, 00:05:07
B>* 10.0.254.8/32 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:40
C>* 172.16.11.0/30 is directly connected, eth1, 00:05:07
B>* 172.16.22.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:40
B>* 172.16.111.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.112.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.113.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.114.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.221.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.222.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.223.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
B>* 172.16.224.0/30 [20/0] via 172.16.11.2, eth1, weight 1, 00:04:41
C>* 172.20.20.0/24 is directly connected, eth0, 00:05:09
```

здесь же из интересного - если посмотреть на таблицу маршрутизации leaf1 без опции `bgp bestpath as-path multipath-relax`:
```
leaf1# sh ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:00:13
B>* 10.0.254.1/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:08
B>* 10.0.254.2/32 [20/0] via 172.16.112.1, eth1, weight 1, 00:00:08
B>* 10.0.254.3/32 [20/0] via 172.16.113.1, eth4, weight 1, 00:00:08
B>* 10.0.254.4/32 [20/0] via 172.16.114.1, eth5, weight 1, 00:00:08
C>* 10.0.254.5/32 is directly connected, lo, 00:00:11
B>* 10.0.254.6/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:08
  *                      via 172.16.112.1, eth1, weight 1, 00:00:08
B>* 10.0.254.7/32 [20/0] via 172.16.11.1, eth3, weight 1, 00:00:08
B>* 10.0.254.8/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:08
  *                      via 172.16.112.1, eth1, weight 1, 00:00:08
C>* 172.16.11.0/30 is directly connected, eth3, 00:00:11
B>* 172.16.22.0/30 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:08
  *                       via 172.16.112.1, eth1, weight 1, 00:00:08
C>* 172.16.111.0/30 is directly connected, eth2, 00:00:11
C>* 172.16.112.0/30 is directly connected, eth1, 00:00:11
C>* 172.16.113.0/30 is directly connected, eth4, 00:00:11
C>* 172.16.114.0/30 is directly connected, eth5, 00:00:11
B>* 172.16.221.0/30 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:08
B>* 172.16.222.0/30 [20/0] via 172.16.112.1, eth1, weight 1, 00:00:08
B>* 172.16.223.0/30 [20/0] via 172.16.113.1, eth4, weight 1, 00:00:08
B>* 172.16.224.0/30 [20/0] via 172.16.114.1, eth5, weight 1, 00:00:08
C>* 172.20.20.0/24 is directly connected, eth0, 00:00:13
```

если добавить опцию, то получатся еще пути через ASN 65200:
```
leaf1# sh ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:00:59
B>* 10.0.254.1/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:56
B>* 10.0.254.2/32 [20/0] via 172.16.112.1, eth1, weight 1, 00:00:55
B>* 10.0.254.3/32 [20/0] via 172.16.113.1, eth4, weight 1, 00:00:55
B>* 10.0.254.4/32 [20/0] via 172.16.114.1, eth5, weight 1, 00:00:55
C>* 10.0.254.5/32 is directly connected, lo, 00:00:58
B>* 10.0.254.6/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:55
  *                      via 172.16.112.1, eth1, weight 1, 00:00:55
  *                      via 172.16.113.1, eth4, weight 1, 00:00:55
  *                      via 172.16.114.1, eth5, weight 1, 00:00:55
B>* 10.0.254.7/32 [20/0] via 172.16.11.1, eth3, weight 1, 00:00:55
B>* 10.0.254.8/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:55
  *                      via 172.16.112.1, eth1, weight 1, 00:00:55
  *                      via 172.16.113.1, eth4, weight 1, 00:00:55
  *                      via 172.16.114.1, eth5, weight 1, 00:00:55
C>* 172.16.11.0/30 is directly connected, eth3, 00:00:58
B>* 172.16.22.0/30 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:55
  *                       via 172.16.112.1, eth1, weight 1, 00:00:55
  *                       via 172.16.113.1, eth4, weight 1, 00:00:55
  *                       via 172.16.114.1, eth5, weight 1, 00:00:55
C>* 172.16.111.0/30 is directly connected, eth2, 00:00:58
C>* 172.16.112.0/30 is directly connected, eth1, 00:00:58
C>* 172.16.113.0/30 is directly connected, eth4, 00:00:58
C>* 172.16.114.0/30 is directly connected, eth5, 00:00:58
B>* 172.16.221.0/30 [20/0] via 172.16.111.1, eth2, weight 1, 00:00:56
B>* 172.16.222.0/30 [20/0] via 172.16.112.1, eth1, weight 1, 00:00:55
B>* 172.16.223.0/30 [20/0] via 172.16.113.1, eth4, weight 1, 00:00:55
B>* 172.16.224.0/30 [20/0] via 172.16.114.1, eth5, weight 1, 00:00:55
C>* 172.20.20.0/24 is directly connected, eth0, 00:00:59
```

и здесь же посмотрим пути, если делать по заданию, то есть только для lo (я как раз убирал из скрипта и по 1 опции, и сразу 3):
```
leaf1# sh ip route
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

K>* 0.0.0.0/0 [0/0] via 172.20.20.1, eth0, 00:01:22
B>* 10.0.254.1/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:01:18
B>* 10.0.254.2/32 [20/0] via 172.16.112.1, eth1, weight 1, 00:01:18
B>* 10.0.254.3/32 [20/0] via 172.16.113.1, eth4, weight 1, 00:01:18
B>* 10.0.254.4/32 [20/0] via 172.16.114.1, eth5, weight 1, 00:01:17
C>* 10.0.254.5/32 is directly connected, lo, 00:01:20
B>* 10.0.254.6/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:01:17
  *                      via 172.16.112.1, eth1, weight 1, 00:01:17
  *                      via 172.16.113.1, eth4, weight 1, 00:01:17
  *                      via 172.16.114.1, eth5, weight 1, 00:01:17
B>* 10.0.254.7/32 [20/0] via 172.16.11.1, eth3, weight 1, 00:01:17
B>* 10.0.254.8/32 [20/0] via 172.16.111.1, eth2, weight 1, 00:01:17
  *                      via 172.16.112.1, eth1, weight 1, 00:01:17
  *                      via 172.16.113.1, eth4, weight 1, 00:01:17
  *                      via 172.16.114.1, eth5, weight 1, 00:01:17
C>* 172.16.11.0/30 is directly connected, eth3, 00:01:20
C>* 172.16.111.0/30 is directly connected, eth2, 00:01:20
C>* 172.16.112.0/30 is directly connected, eth1, 00:01:20
C>* 172.16.113.0/30 is directly connected, eth4, 00:01:20
C>* 172.16.114.0/30 is directly connected, eth5, 00:01:20
C>* 172.20.20.0/24 is directly connected, eth0, 00:01:22
```

> 7. Написать скрипт на Python, генерирующий базовую и BGP конфигурацию для каждого устройства

части скрипта описаны выше, они не сильно менялись относительно лабораторной 2 (см. секцию "скрипты" [здесь](containerlab/dynamic_routing/solution/README.md)), сами скрипты лежат в директории ./scripts

> 8. Написать скрипт на Python, выводящий требуемые команды

аналогично п.7, но добавлены комманды для `ip bgp`

для них написан парсер, посмотрим на вывод команд с учетом парсера (по 1 для каждого типа устройств - pc/leaf/spine):
```
RUNNING NODE=leaf1, VTYSH COMMAND="sh ip bgp neighbors".....
Hostname: spine2
Nexthop: 172.16.112.2
Nexthop global: fe80::a8c1:abff:fea6:4911
Nexthop local: fe80::a8c1:abff:fea6:4911
Hostname: spine1
Nexthop: 172.16.111.2
Nexthop global: fe80::a8c1:abff:fe14:f87
Nexthop local: fe80::a8c1:abff:fe14:f87
Hostname: PC1
Nexthop: 172.16.11.2
Nexthop global: fe80::a8c1:abff:fe61:162
Nexthop local: fe80::a8c1:abff:fe61:162
Hostname: spine3
Nexthop: 172.16.113.2
Nexthop global: fe80::a8c1:abff:fe49:121d
Nexthop local: fe80::a8c1:abff:fe49:121d
Hostname: spine4
Nexthop: 172.16.114.2
Nexthop global: fe80::a8c1:abff:fed6:3530
Nexthop local: fe80::a8c1:abff:fed6:3530

RUNNING NODE=leaf1, VTYSH COMMAND="sh ip bgp summary".....
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
eth1            4      65000        61        62        0    0    0 00:30:39            3        8 N/A
eth2            4      65000        61        62        0    0    0 00:30:39            3        8 N/A
eth3            4      65100        66        60        0    0    0 00:30:38            1        8 N/A
eth4            4      65200        60        63        0    0    0 00:30:39            3        8 N/A
eth5            4      65200        60        63        0    0    0 00:30:39            3        8 N/A

Total number of neighbors 5




RUNNING NODE=spine2, VTYSH COMMAND="sh ip bgp neighbors".....
Hostname: leaf1
Nexthop: 172.16.112.1
Nexthop global: fe80::a8c1:abff:fe41:87b2
Nexthop local: fe80::a8c1:abff:fe41:87b2
Hostname: leaf2
Nexthop: 172.16.222.1
Nexthop global: fe80::a8c1:abff:fe35:fc3b
Nexthop local: fe80::a8c1:abff:fe35:fc3b

RUNNING NODE=spine2, VTYSH COMMAND="sh ip bgp summary".....
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
eth1            4      65001        62        61        0    0    0 00:30:39            4        7 N/A
eth2            4      65002        69        67        0    0    0 00:30:38            4        7 N/A

Total number of neighbors 2




RUNNING NODE=PC1, VTYSH COMMAND="sh ip bgp neighbors".....
Hostname: leaf1
Nexthop: 172.16.11.1
Nexthop global: fe80::a8c1:abff:fe6a:30d6
Nexthop local: fe80::a8c1:abff:fe6a:30d6

RUNNING NODE=PC1, VTYSH COMMAND="sh ip bgp summary".....
Neighbor        V         AS   MsgRcvd   MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd   PfxSnt Desc
eth1            4      65001        60        66        0    0    0 00:30:39            7        8 N/A

Total number of neighbors 1
```

> sh ip bgp (BGP таблица), на ее основе описать используемый AS PATH между РС1 и РС2. На РС1 и РС2 посмотреть маршрутную информацию о lo интерфейса другого lo (show ip bgp 10.0.254.5 и show ip bgp 10.0.254.6)

посмотрим с PC1 машрутную информацию о другом lo:
```
PC1# sh ip bgp 10.0.254.5
BGP routing table entry for 10.0.254.5/32, version 7
Paths: (1 available, best #1, table default)
  Advertised to non peer-group peers:
  eth1
  65001
    172.16.11.2 from eth1 (10.0.254.5)
      Origin incomplete, metric 0, valid, external, best (First path received)
      Last update: Sat May 25 12:00:17 2024
PC1# sh ip bgp 10.0.254.6
BGP routing table entry for 10.0.254.6/32, version 8
Paths: (1 available, best #1, table default)
  Advertised to non peer-group peers:
  eth1
  65001 65000 65002
    172.16.11.2 from eth1 (10.0.254.5)
      Origin incomplete, valid, external, best (First path received)
      Last update: Sat May 25 12:00:18 2024
```

видим, что до 10.0.254.5 (leaf1) AS-PATH=[65001], NH=172.16.11.2 (leaf1). для 10.0.254.6 (leaf2) NH тот же, но AS-PATH=[65001, 65000, 65002]. на PC2 симметричная картинка.

более интересно посмотреть на leaf1:

```
leaf1# sh ip bgp 10.0.254.6
BGP routing table entry for 10.0.254.6/32, version 9
Paths: (4 available, best #3, table default)
  Advertised to non peer-group peers:
  eth1 eth2 eth3 eth4 eth5
  65200 65002
    172.16.114.1 from eth5 (10.0.254.4)
      Origin incomplete, valid, external, multipath
      Last update: Sat May 25 12:00:18 2024
  65200 65002
    172.16.113.1 from eth4 (10.0.254.3)
      Origin incomplete, valid, external, multipath
      Last update: Sat May 25 12:00:18 2024
  65000 65002
    172.16.111.1 from eth2 (10.0.254.1)
      Origin incomplete, valid, external, multipath, best (Older Path)
      Last update: Sat May 25 12:00:18 2024
  65000 65002
    172.16.112.1 from eth1 (10.0.254.2)
      Origin incomplete, valid, external, multipath
      Last update: Sat May 25 12:00:18 2024
```

с опцией multipath он показывает 4 пути достижения - AS-PATH разные, но длина одинаковая, NH перебирает всех возможных spine.

### примечание

spine1 не может сделать ping на spine2, потому что:
1. они находятся в одной AS, поэтому информация по BGP не доходит от одного другому
2. они не подключены друг к другу напрямую (поэтому нет connected связи)

это ожидаемо - для маршрутизации внутри AS нужен IGP, в нашем случае связность между ними просто не нужна, потому что данные "ходят" в рамках сети иначе

при этом им общая AS назначена специально:
1. это удобно, когда у нас нет bestpath multipath-relax опции - тогда через эти spine пути будут считаться равными (с разными AS так бы не было)
2. нет смысла плодить лишние AS в сети, это усложняет систему (в данном случае они подключены к одинаковым AS, поэтому и распространять будут одинаковую информацию)
