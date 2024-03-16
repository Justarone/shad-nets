import json
import argparse
import yaml
import re


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.json", help="path to config file")
    parser.add_argument("-t", "--topology", default="clab.yml", help="path to clab file")
    return parser.parse_args()


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def load_yml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def parse_links(links):
    def make_link_description(interface):
        return {'interface': interface}

    def process_link(mapping, from_device, to_device):
        if from_device[0] not in mapping:
            mapping[from_device[0]] = dict()
        mapping[from_device[0]][to_device[0]] = make_link_description(from_device[1])

    device_to_links = {}
    for link in links:
        dev1, dev2 = map(lambda dev_with_int: dev_with_int.split(':'), link['endpoints'])
        process_link(device_to_links, dev1, dev2)
        process_link(device_to_links, dev2, dev1)
    return device_to_links


def get_idx(device):
    return int(device[re.search(r'\d', device).start():])


def generate_ip(from_device, to_device, routers_total):
    def get_net_idx(router1, router2, routers_total):
        id1, id2 = get_idx(router1), get_idx(router2)
        if id1 > id2:
            id1, id2 = id2, id1
        return sum(range(routers_total - 1, routers_total - id1, -1)) + id2 - id1

    def generate_pc_router_ip(pc, router, pc_ip_ending):
        return f'192.168.{get_idx(pc) * 11}.{pc_ip_ending}'

    def generate_router_pc_ip(router, pc):
        return f'192.168.{get_idx(pc) * 11}.{get_idx(router)}'

    def generate_router_router_ip(from_router, to_router, routers_total):
        return f'192.168.{get_net_idx(from_router, to_router, routers_total)}.{get_idx(from_router)}'

    if 'PC' in from_device:
        assert 'router' in to_device
        return generate_pc_router_ip(from_device, to_device, routers_total + 1)
    elif 'PC' in to_device:
        assert 'router' in from_device
        return generate_router_pc_ip(from_device, to_device)
    else:
        assert 'router' in from_device
        assert 'router' in to_device
        return generate_router_router_ip(from_device, to_device, routers_total)


LOOPBACKS_NETWORK_TEMPLATE = '10.10.10.{}'


def fill_loopbacks(links):
    for device, destinations in filter(lambda dev: 'router' in dev[0], links.items()):
        destinations[device] = {'interface': 'lo', 'ip': LOOPBACKS_NETWORK_TEMPLATE.format(get_idx(device))}


def assign_ips_to_links(links, routers_total):
    assert routers_total < 6, "generator needs changes to work with more than 5 routers"
    for device, destionations in links.items():
        for destination, descr in destionations.items():
            descr['ip'] = generate_ip(device, destination, routers_total)
    fill_loopbacks(links)
