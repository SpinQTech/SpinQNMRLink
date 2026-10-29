"""Shared Sphinx configuration for the paired Chinese and English source trees."""

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "docs/_ext"))
project = "SpinQNMRLink"
author = "SpinQ Technology Co., Ltd."
copyright = "2026, " + author
release = runpy.run_path(str(ROOT / "src/spinqnmrlink/_core/_version.py"))["__version__"]
version = release
language = "en"
extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon", "sdk_parameters"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
templates_path = ["_templates"]
html_css_files = ["sdk.css"]
html_title = project
html_theme_options = {
    "navigation_depth": 3,
    "style_nav_header_background": "#245b8a",
    "version_selector": False,
}
autodoc_typehints = "none"
nitpicky = True


def page_context(app, pagename, templatename, context, doctree):
    current = app.config.language
    target = "en" if current == "zh_CN" else "zh_CN"
    source = Path(current) / Path(pagename).parent
    destination = Path(target) / (pagename + ".html")
    context["language_switch_url"] = os.path.relpath(str(destination), str(source)).replace(
        "\\", "/"
    )
    context["language_switch_label"] = "English" if target == "en" else "中文"


def setup(app):
    app.connect("html-page-context", page_context)
