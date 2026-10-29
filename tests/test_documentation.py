"""Regression checks for experiment/source mappings and actual HTML coverage."""

import json
import os
from pathlib import Path

import pytest

from tools.check_docs import ROOT, check_html, check_source_correspondence


@pytest.fixture
def source_tree(tmp_path):
    entries = json.loads((ROOT / "examples/manifest.json").read_text(encoding="utf-8"))
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples/manifest.json").write_text(json.dumps(entries), encoding="utf-8")
    for entry in entries:
        source = tmp_path / entry["source"]
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("EXPERIMENT_KEY = " + repr(entry["experiment_key"]), encoding="utf-8")
        relative = Path(entry["source"]).relative_to("examples").with_suffix(".rst")
        for language in ("en", "zh_CN"):
            page = tmp_path / "docs" / language / relative
            page.parent.mkdir(parents=True, exist_ok=True)
            include = os.path.relpath(source, page.parent).replace("\\", "/")
            page.write_text(
                ".. sdk-parameters:: {}\n\n.. literalinclude:: {}\n".format(
                    entry["experiment_key"], include
                ),
                encoding="utf-8",
            )
    return tmp_path


def test_repository_experiments_match_examples_and_both_languages():
    assert check_source_correspondence() == 35


def test_missing_experiment_page_is_detected(source_tree):
    (source_tree / "docs/en/triangulum/circuit.rst").unlink()
    with pytest.raises(AssertionError, match="Missing experiment pages"):
        check_source_correspondence(source_tree)


def test_wrong_documented_source_is_detected(source_tree):
    page = source_tree / "docs/en/triangulum/circuit.rst"
    page.write_text(page.read_text().replace("circuit.py", "physical.py"), encoding="utf-8")
    with pytest.raises(AssertionError, match="Documented example differs"):
        check_source_correspondence(source_tree)


def test_example_key_drift_is_detected(source_tree):
    source = source_tree / "examples/triangulum/circuit.py"
    source.write_text('EXPERIMENT_KEY = "triangulum.physical"', encoding="utf-8")
    with pytest.raises(AssertionError, match="EXPERIMENT_KEY differs"):
        check_source_correspondence(source_tree)


@pytest.fixture
def html_tree(tmp_path):
    for language in ("en", "zh_CN"):
        source = tmp_path / language
        source.mkdir()
        (source / "index.rst").write_text("Index\n=====\n", encoding="utf-8")
        output = tmp_path / "_build/html" / language
        output.mkdir(parents=True)
        other = "zh_CN" if language == "en" else "en"
        (output / "index.html").write_text(
            '<a hreflang="{0}" href="../{0}/index.html">Language</a>'
            '<h1 id="intro">Intro</h1><a href="#intro">Intro</a>'.format(other),
            encoding="utf-8",
        )
    return tmp_path


def test_empty_build_cannot_pass_link_validation(tmp_path):
    with pytest.raises(AssertionError, match="Build documentation first"):
        check_html(tmp_path)


def test_html_fragments_are_checked(html_tree):
    page = html_tree / "_build/html/en/index.html"
    page.write_text(page.read_text() + '<a href="#missing">Bad link</a>', encoding="utf-8")
    with pytest.raises(AssertionError, match="Broken local anchor"):
        check_html(html_tree)


def test_language_switch_requires_the_same_page(html_tree):
    output = html_tree / "_build/html/en"
    (output / "other.html").write_text("Other page", encoding="utf-8")
    page = html_tree / "_build/html/zh_CN/index.html"
    page.write_text(page.read_text().replace("en/index.html", "en/other.html"), encoding="utf-8")
    with pytest.raises(AssertionError, match="different page"):
        check_html(html_tree)


def test_complete_html_with_valid_fragments_passes(html_tree):
    assert check_html(html_tree) == 2
