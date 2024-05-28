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


def assign_ips_to_links(links, config):
    ips_config = config['ips']
    for device, destinations in links.items():
        for destination, descr in destinations.items():
            descr['ip'] = ips_config[device][descr['interface']]
        destinations[device] = {'interface': 'lo', 'ip': ips_config[device]['lo']}
