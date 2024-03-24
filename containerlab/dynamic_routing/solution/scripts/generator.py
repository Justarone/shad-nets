import json
import functools
import os
import common


def get_subnet(interface):
    return 32 if 'lo' in interface else 24


NET_AREA = '49.0001'
HOST_PATTERN = "{id}000.0000.{id}00{pc_id}.00"


def get_host_addr(id, is_router):
    assert id < 10
    return HOST_PATTERN.format(id=id, pc_id=0 if is_router else id)


# NOTE: для использования общего паттерна и более простой генерации я задал адреса
# router1 и PC1 подходящими под паттерн, альтернативно - можно построить в конфиге 
# отображение вида устройство->NET-адрес
def get_isis_addr(dev):
    id = common.get_idx(dev)
    return f"{NET_AREA}.{get_host_addr(id, 'router' in dev)}"


def configure_isis_interface(descr):
    if descr['interface'] == 'lo':
        return [
            f"ip addr {descr['ip']}/{get_subnet(descr['interface'])}",
            "ip router isis 1",
            "isis passive",
        ]
    return [
        f"ip addr {descr['ip']}/{get_subnet(descr['interface'])}",
        "ip router isis 1",
        "isis circuit-type level-2-only",
        "isis network point-to-point",
    ]


def configure_router_routings(links, container_template):
    container_to_commands = dict()
    for dev, destinations in filter(lambda d: 'router' in d[0], links.items()):
        commands = ['conf', 'router isis 1', 'is-type level-2-only', f'net {get_isis_addr(dev)}', 'exit']
        for descr in destinations.values():
            commands.append(f"int {descr['interface']}")
            commands += configure_isis_interface(descr)
            commands.append("exit")
        commands += ['do wr', 'exit']
        container_to_commands[container_template.format(dev)] = commands
    return container_to_commands


def configure_pc_routings(links, container_template):
    container_to_commands = dict()
    for dev in filter(lambda d: 'PC' in d, links.keys()):
        commands = ["conf", "router isis 1", f"net {get_isis_addr(dev)}", "is-type level-2-only", "exit"]
        for descr in links[dev].values():
            commands.append(f"int {descr['interface']}")
            commands += configure_isis_interface(descr)
            commands.append("exit")
        commands += ['do wr', 'exit']
        container_to_commands[container_template.format(dev)] = commands
    return container_to_commands


def to_net(ip):
    if ip.startswith('192.168') and int(ip.split('.')[2]) > 10:
        return f"{'.'.join(ip.split('.')[:3])}.0/24"
    else:
        return ip + '/32'


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
    routers_count = sum(map(lambda _: 1, filter(lambda d: 'router' in d, device_to_links)))
    common.assign_ips_to_links(device_to_links, routers_count)

    # commands
    all_commands = dict()
    all_commands.update(configure_router_routings(device_to_links, config['container_template']))
    all_commands.update(configure_pc_routings(device_to_links, config['container_template']))

    if config.get("execute_commands", False):
        commands = build_commands(config.get('docker_command', 'docker'), all_commands, config.get("execute_prepare", True))
        for command in commands:
            print(f'executing {command}.....')
            if os.system(command) != 0:
                print("something went wrong during execution, aborting the whole process")
                break
    else:
        print('commands are not executed, set "execute_commands": true in config to do it, listing vtysh commands:')
        print(json.dumps(all_commands, indent=4))


main()
