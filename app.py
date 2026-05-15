import argparse

from flask import Flask, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix

from loader import clear_runtime_cache, load_config, load_questions, load_topics
from tree import tree
from utils import load_html_from_file
from wrapper import Wrapper

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

CONFIG_PATH = "config/cv.ini"
AGENTS_CONFIG_PATH = "config/agents.ini"


def build_page_context(config, source_state, current_path):
    status_badge = ""
    if source_state["connection_failed"]:
        status_badge = '<span class="badge text-bg-danger page-status-badge">Connection failed, using cache</span>'

    footer_text = f'Data updated: {source_state["updated_at"]}'
    page_footer = f'<div class="page-footer text-body-secondary small">{footer_text}</div>'
    refresh_form = (
        '<form method="post" action="/refresh" class="page-refresh-form">'
        f'<input type="hidden" name="next" value="{current_path}">'
        '<button type="submit" class="btn btn-outline-secondary btn-sm">Refresh</button>'
        '</form>'
    )

    return {
        "__PAGE_TITLE__": config["app"].get("title", "Computer vision topics"),
        "__STATUS_BADGE__": status_badge,
        "__REFRESH_FORM__": refresh_form,
        "__PAGE_FOOTER__": page_footer,
    }


def render_cached_or_fresh(loader, config_path, output_file, current_path):
    try:
        config = load_config(config_path)
        data, source_state = loader(config_path)
        t = tree(data)
        wrapper = Wrapper(max_level=2)
        html = wrapper.wrap(t)
        wrapper.builder.add(html)
        wrapper.builder.save(output_file, context=build_page_context(config, source_state, current_path))
    except Exception:
        pass
    return load_html_from_file(output_file)


@app.route('/')
def topics():
    config = load_config(CONFIG_PATH)
    return render_cached_or_fresh(load_topics, CONFIG_PATH, config["app"]["topics_output"], "/")


@app.route('/questions')
def questions():
    config = load_config(CONFIG_PATH)
    return render_cached_or_fresh(load_questions, CONFIG_PATH, config["app"]["questions_output"], "/questions")


@app.route('/agents')
def agents_topics():
    config = load_config(AGENTS_CONFIG_PATH)
    return render_cached_or_fresh(load_topics, AGENTS_CONFIG_PATH, config["app"]["topics_output"], "/agents")


@app.route('/agents/questions')
def agents_questions():
    config = load_config(AGENTS_CONFIG_PATH)
    return render_cached_or_fresh(
        load_questions,
        AGENTS_CONFIG_PATH,
        config["app"]["questions_output"],
        "/agents/questions",
    )


@app.route('/refresh', methods=['POST'])
def refresh():
    next_path = request.form.get("next") or "/"
    config_path = AGENTS_CONFIG_PATH if next_path.startswith("/agents") else CONFIG_PATH
    clear_runtime_cache(config_path)
    return redirect(next_path)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/cv.ini", help="Path to INI config file")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    CONFIG_PATH = args.config
    config = load_config(CONFIG_PATH)
    app.run(host=config["server"]["host"], port=config.getint("server", "port"))
