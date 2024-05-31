import scapy
from scapy.all import *
from core import Response, Sender


logging.getLogger('scrapy').propagate = False


def is_icmp_expired(response):
    return ICMP in response and response.proto == 1 and response.type == 11 and response.code == 0 \
        or ICMPv6TimeExceeded in response


def not_valid(response):
    return any(map(lambda er: er in response, [IPerror, UDPerror, ICMPerror, TCPerror]))


class PacketSender(Sender):
    def __init__(self, l3factory, l4factory):
        self.L3Factory = l3factory
        self.L4Factory = l4factory

    def send(self, address, ttl=None) -> Response:
        packet = self.L4Factory(self.L3Factory(address, ttl))
        try:
            response = sr1(packet, timeout=2, verbose=0)
            if response is not None and is_icmp_expired(response):
                return Response(Response.TTL_EXCEEDED, response.src)
            elif response is None or not_valid(response):
                return Response(Response.NO_ANSWER, None)
            return Response(Response.SUCCESSFULLY_REACHED, response.src)
        except Exception as e:
            print(e)
            return Response(Response.NO_ANSWER, None)

        


def ipv6_packet_factory(dst, ttl=None):
    kwargs = {"dst": dst}
    if ttl is not None:
        kwargs["hlim"] = ttl
    return IPv6(**kwargs)


def ipv4_packet_factory(dst, ttl=None):
    kwargs = {"dst": dst}
    if ttl is not None:
        kwargs["ttl"] = ttl
    return IP(**kwargs)


def tcp_syn_packet_factory(l3packet, port):
    return l3packet/TCP(dport=port)


def icmp_packet_factory(l3packet, is_v6):
    return l3packet/(ICMP() if not is_v6 else ICMPv6EchoRequest())


def udp_dns_packet_factory(l3packet):
    return l3packet/UDP()/DNS(rd=1,qd=DNSQR(qname="ya.ru"))


def raw_udp_packet_factory(l3packet, port, payload):
    return l3packet/UDP(dport=port)/Raw(payload)


def build_sender(config):
    l3 = config.get('l3', 'ip')
    is_ipv6 = False
    l3Factory = None
    if l3.lower() in ['ip', 'ipv4']:
        l3Factory = ipv4_packet_factory
    elif l3.lower() == 'ipv6':
        is_ipv6 = True
        l3Factory = ipv6_packet_factory
    else:
        raise RuntimeError("unknown l3 protocol")

    l4 = config.get('l4', 'icmp')
    l4Factory = None
    if l4 == 'icmp':
        l4Factory = lambda l3p: icmp_packet_factory(l3p, is_ipv6)
    elif l4 == 'tcp':
        port = config["port"]
        l4Factory = lambda l3p: tcp_syn_packet_factory(l3p, port)
    elif l4 == 'udp':
        if config.get("use_dns", True):
            l4Factory = udp_dns_packet_factory
        else:
            port = config["port"]
            l4Factory = lambda l3p: raw_udp_packet_factory(l3p, port, config.get('payload', ''))

    return PacketSender(l3Factory, l4Factory)
