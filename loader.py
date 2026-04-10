import configparser
import os

import numpy as np
import pandas as pd
import wget


def load_config(config_path):
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return config


def _download_csv(url, destination):
    destination_dir = os.path.dirname(destination)
    if destination_dir:
        os.makedirs(destination_dir, exist_ok=True)
    temp_filename = f"{destination}.download"
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    try:
        wget.download(url, out=temp_filename)
        os.replace(temp_filename, destination)
        return destination
    except Exception:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if os.path.exists(destination):
            return destination
        raise


def _load_sheet_source(config, section_name):
    source_type = config[section_name]["type"]
    if source_type == "local":
        return config[section_name]["path"]
    if source_type == "remote":
        destination = config[section_name]["cache_path"]
        url = config[section_name]["url"]
        return _download_csv(url, destination)
    raise ValueError(f"Unsupported source type for {section_name}: {source_type}")


def load_questions(config_path):
    config = load_config(config_path)
    filename = _load_sheet_source(config, "questions")
    data = pd.read_csv(filename, header=None)
    data = data.iloc[1:, 1:]
    return data


def load_topics(config_path):
    config = load_config(config_path)
    filename = _load_sheet_source(config, "topics")
    data = pd.read_csv(filename, header=None)
    index = np.where(data == 'Защита работ')
    if len(index[0]):
        stop = index[0][0]
    else:
        stop = len(data)
    data = data.iloc[1:stop, 1:]
    return data
