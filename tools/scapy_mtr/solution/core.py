import time
from time import sleep
from prettytable import PrettyTable


class Response:
    SUCCESSFULLY_REACHED = 0
    TTL_EXCEEDED = 1
    NO_ANSWER = 2 # packet lost case

    def __init__(self, status, received_from):
        assert received_from is not None or status == Response.NO_ANSWER
        self.status = status
        self.received_from = received_from


class Sender:
    def send(self, address, ttl=None) -> Response:
        pass


class HopStat:
    COLUMNS = ["sent", "lost %", "avg ms", "min ms", "max ms", "addresses"]
    def __init__(self):
        self.addresses = set()
        self.collected = 0
        self.total = 0
        self.times = []

    def update(self, trace_item):
        self.addresses.add(trace_item["response"].received_from)
        self.collected += trace_item["response"].status != Response.NO_ANSWER
        self.total += 1
        self.times.append(trace_item["time"] * 1000)

    def get_stat_list(self):
        return [
            self.total,
            "{:.2f}".format((self.total - self.collected) / self.total * 100) + '%',
            "{:.2f}".format(sum(self.times) / len(self.times)),
            "{:.2f}".format(min(self.times)),
            "{:.2f}".format(max(self.times)),
            ', '.join(map(lambda a: 'unknown' if a is None else a, self.addresses)),
        ]


def trace(sender, target_address):
    ttl = 1
    result = []
    response = None
    while response is None or response.status != Response.SUCCESSFULLY_REACHED:
        start_ts = time.time()
        response = sender.send(target_address, ttl=ttl)
        result.append({
            "time": time.time() - start_ts,
            "response": response,
        })
        ttl += 1

    return result


def collect_stat(trace_result, stat):
    for hops0, descr in enumerate(trace_result, 0):
        stat[hops0].update(descr)


def print_stat(stat, iteration):
    table = PrettyTable()
    table.field_names = ['hops'] + HopStat.COLUMNS
    for i, hs in enumerate(stat, 1):
        table.add_row([i] + hs.get_stat_list())
    print(table)


def run_algorithm(sender, config):
    target_address = config["target_address"]
    response = sender.send(target_address)
    assert response.status == Response.SUCCESSFULLY_REACHED, 'address must be reachable via protocols'
    target_address = response.received_from
    print(target_address)
    iteration = 1
    stat = []  # per address
    while iteration < config.get("iterations_count", 1_000_000):
        result = trace(sender, target_address)
        while len(stat) < len(result):
            stat.append(HopStat())
        collect_stat(result, stat)
        if iteration % config.get("print_every", 1) == 0:
            print_stat(stat, iteration)
        sleep(config.get("iteration_sleep_ms", 500) / 1000)
