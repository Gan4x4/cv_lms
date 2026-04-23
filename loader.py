import configparser
import os
from datetime import datetime, timezone
from time import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib import request

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
    generated_dir = os.path.dirname(config["app"].get("topics_output", "")) or "var/generated"
    for section_name in ("topics", "questions"):
        if config.has_section(section_name):
            _remove_file_if_exists(config[section_name].get("cache_path"))
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


def _cell_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _question_link_columns(data):
    if data.empty:
        return []
    header = data.iloc[0]
    return [
        column_index
        for column_index, value in enumerate(header)
        if _cell_text(value) and _cell_text(value).lower().startswith("link")
    ]


def _topics_from_questions(data):
    link_columns = _question_link_columns(data)
    rows = []
    current_topic = None
    current_subtopic = None
    seen_links = {}

    for _, source_row in data.iloc[1:].iterrows():
        topic = _cell_text(source_row.iloc[1]) if len(source_row) > 1 else None
        subtopic = _cell_text(source_row.iloc[2]) if len(source_row) > 2 else None
        links = [
            text
            for column_index in link_columns
            if column_index < len(source_row)
            for text in [_cell_text(source_row.iloc[column_index])]
            if text
        ]

        if topic:
            current_topic = topic
            current_subtopic = None

        if subtopic:
            current_subtopic = subtopic

        if not topic and not subtopic and not links:
            continue

        target_key = None
        if subtopic or current_subtopic:
            target_key = ("subtopic", topic or current_topic, subtopic or current_subtopic)
        elif topic or current_topic:
            target_key = ("topic", topic or current_topic)

        if links and target_key is not None:
            target_seen = seen_links.setdefault(target_key, set())
            unique_links = []
            for link in links:
                if link in target_seen:
                    continue
                target_seen.add(link)
                unique_links.append(link)
            links = unique_links

        if not links:
            rows.append([topic, subtopic, None])
            continue

        if subtopic or current_subtopic:
            rows.append([topic, subtopic, links[0]])
            rows.extend([[None, None, link] for link in links[1:]])
            continue

        if topic or current_topic:
            rows.append([topic, links[0], None])
            rows.extend([[None, link, None] for link in links[1:]])
            continue

        rows.append([links[0], None, None])
        rows.extend([[None, link, None] for link in links[1:]])

    return pd.DataFrame(rows)


def load_topics(config_path):
    config = load_config(config_path)
    source_state = _load_sheet_source(config, "questions")
    data = pd.read_csv(source_state["filename"], header=None)
    return _topics_from_questions(data), source_state
