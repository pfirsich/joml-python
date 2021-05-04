import argparse
import json

from . import joml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    with open(args.file) as f:
        print(json.dumps(joml.load(f, dict_type=dict), indent=4))


if __name__ == "__main__":
    main()
