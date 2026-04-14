import argparse
import configparser
import os
from datetime import datetime, timezone


def load_config(config_path):
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return config


def format_timestamp(path):
    if not os.path.exists(path):
        return "missing"
    dt = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_source_path(config, section_name):
    source = config[section_name]
    if source["type"] == "local":
        return source["path"]
    if source["type"] == "remote":
        return source["cache_path"]
    raise ValueError(f"Unsupported source type for {section_name}: {source['type']}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print cached/local file times for configured sheet sections."
    )
    parser.add_argument(
        "--config",
        default="config/config.ini",
        help="Path to config file. Defaults to config/config.ini.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)
    for section_name in ("topics", "questions"):
        print(f"{section_name}: {format_timestamp(get_source_path(config, section_name))}")


if __name__ == "__main__":
    main()
