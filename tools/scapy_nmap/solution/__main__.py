from scapy.all import *
import argparse
import math
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addresses", help="addresses to scan")
    parser.add_argument("-p", "--ports", help="ports to scan")
    return parser.parse_args()


def main():
    args = parse_args()
    ps = list(IP(dst=args.addresses)/TCP(dport=tuple(map(int, args.ports.split('-'))), sport=1234))
    answers = []

    attempts = 3
    timeout = 3
    portion = 20

    for attempt in range(attempts):
        unanswered = []
        for i in range(0, len(ps), portion):
            [new_answers, new_unanswered] = sr(ps[i:min(len(ps), i + portion)], timeout=3)
            answers += new_answers
            unanswered += new_unanswered
        ps = unanswered
        eprint(f"after attempt [{attempt + 1}]: {len(answers)}/{len(answers) + len(ps)}")

    eprint(f'unanswered in {timeout} seconds and {attempts} attempts:', len(ps))

    available_endpoints = list(map(lambda a: (a.answer.src, a.answer.sport), filter(lambda a: a.answer['TCP'].flags == "SA", answers)))
    eprint("not SA flags count:", len(answers) - len(available_endpoints))
    eprint("available endpoints:", ', '.join(map(lambda p: f'{p[0]}:{p[1]}', available_endpoints)))


if __name__ == '__main__':
    main()
