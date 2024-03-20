# Необходимо создать аналог утилиты MTR с помощью Scapy.

Результат - файл программы на Python с описанием как запустить файл. Из зависимостей достаточно Scapy, при желании можно приложить requirements.txt

MTR: https://www.cloudflare.com/ru-ru/learning/network-layer/what-is-mtr/

Scapy: https://scapy.readthedocs.io/en/latest/usage.html

Программа на 100 баллов должна уметь:

    собрать статистику по каждому hop-у, достаточно будет число потерь пакетов;
    уметь выбирать IPv4 или IPv6;
    уметь выбирать TCP/UPD/ICMP;

Программа на 50 баллов эмулирует работу ping.

Программа на 75 баллов эмулирует работу traceroute - без статистики, выбора протокола, etc.

Работа со scapy:

```
dig AAAA ya.ru
python3 -m venv scapy_venv
. ./scapy_venv/bin/activate
pip install scapy
sudo -E scapy_venv/bin/python
i=IPv6()
i.dst="2a02:6b8::2:242"
q=ICMPv6EchoRequest()
p=(i/q)
sr1(p)
```

Вывод:

```
Begin emission:
Finished sending 1 packets.
...*
Received 4 packets, got 1 answers, remaining 0 packets
<IPv6  version=6 tc=96 fl=0 plen=8 nh=ICMPv6 hlim=55 src=2a02:6b8::2:242 dst=2a02:6b8:c07:88c:0:696:9091:0 |<ICMPv6EchoReply  type=Echo Reply code=0 cksum=0x6f4a id=0x0 seq=0x0 |>>
```

Примерный вывод команды mtr ya.ru:


```
                                            My traceroute  [v0.93]
speedwagon-dev.sas.yp-c.yandex.net (2a02:6b8:c07:88c:0:696:9091:0)                    2023-04-26T18:34:15+0300
Keys:  Help   Display mode   Restart statistics   Order of fields   quit
                                                                      Packets               Pings
 Host                                                               Loss%   Snt   Last   Avg  Best  Wrst StDev
 1. 2a02:6b8:c07:88c:0:43e9:856d:0                                   0.0%     8    0.2   0.2   0.1   0.3   0.0
 2. 2a02:6b8:c07:88c::badc:ab1e                                      0.0%     8    0.3   0.2   0.2   0.3   0.0
 3. 2a02:6b8:c07:880::1                                              0.0%     7    2.0   3.0   1.8   5.9   1.5
 4. 2a02:6b8:c02:b33::1                                              0.0%     7    2.2   2.4   1.8   4.3   0.9
 5. (waiting for reply)
 6. fd00:11:aa:3:0:2:20:2                                            0.0%     7    0.5   0.5   0.5   0.6   0.1
 7. fd00:11:aa:3:0:1:32:2                                            0.0%     7    9.9   3.0   1.4   9.9   3.1
 8. (waiting for reply)
 9. (waiting for reply)
10. ya.ru                                                            0.0%     7    0.4   0.7   0.4   0.8   0.2
```