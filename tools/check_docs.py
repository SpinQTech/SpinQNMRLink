"""Check code/source correspondence, paired pages and built HTML links offline."""

import argparse
import ast
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.switches = []
        self.anchors = set()

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if values.get("id"):
            self.anchors.add(values["id"])
        if tag == "a" and values.get("name"):
            self.anchors.add(values["name"])
        if tag == "a" and "href" in values:
            self.links.append(values["href"])
            if "hreflang" in values:
                self.switches.append(values["href"])


def check_source_correspondence(root=ROOT):
    """Require each actual experiment to have the correct example and paired page."""
    from spinqnmrlink import list_experiments

    catalogue = {entry.key: entry for entry in list_experiments()}
    manifest = json.loads((root / "examples/manifest.json").read_text(encoding="utf-8"))
    entries = {entry["experiment_key"]: entry for entry in manifest}
    assert len(entries) == len(manifest), "Duplicate experiment keys in example manifest"
    assert entries.keys() == catalogue.keys(), "Example manifest differs from the SDK catalogue"
    for key, entry in entries.items():
        assert entry["device"] == catalogue[key].device_type, "Example device differs: " + key
        assert entry["mode"] == catalogue[key].mode, "Example mode differs: " + key
        path = root / entry["source"]
        assert path.is_file(), "Missing example source: " + str(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        keys = [
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "EXPERIMENT_KEY"
                    for target in node.targets)
        ]
        assert keys == [key], "Example EXPERIMENT_KEY differs from manifest: " + str(path)

    paired = []
    for language in ("zh_CN", "en"):
        pages = {}
        directory = root / "docs" / language
        for path in directory.rglob("*.rst"):
            content = path.read_text(encoding="utf-8")
            keys = re.findall(r"^\.\. sdk-parameters::\s+(\S+)\s*$", content, re.M)
            if not keys:
                continue
            assert len(keys) == 1, "Experiment page must document one exact key: " + str(path)
            key = keys[0]
            assert key in catalogue, "Unknown documented experiment key: " + key
            assert key not in pages, "Duplicate experiment page for " + key
            includes = re.findall(r"^\.\. literalinclude::\s+(.+?)\s*$", content, re.M)
            expected = (root / entries[key]["source"]).resolve()
            assert expected in [(path.parent / value).resolve() for value in includes], (
                "Documented example differs from manifest: " + str(path)
            )
            pages[key] = path.relative_to(directory)
        assert pages.keys() == catalogue.keys(), "Missing experiment pages in " + language
        paired.append(pages)
    assert paired[0] == paired[1], "Experiment keys appear on different language pages"
    return len(catalogue)


def check_html(source, output_root=None):
    output_root = source / "_build/html" if output_root is None else output_root.resolve()
    sets = [
        {
            x.relative_to(source / language)
            for x in (source / language).rglob("*")
            if x.suffix in (".rst", ".md")
        }
        for language in ("zh_CN", "en")
    ]
    assert sets[0] == sets[1], "Language page sets differ"
    parsed_pages = {}

    def parse(path):
        path = path.resolve()
        if path not in parsed_pages:
            parser = Links()
            parser.feed(path.read_text(encoding="utf-8"))
            parsed_pages[path] = parser
        return parsed_pages[path]

    count = 0
    for language in ("zh_CN", "en"):
        output = output_root / language
        assert output.is_dir(), "Build documentation first; missing output: " + str(output)
        for page in sets[0]:
            assert (output / page.with_suffix(".html")).is_file(), "Missing built page: " + str(page)
        for path in output.rglob("*.html"):
            if "_static" in path.parts:
                continue
            parser = parse(path)
            assert len(parser.switches) == 1, "Missing language switch: " + str(path)
            target = (path.parent / parser.switches[0]).resolve()
            assert target.is_file(), "Broken language switch: " + str(target)
            other = "en" if language == "zh_CN" else "zh_CN"
            expected = output_root / other / path.relative_to(output)
            assert target == expected.resolve(), "Language switch goes to a different page: " + str(path)
            for link in parser.links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc:
                    continue
                destination = path.parent / unquote(parsed.path) if parsed.path else path
                assert destination.exists(), "Broken local link: {} -> {}".format(path, link)
                if parsed.fragment and destination.suffix == ".html":
                    assert unquote(parsed.fragment) in parse(destination).anchors, (
                        "Broken local anchor: {} -> {}".format(path, link)
                    )
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-dir", type=Path)
    args = parser.parse_args()
    experiments = check_source_correspondence()
    count = check_html(ROOT / "docs", args.html_dir)
    print("Code, examples and paired documentation agree for {} experiments".format(experiments))
    print("Paired sources and local/language links passed for {} HTML pages".format(count))


if __name__ == "__main__":
    main()
