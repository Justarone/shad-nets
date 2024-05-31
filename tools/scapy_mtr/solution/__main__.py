import core
import impl
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.json", help="path to config file")
    return parser.parse_args()


def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def main():
    args = parse_args()
    config = load_json(args.config)
    sender = impl.build_sender(config['sender'])
    core.run_algorithm(sender, config['algorithm'])


if __name__ == '__main__':
    main()
