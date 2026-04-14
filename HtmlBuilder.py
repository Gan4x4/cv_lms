import os
from utils import load_html_from_file


def save_modified_html(modified_html, file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_html)


class HTMLBuilder(object):
    def __init__(self, template_dir="templates"):
        self.core = ""
        self.id = 0
        self.template_dir = template_dir
        self.collapse = load_html_from_file(f"{self.template_dir}{os.sep}collapse.html")
        self.page = load_html_from_file(f"{self.template_dir}{os.sep}template.html")
        self.button = load_html_from_file(f"{self.template_dir}{os.sep}button.html")

    def make_collapse(self, name, content):
        x = self.collapse.replace("{id}", str(self.id))
        x = x.replace("{name}", name)
        x = x.replace("{text}", content)
        self.id += 1
        return x

    def make_button(self, name):
        x = self.button.replace("{name}", name)
        return x

    def add(self, content):
        self.core += content

    def save(self, file_path, context=None):
        modified_html = self.page.replace("{}", self.core)
        replacements = {
            "__STATUS_BADGE__": "",
            "__REFRESH_FORM__": "",
            "__PAGE_FOOTER__": "",
        }
        if context:
            replacements.update(context)
        for placeholder, value in replacements.items():
            modified_html = modified_html.replace(placeholder, value)
        save_modified_html(modified_html, file_path)
