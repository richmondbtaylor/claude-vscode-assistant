import json
import random

from vidforge.prompts import build_batch, expand, load_prompt_file, load_wildcards


def test_alternation_picks_one_option():
    rng = random.Random(0)
    for _ in range(20):
        assert expand("a {red|blue} car", rng=rng) in ("a red car", "a blue car")


def test_alternation_nests():
    rng = random.Random(1)
    results = {expand("{neon {pink|blue}|daylight}", rng=rng) for _ in range(60)}
    assert results <= {"neon pink", "neon blue", "daylight"}
    assert len(results) > 1


def test_wildcard_files_resolve(tmp_path):
    (tmp_path / "camera.txt").write_text("# comment\ndolly in\n\npan left\n")
    table = load_wildcards(tmp_path)
    assert table == {"camera": ["dolly in", "pan left"]}
    assert expand("shot: __camera__", table) in ("shot: dolly in", "shot: pan left")


def test_unknown_wildcard_is_left_alone():
    assert expand("shot: __nope__", {}) == "shot: __nope__"


def test_build_batch_crosses_prompts_and_seeds():
    items = build_batch(["a", "b"], seeds=[1, 2, 3])
    assert len(items) == 6
    assert {seed for _, seed in items} == {1, 2, 3}


def test_variants_produce_distinct_seeds():
    items = build_batch(["a"], variants=8, rng=random.Random(7))
    assert len(items) == 8
    assert len({seed for _, seed in items}) == 8


def test_explicit_seeds_beat_variants():
    assert len(build_batch(["a"], variants=5, seeds=[42])) == 1


def test_load_prompt_file_formats(tmp_path):
    txt = tmp_path / "p.txt"
    txt.write_text("# skip me\nfirst prompt\n\nsecond prompt\n")
    assert load_prompt_file(txt) == ["first prompt", "second prompt"]

    js = tmp_path / "p.json"
    js.write_text(json.dumps([{"prompt": "from object"}, "from string"]))
    assert load_prompt_file(js) == ["from object", "from string"]

    jl = tmp_path / "p.jsonl"
    jl.write_text('{"prompt": "one"}\n{"text": "two"}\n')
    assert load_prompt_file(jl) == ["one", "two"]
