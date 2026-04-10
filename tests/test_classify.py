"""Tests for tokpipe.classify module."""

import pandas as pd
import pytest
import yaml

from tokpipe.classify import classify, load_rules, _match_rules, _find_text_column


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def df_caption():
    """DataFrame with a 'caption' text column."""
    return pd.DataFrame({
        "caption": [
            "My new keyboard setup is amazing",
            "Learning python for data science",
            "Random vlog about my day",
            "Studying for my university exam",
        ],
        "views": [100, 200, 300, 400],
    })


@pytest.fixture
def custom_rules():
    return {
        "music": ["guitar", "piano", "song"],
        "cooking": ["recipe", "kitchen", "cook"],
    }


# ---------------------------------------------------------------------------
# Default rules
# ---------------------------------------------------------------------------

class TestClassifyDefaultRules:
    def test_keyboard_classified_as_setup(self, df_caption):
        result = classify(df_caption)
        assert result.iloc[0] == "setup"

    def test_python_classified_as_coding(self, df_caption):
        result = classify(df_caption)
        assert result.iloc[1] == "coding"

    def test_university_classified_as_study(self, df_caption):
        result = classify(df_caption)
        assert result.iloc[3] == "study"

    def test_no_match_returns_other(self, df_caption):
        result = classify(df_caption)
        assert result.iloc[2] == "other"

    def test_returns_series(self, df_caption):
        result = classify(df_caption)
        assert isinstance(result, pd.Series)
        assert len(result) == len(df_caption)


# ---------------------------------------------------------------------------
# Custom rules dict
# ---------------------------------------------------------------------------

class TestClassifyCustomRules:
    def test_custom_rules_match(self, custom_rules):
        df = pd.DataFrame({"caption": ["I played guitar and piano today"]})
        result = classify(df, rules=custom_rules)
        assert result.iloc[0] == "music"

    def test_custom_rules_no_match_returns_other(self, custom_rules):
        df = pd.DataFrame({"caption": ["Nothing relevant here"]})
        result = classify(df, rules=custom_rules)
        assert result.iloc[0] == "other"

    def test_custom_rules_override_defaults(self):
        rules = {"mycat": ["keyboard"]}
        df = pd.DataFrame({"caption": ["keyboard review"]})
        result = classify(df, rules=rules)
        assert result.iloc[0] == "mycat"


# ---------------------------------------------------------------------------
# Custom classifier function
# ---------------------------------------------------------------------------

class TestClassifyCustomFn:
    def test_classifier_fn_overrides_rules(self, df_caption):
        result = classify(df_caption, classifier_fn=lambda t: "always_this")
        assert (result == "always_this").all()

    def test_classifier_fn_receives_lowercase_text(self):
        received = []

        def capture(text):
            received.append(text)
            return "x"

        df = pd.DataFrame({"caption": ["HELLO World"]})
        classify(df, classifier_fn=capture)
        assert received[0] == "hello world"

    def test_classifier_fn_with_rules_ignores_rules(self, custom_rules):
        df = pd.DataFrame({"caption": ["guitar song"]})
        result = classify(df, rules=custom_rules, classifier_fn=lambda t: "fn_wins")
        assert result.iloc[0] == "fn_wins"


# ---------------------------------------------------------------------------
# YAML file rules
# ---------------------------------------------------------------------------

class TestClassifyYAML:
    def test_load_rules_from_yaml(self, tmp_path):
        rules_data = {
            "gaming": ["controller", "fps", "console"],
            "art": ["drawing", "paint", "sketch"],
        }
        yaml_path = tmp_path / "rules.yaml"
        yaml_path.write_text(yaml.dump(rules_data))

        loaded = load_rules(yaml_path)
        assert "gaming" in loaded
        assert "controller" in loaded["gaming"]
        assert "art" in loaded
        assert len(loaded["art"]) == 3

    def test_classify_with_yaml_path(self, tmp_path):
        rules_data = {"gaming": ["controller", "console"]}
        yaml_path = tmp_path / "rules.yaml"
        yaml_path.write_text(yaml.dump(rules_data))

        df = pd.DataFrame({"caption": ["Playing on my console"]})
        result = classify(df, rules=str(yaml_path))
        assert result.iloc[0] == "gaming"

    def test_classify_with_yaml_path_object(self, tmp_path):
        rules_data = {"gaming": ["controller"]}
        yaml_path = tmp_path / "rules.yaml"
        yaml_path.write_text(yaml.dump(rules_data))

        df = pd.DataFrame({"caption": ["new controller unboxing"]})
        result = classify(df, rules=yaml_path)
        assert result.iloc[0] == "gaming"

    def test_load_rules_invalid_yaml_raises(self, tmp_path):
        yaml_path = tmp_path / "bad.yaml"
        yaml_path.write_text("- just\n- a\n- list\n")
        with pytest.raises(ValueError, match="YAML must be a dict"):
            load_rules(yaml_path)

    def test_load_rules_lowercases_keywords(self, tmp_path):
        rules_data = {"tech": ["Python", "RUST", "GoLang"]}
        yaml_path = tmp_path / "rules.yaml"
        yaml_path.write_text(yaml.dump(rules_data))

        loaded = load_rules(yaml_path)
        assert loaded["tech"] == ["python", "rust", "golang"]


