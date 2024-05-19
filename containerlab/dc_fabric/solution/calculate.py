import json
import argparse
import math


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.json", help="path to config file")
    parser.add_argument("-p", "--ports", default=500, type=int, help="client ports count")
    parser.add_argument("-o", "--oversubscription", default=1, type=int, help="expected oversubscription")
    return parser.parse_args()


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def run_algorithm(config, specific_params):
    client_ports = config["tor"]["client_ports"]
    spine_ports = config["tor"]["spine_ports"]

    downwidth = client_ports["bandwidth"] * client_ports["count"]
    planes = uplinks = max(2 if config['safe'] else 1, math.floor(downwidth / spine_ports['bandwidth'] / specific_params['oversubscription']))
    assert uplinks <= spine_ports['max_count'], "tor'у не хватает портов наверх к spine'ам"

    tors_count = math.ceil(specific_params['ports'] / client_ports["count"])

    pods = 1
    spine_ports_count = specific_params["spine"]["ports"]
    if tors_count > spine_ports_count:
        # 2-level scheme
        assert spine_ports_count % 2 == 0
        spine_ports_count //= 2
        pods = math.ceil(tors_count / spine_ports_count)

    total_tor_links = uplinks * tors_count # суммарное число link'ов между tor и spine1
    total_spine_links = specific_params['spine']['ports'] // 2 * pods * planes if pods > 1 else 0 # суммарное число link'ов между spine1 и spine2

    total_spines1 = uplinks * pods
    spines2_per_plane = min(filter(lambda z: (not config['safe'] or z > 1) and z >= pods // 2, map(lambda x: 2^x, range(math.floor(math.log2(specific_params['spine']['ports'])) + 1))))

    tors_price = tors_count * config['tor']['price']
    all_spines_price = specific_params['spine']['price'] * (total_spines1 + spines2_per_plane * planes)
    transceivers_price = config['link_price'] * 2 * (total_tor_links + total_spine_links) # 2 per every tor-spine, spine1-spine2 link

    return {
        'levels': 1 if pods == 1 else 2,
        'tors_per_pod': spine_ports_count if pods > 1 else tors_count,
        'last_pod_tors': (tors_count % spine_ports_count if tors_count % spine_ports_count != 0 else spine_ports) if pods > 1 else tors_count,
        'spines_per_pod': uplinks,
        'pods': pods,
        'spines2_per_plane': spines2_per_plane if pods > 1 else 0,
        'price': tors_price + all_spines_price + transceivers_price
    }


def main():
    args = parse_args()
    config = load_json(args.config)
    params = {"oversubscription": args.oversubscription, "ports": args.ports}
    for spine in config["spines"]:
        params["spine"] = spine
        print(f'result for spine {spine}:\n{run_algorithm(config, params)}')


main()
