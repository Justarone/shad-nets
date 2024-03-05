import json
import functools
import os
import common


def build_min_paths(links):
    devices = list(links.keys())
    paths = {device: {dev: [dev] if dev in links[device] else None for dev in devices} for device in devices}

    def update(dev1, dev2, dev3):
        if paths[dev1][dev3] is not None and paths[dev3][dev2] is not None:
            new_path = paths[dev1][dev3] + paths[dev3][dev2]
            if paths[dev1][dev2] is None or len(paths[dev1][dev2]) > len(new_path):
                paths[dev1][dev2] = new_path

    for k in devices:
        for i in devices:
            for j in devices:
                update(i, j, k)

    return paths


def get_subnet(interface):
    return 32 if 'lo' in interface else 24


def assign_ips_to_interfaces(links, container_template):
    container_to_commands = dict()
    for dev, destinations in links.items():
        commands = ['conf']
        for descr in destinations.values():
            commands.append(f"int {descr['interface']}")
            commands.append(f"ip addr {descr['ip']}/{get_subnet(descr['interface'])}")
            commands.append(f"exit")
        commands += ['do wr', 'exit']
        container_to_commands[container_template.format(dev)] = commands
    return container_to_commands


def configure_pc_routings(links, container_template):
    container_to_commands = dict()
    for dev in filter(lambda d: 'PC' in d, links.keys()):
        local_links = list(links[dev].items())
        assert len(local_links) == 1 and 'router' in local_links[0][0]
        local_link = local_links[0]
        dst_ip_and_int = f"{links[local_link[0]][dev]['ip']} {local_link[1]['interface']}"
        container_to_commands[container_template.format(dev)] = [
            'conf',
            f'ip route {common.LOOPBACKS_NETWORK_TEMPLATE.format(0)}/24 {dst_ip_and_int}',
            f'ip route 192.168.0.0/16 {dst_ip_and_int}',
            'do wr',
            'exit'
        ]
    return container_to_commands


def to_net(ip):
    if ip.startswith('192.168') and int(ip.split('.')[2]) > 10:
        return f"{'.'.join(ip.split('.')[:3])}.0/24"
    else:
        return ip + '/32'


def check_directly_connected(links, net, router):
    if not net.endswith('/32'):
        return False
    ip = net[:net.find('/')]
    connected = links[router].keys()
    return ip in map(lambda target: links[target][router]['ip'], connected)


def make_routers_to_routes(links, container_template, paths):
    routers_to_routes = {r: dict() for r in filter(lambda d: 'router' in d, links.keys())}  # router -> { target_ip -> int/ip }
    for src, dsts in paths.items():
        for dst, path in dsts.items():
            target_nets = map(lambda descr: to_net(descr['ip']), links[dst].values())

            for i in range(len(path) - 1):
                router_name = path[i]
                route_to_name = path[i + 1]
                for net in target_nets:
                    if check_directly_connected(links, net, router_name):
                        continue
                    out_descr = {
                        'ip': links[route_to_name][router_name]['ip'],
                        'interface': links[router_name][route_to_name]['interface']
                    }
                    routers_to_routes[router_name][net] = out_descr
    return routers_to_routes


def configure_routers_routing(links, container_template, paths):
    routers_to_routes = make_routers_to_routes(links, container_template, paths)
    router_to_commands = {}
    for router, routes in routers_to_routes.items():
        commands = []
        for target_net, out_descr in routes.items():
            commands.append(f"ip route {target_net} {out_descr['ip']} {out_descr['interface']}")
        commands.sort()
        router_to_commands[container_template.format(router)] = ['conf'] + commands + ['exit']
    return router_to_commands


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
    paths = build_min_paths(device_to_links)

    # commands
    assign_ips_commands = assign_ips_to_interfaces(device_to_links, config['container_template'])
    pc_routing_commands = configure_pc_routings(device_to_links, config['container_template'])
    routers_routing_commands = configure_routers_routing(device_to_links, config['container_template'], paths)

    def combine_maps(combinator):
        return combinator([assign_ips_commands, pc_routing_commands, routers_routing_commands])

    containers = combine_maps(lambda ms: functools.reduce(lambda res, m: res | set(m.keys()), ms, set()))
    all_commands = {c: combine_maps(lambda ms: functools.reduce(lambda res, m: res + m.get(c, []), ms, [])) for c in containers}
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