# ---------------------------------------------------------------------------
# Auto-detection of text column
# ---------------------------------------------------------------------------

class TestFindTextColumn:
    def test_detects_caption(self):
        df = pd.DataFrame({"caption": ["a"], "views": [1]})
        assert _find_text_column(df) == "caption"

    def test_detects_description(self):
        df = pd.DataFrame({"description": ["a"], "views": [1]})
        assert _find_text_column(df) == "description"

    def test_detects_title(self):
        df = pd.DataFrame({"title": ["a"], "views": [1]})
        assert _find_text_column(df) == "title"

    def test_detects_text(self):
        df = pd.DataFrame({"text": ["a"], "views": [1]})
        assert _find_text_column(df) == "text"

    def test_detects_titulo(self):
        df = pd.DataFrame({"titulo": ["a"]})
        assert _find_text_column(df) == "titulo"

    def test_detects_column_containing_candidate(self):
        df = pd.DataFrame({"video_caption": ["a"]})
        assert _find_text_column(df) == "video_caption"

    def test_returns_none_when_no_match(self):
        df = pd.DataFrame({"views": [1], "likes": [2]})
        assert _find_text_column(df) is None

    def test_explicit_text_column_overrides_auto(self):
        df = pd.DataFrame({"caption": ["a"], "my_col": ["b"]})
        result = classify(df, text_column="my_col")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Error when no text column
# ---------------------------------------------------------------------------

class TestNoTextColumnError:
    def test_raises_value_error_no_text_column(self):
        df = pd.DataFrame({"views": [100], "likes": [10]})
        with pytest.raises(ValueError, match="No text column found"):
            classify(df)

    def test_error_lists_available_columns(self):
        df = pd.DataFrame({"views": [1], "likes": [2]})
        with pytest.raises(ValueError, match="views"):
            classify(df)


# ---------------------------------------------------------------------------
# _match_rules picks category with most keyword matches
# ---------------------------------------------------------------------------

class TestMatchRules:
    def test_picks_category_with_most_matches(self):
        rules = {
            "setup": ["keyboard", "monitor", "desk"],
            "coding": ["keyboard", "python"],
        }
        # "keyboard" matches both, but "monitor desk" adds 2 more for setup
        text = "keyboard monitor desk"
        assert _match_rules(text, rules) == "setup"

    def test_single_keyword_match(self):
        rules = {"coding": ["python"], "setup": ["keyboard"]}
        assert _match_rules("python tutorial", rules) == "coding"

    def test_no_match_returns_other(self):
        rules = {"coding": ["python"], "setup": ["keyboard"]}
        assert _match_rules("random content", rules) == "other"

    def test_tie_goes_to_first_category(self):
        # When counts are equal, the first one encountered with that count wins
        rules = {"alpha": ["word"], "beta": ["word"]}
        # "alpha" is iterated first, gets count=1; "beta" also count=1 but
        # not strictly greater, so alpha stays
        assert _match_rules("word", rules) == "alpha"

    def test_handles_empty_text(self):
        rules = {"coding": ["python"]}
        assert _match_rules("", rules) == "other"

    def test_handles_nan_filled_as_empty(self):
        df = pd.DataFrame({"caption": [None, "keyboard setup"]})
        result = classify(df)
        assert result.iloc[0] == "other"
        assert result.iloc[1] == "setup"
