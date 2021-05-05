import argparse
import json
import sys

from . import joml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--full", "-f", action="store_true")
    parser.add_argument("--ignore-duplicate-keys", "-i", action="store_true")
    args = parser.parse_args()

    if args.full and args.ignore_duplicate_keys:
        sys.exit("--full and --ignore-duplicate-keys are mutually exclusive")

    with open(args.file) as f:
        data = joml.load(f)

    if args.full:
        print(json.dumps(data.full_unpack(), indent=4))
    else:
        print(json.dumps(data.unpack(not args.ignore_duplicate_keys), indent=4))


if __name__ == "__main__":
    main()
