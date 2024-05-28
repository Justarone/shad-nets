import common
import subprocess


def all_ips(links):
    ips = dict()
    for dev, devmap in links.items():
        for descr in devmap.values():
            ips[descr['ip']] = dev

        # ips[devmap[dev]['ip']] = dev
    return ips


def mask_command(command):
    return command.replace(' ', '#')


def unmask_command(command):
    return command.replace('#', ' ')


def run_command(docker_command, command, container, ip):
    result_command = map(lambda w: unmask_command(w), f'{docker_command} exec -it {container} {command} {ip}'.split(' '))
    return subprocess.run(result_command, capture_output=True, text=True)


def parse_ip_route(output):
    lines = list(map(lambda line: line.strip(), output.splitlines()))
    return '\n'.join(lines[lines.index('')+1:])

def parse_bgp_neighbors(output):
    lines = list(map(lambda line: line.strip(), output.splitlines()))
    return '\n'.join(filter(lambda line: 'Hostname:' in line or 'Nexthop' in line, lines))

def parse_ip_bgp_summary(output):
    lines = list(map(lambda line: line.strip(), output.splitlines()))
    return '\n'.join(lines[lines[1:].index('')+1:])


COMMUNICATION_COMMANDS_DESCRIPTIONS = {
    'ping': {
        'command': 'ping -w 2 -c 1',
        'print_output': False
    },
    'traceroute': {
        'command': 'traceroute',
        'print_output': True
    }
}


NODE_COMMANDS_PARSERS = {
    'sh ip route': parse_ip_route,
    'sh ip bgp neighbors': parse_bgp_neighbors,
    'sh ip bgp summary': parse_ip_bgp_summary,
}


def main():
    args = common.parse_args()
    config = common.load_json(args.config)
    topology_config = common.load_yml(args.topology)
    links = common.parse_links(topology_config['topology']['links'])
    common.assign_ips_to_links(links, config)

    ips_to_dev = all_ips(links) if config.get("check_all", True) else { k: 'unspecified_node' for k in config.get('check_ips', []) }
    nodes = list(links.keys()) if config.get("check_all", True) else config['check_nodes']
    communication_commands = config.get('check_communication_commands', ['ping', 'traceroute'])
    node_commands = config.get('check_node_commands', ['sh run', 'sh int brief', 'sh ip route'])

    for node in nodes:
        for command in node_commands:
            print(f'RUNNING NODE={node}, VTYSH COMMAND="{command}".....')
            result = run_command(config.get('docker_command', 'docker'), f'vtysh -c {mask_command(command)}', config['container_template'].format(node), '')
            print(NODE_COMMANDS_PARSERS[command](result.stdout) if command in NODE_COMMANDS_PARSERS else result.stdout)
            assert result.returncode == 0

    show_docker_ps = config.get('show_docker_ps', False)
    if show_docker_ps:
        result = subprocess.run(f"docker ps".split(' '), capture_output=True, text=True)
        print(result.stdout)
        assert result.returncode == 0

    for ip, target_dev in ips_to_dev.items():
        for node in nodes:
             # links[target_dev][target_dev]['ip'] -- чтобы проверить direct пинг до адреса lo интерфейса соседа (не работает без bgp)
            if config.get('only_direct', False) and (node not in links[target_dev] or ip not in [links[target_dev][node]['ip']]):
                continue

            for command in communication_commands:
                print(f"RUNNING {command}: from={node}, to={target_dev} ({ip})")
                descr = COMMUNICATION_COMMANDS_DESCRIPTIONS[command]
                run_result = run_command(config.get('docker_command', 'docker'), descr['command'], config['container_template'].format(node), ip)
                assert run_result.returncode == 0
                print(run_result.stdout if descr['print_output'] else "success!")


if __name__ == '__main__':
    main()
