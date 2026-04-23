import re
import os
from urllib.parse import urlsplit, unquote
from HtmlBuilder import HTMLBuilder


URL_PATTERN = re.compile(r"https?://[^\s]+")
GENERIC_SEGMENTS = {"", "edit", "view", "blob", "tree", "main", "drive", "d", "article"}


def is_opaque_segment(segment):
    return len(segment) >= 16 and any(char.isdigit() for char in segment)


def classify_url_label(url):
    lowered = url.lower()

    if "docs.google.com/presentation/" in lowered:
        return "pptx"
    if "colab.research.google.com/" in lowered or lowered.endswith(".ipynb"):
        return "Colab"
    if "github.com/" in lowered and ".ipynb" in lowered:
        return "Colab"
    if "youtube.com/" in lowered or "youtu.be/" in lowered:
        return "video"
    if "github.com/" in lowered and "/tree/" in lowered:
        return "repo"
    if "github.com/" in lowered and "/blob/" in lowered:
        return "file"
    if lowered.endswith(".pdf"):
        return "pdf"
    if lowered.endswith(".pptx") or lowered.endswith(".ppt"):
        return "pptx"
    if lowered.endswith(".html") or lowered.endswith(".htm"):
        return "html"
    return "link"


def label_from_url(url):
    notebook_label = classify_url_label(url)
    if notebook_label == "Colab":
        return notebook_label

    parts = urlsplit(url)
    path_segments = [unquote(segment) for segment in parts.path.split("/") if segment]

    for segment in reversed(path_segments):
        candidate = segment.strip()
        lowered = candidate.lower()
        if lowered in GENERIC_SEGMENTS:
            continue
        if is_opaque_segment(candidate):
            continue
        stem, _ = os.path.splitext(candidate)
        if stem:
            candidate = stem
        if any(char.isalpha() for char in candidate):
            return candidate

    return classify_url_label(url)


def render_url_chip(url):
    label = label_from_url(url)
    return (
        f'<a href="{url}" target="_blank" title="{url}" '
        f'class="badge text-bg-light border text-decoration-none">{label}</a>'
    )

def make_url_clickable(text):
    parts = []
    cursor = 0

    for match in URL_PATTERN.finditer(text):
        parts.append(text[cursor:match.start()])
        url = match.group(0)
        parts.append(render_url_chip(url))
        cursor = match.end()

    parts.append(text[cursor:])
    return "".join(parts)


class Wrapper(object):
    def __init__(self, max_level = 2):
        self.builder = HTMLBuilder()
        self.max_level = max_level

    def flatten(self, t):
        out = ""
        inline_links = []

        for key, value in t.items():
            is_link_leaf = "https" in key and not value
            if is_link_leaf:
                inline_links.append(render_url_chip(key))
                continue

            if inline_links:
                out += '<div class="filter-leaf filter-link-row">' + "".join(inline_links) + "</div>\n"
                inline_links = []

            v = '<div class="filter-leaf">'
            v += make_url_clickable(key)
            if len(value):
                v += self.flatten(value)
            v += "</div>\n"
            out += v

        if inline_links:
            out += '<div class="filter-leaf filter-link-row">' + "".join(inline_links) + "</div>\n"

        return out


    def wrap(self, t, level=0):
        if level > self.max_level:
            return self.flatten(t)
        out = ""
        inline_links = []

        for key, value in t.items():
            is_link_leaf = "https" in key and not value
            if is_link_leaf:
                inline_links.append(render_url_chip(key))
                continue

            if inline_links:
                out += '<div class="filter-leaf filter-link-row">' + "".join(inline_links) + "</div>\n"
                inline_links = []

            if len(value):
                v = self.wrap(value, level + 1)
            else:
                v = ""
            if len(v):
                out += self.builder.make_collapse(key, v)
            else:
                out += self.builder.make_button(key)

        if inline_links:
            out += '<div class="filter-leaf filter-link-row">' + "".join(inline_links) + "</div>\n"

        return out
