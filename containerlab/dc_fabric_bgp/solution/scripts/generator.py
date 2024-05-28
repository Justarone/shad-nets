import json
import functools
import os
import common


def configure_ip(descr):
    return f"ip addr {descr['ip']}/{32 if descr['interface'] == 'lo' else 30}"


def get_bgp_commands(device, descriptions, config):
    interfaces = filter(lambda x: x != 'lo', map(lambda x: x['interface'], descriptions.values()))
    return [
        "ip prefix-list DC_LOCAL_SUBNET seq 5 permit 172.16.0.0/16 le 32",
        "ip prefix-list DC_LOCAL_SUBNET seq 10 permit 10.0.254.0/24 le 32",
        "route-map ACCEPT_DC_LOCAL permit 10",
        "match ip address prefix-list DC_LOCAL_SUBNET",
        "exit",
        "route-map PERMIT_EBGP permit 10",
        "exit",
        f"router bgp {config['asns'][device]}",
            f"bgp router-id {descriptions[device]['ip']}",
            "bgp bestpath as-path multipath-relax",
            "neighbor FABRIC peer-group",
            *[f"neighbor {interface} interface peer-group FABRIC" for interface in interfaces],
            "neighbor FABRIC remote-as external",
            "address-family ipv4 unicast",
                "redistribute connected route-map ACCEPT_DC_LOCAL",
                "neighbor FABRIC route-map PERMIT_EBGP in",
                "neighbor FABRIC route-map PERMIT_EBGP out",
            "exit-address-family",
        "exit",
    ]


def configure_bgp(links, config):
    container_to_commands = dict()
    for dev, destinations in links.items():
        commands = ['conf']
        for descr in destinations.values():
            commands.append(f"int {descr['interface']}")
            commands.append(configure_ip(descr))
            commands.append("exit")
        commands += get_bgp_commands(dev, destinations, config)
        commands += ['do wr', 'exit']
        container_to_commands[config['container_template'].format(dev)] = commands
    return container_to_commands


def build_vtysh_arguments(commands):
    return ''.join(map(lambda c: f' -c "{c}"', commands))


def build_commands(docker_command, vtysh_commands_map, execute_prepare):
    commands = []
    for container, vtysh_commands in vtysh_commands_map.items():
        vtysh_args = build_vtysh_arguments(vtysh_commands)
        if execute_prepare:
            commands.append(f"{docker_command} exec -it {container} touch /etc/frr/vtysh.conf")
        commands.append(f"{docker_command} exec -it {container} vtysh {vtysh_args}")
    return commands


def main():
    args = common.parse_args()
    config = common.load_json(args.config)
    topology_config = common.load_yml(args.topology)

    # preparation
    device_to_links = common.parse_links(topology_config['topology']['links'])
    common.assign_ips_to_links(device_to_links, config)

    # commands
    commands = configure_bgp(device_to_links, config)
    if config.get("execute_commands", False):
        commands = build_commands(config.get('docker_command', 'docker'), commands, config.get("execute_prepare", True))
        for command in commands:
            print(f'executing {command}.....')
            if os.system(command) != 0:
                print("something went wrong during execution, aborting the whole process")
                break
    else:
        print('commands are not executed, set "execute_commands": true in config to do it, listing vtysh commands:')
        print(json.dumps(commands, indent=4))


main()
