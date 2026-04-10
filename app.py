import argparse

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from loader import load_config, load_questions, load_topics
from tree import tree
from utils import load_html_from_file
from wrapper import Wrapper

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

CONFIG_PATH = "config/config.ini"


def render_cached_or_fresh(loader, output_file):
    try:
        data = loader(CONFIG_PATH)
        t = tree(data)
        wrapper = Wrapper(max_level=2)
        html = wrapper.wrap(t)
        wrapper.builder.add(html)
        wrapper.builder.save(output_file)
    except Exception:
        pass
    return load_html_from_file(output_file)


@app.route('/')
def topics():
    config = load_config(CONFIG_PATH)
    return render_cached_or_fresh(load_topics, config["app"]["topics_output"])


@app.route('/questions')
def questions():
    config = load_config(CONFIG_PATH)
    return render_cached_or_fresh(load_questions, config["app"]["questions_output"])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.ini", help="Path to INI config file")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    CONFIG_PATH = args.config
    config = load_config(CONFIG_PATH)
    app.run(host=config["server"]["host"], port=config.getint("server", "port"))
