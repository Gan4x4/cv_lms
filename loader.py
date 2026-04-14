import configparser
import os
from datetime import datetime, timezone
from time import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib import request

import numpy as np
import pandas as pd


def load_config(config_path):
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return config


def _remove_file_if_exists(path):
    if path and os.path.exists(path):
        os.remove(path)


def _clear_directory(directory):
    if not directory or not os.path.isdir(directory):
        return
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isfile(path):
            os.remove(path)


def clear_runtime_cache(config_path):
    config = load_config(config_path)
    cache_dir = os.path.dirname(config["topics"].get("cache_path", "")) or "var/cache"
    generated_dir = os.path.dirname(config["app"].get("topics_output", "")) or "var/generated"
    _clear_directory(cache_dir)
    _clear_directory(generated_dir)


def _format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _display_updated_at(path):
    if os.path.exists(path):
        return _format_timestamp(os.path.getmtime(path))
    return "unknown"


def _local_source_state(path):
    return {
        "source_type": "local",
        "filename": path,
        "updated_at": _display_updated_at(path),
        "connection_failed": False,
    }


def _build_request_url(url):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["_cache_bust"] = str(int(time()))
    return urlunsplit(parts._replace(query=urlencode(query)))


def _download_csv(url, destination):
    destination_dir = os.path.dirname(destination)
    if destination_dir:
        os.makedirs(destination_dir, exist_ok=True)

    temp_filename = f"{destination}.download"
    _remove_file_if_exists(temp_filename)

    request_url = _build_request_url(url)
    http_request = request.Request(
        request_url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    try:
        with request.urlopen(http_request) as response:
            with open(temp_filename, "wb") as file:
                file.write(response.read())
        os.replace(temp_filename, destination)
        return {
            "source_type": "remote",
            "filename": destination,
            "updated_at": _display_updated_at(destination),
            "connection_failed": False,
        }
    except Exception:
        _remove_file_if_exists(temp_filename)
        if os.path.exists(destination):
            return {
                "source_type": "remote",
                "filename": destination,
                "updated_at": _display_updated_at(destination),
                "connection_failed": True,
            }
        raise


def _load_sheet_source(config, section_name):
    source_type = config[section_name]["type"]
    if source_type == "local":
        return _local_source_state(config[section_name]["path"])
    if source_type == "remote":
        destination = config[section_name]["cache_path"]
        if os.path.exists(destination) and time() - os.path.getmtime(destination) < 3600:
            source_state = _local_source_state(destination)
            source_state["source_type"] = "remote"
            return source_state
        return _download_csv(config[section_name]["url"], destination)
    raise ValueError(f"Unsupported source type for {section_name}: {source_type}")


def load_questions(config_path):
    config = load_config(config_path)
    source_state = _load_sheet_source(config, "questions")
    data = pd.read_csv(source_state["filename"], header=None)
    data = data.iloc[1:, 1:]
    return data, source_state


def load_topics(config_path):
    config = load_config(config_path)
    source_state = _load_sheet_source(config, "topics")
    data = pd.read_csv(source_state["filename"], header=None)
    index = np.where(data == 'Защита работ')
    if len(index[0]):
        stop = index[0][0]
    else:
        stop = len(data)
    data = data.iloc[1:stop, 1:]
    return data, source_state
