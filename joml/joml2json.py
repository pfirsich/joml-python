import argparse
import json

from . import joml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    with open(args.file) as f:
        data = joml.load(f)
        print(json.dumps(data.full_unpack(), indent=4))
        print(json.dumps(data.unpack(), indent=4))


if __name__ == "__main__":
    main()
