import csv
from tree import tree
import re
from HtmlBuilder import HTMLBuilder
from loader import load_topics


MAX_LEVEL = 2
URL_PATTERN = re.compile(r"https?://[^\s]+")
#def read_csv(filename):
#    data = []
#    with open(filename, mode='r', encoding='utf-8') as file:
#        reader = csv.reader(file)
#        for row in reader:
#            data.append(row)
#    return data

# https://docs.google.com/spreadsheets/d/1TfAWZkN1dA-ftaSONKegxrnF12kO35ZwClaBhIkGszY/edit?usp=drive_link
# https://docs.google.com/spreadsheets/d/1TfAWZkN1dA-ftaSONKegxrnF12kO35ZwClaBhIkGszY/edit?usp=sharing
# gdown.download(id = "https://docs.google.com/spreadsheets/d/1TfAWZkN1dA-ftaSONKegxrnF12kO35ZwClaBhIkGszY/edit?usp=sharing", output = "questions.xls")
# url = "https://docs.google.com/spreadsheets/d/1TfAWZkN1dA-ftaSONKegxrnF12kO35ZwClaBhIkGszY/edit?usp=sharing"
# gdown.download(url=url, output = "questions.xls", fuzzy=True)

def make_url_clickable(text):
    parts = []
    cursor = 0

    for match in URL_PATTERN.finditer(text):
        parts.append(text[cursor:match.start()])
        url = match.group(0)
        parts.append(f'<a href="{url}" target="_blank">{url}</a>')
        cursor = match.end()

    parts.append(text[cursor:])
    return "".join(parts)


class Wrapper(object):
    def __init__(self, max_level = 2):
        self.builder = HTMLBuilder()
        self.max_level = max_level

    def flatten(self, t):
        out = ""
        for key, value in t.items():
            v = '<div class="filter-leaf">'
            v += make_url_clickable(key)
            if len(value):
                v += self.flatten(value)
            v += "</div>\n"
            out += v

        return out


    def wrap(self, t, level=0):
        if level > self.max_level:
            return self.flatten(t)
        out = ""
        for key, value in t.items():
            if "https" in key:
                out += make_url_clickable(key) + self.flatten(value)
                continue
            if len(value):
                v = self.wrap(value, level + 1)
            else:
                v = ""
            if len(v):
                out += self.builder.make_collapse(key, v)
            else:
                out += self.builder.make_button(key)
        return out






#data = load_topics()
#t = tree(data)
#builder = HTMLBuilder()
#html = wrap(t)

#builder.add(html)
#builder.save("out.html")
