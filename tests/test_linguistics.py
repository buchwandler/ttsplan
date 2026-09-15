import sys
from types import SimpleNamespace

from ttsplan import PlannerConfig, TTSPlanner
from ttsplan.language import LanguageRun
from ttsplan.linguistics import LinguisticResourcePool, analyze_run_analyses


def test_run_analysis_is_lightweight_and_request_local():
    pool = LinguisticResourcePool()

    class Pipeline:
        def __call__(self, text):
            return [SimpleNamespace(idx=0, text=text, pos_="NOUN", tag_="NN", lemma_=text)]

    pool.pipeline = lambda model, require=False: Pipeline()
    analyses = analyze_run_analyses(
        "hello",
        (LanguageRun("lang-0", 0, 5, "en-us"),),
        PlannerConfig(language="en-us").linguistics.__class__(
            use_spacy=True, spacy_model="fake", require_spacy=True
        ),
        pool,
    )
    assert analyses[0].provider_doc is not None
    assert analyses[0].tokens[0].lemma == "hello"


def test_provider_documents_are_not_serialized():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello world.")
    serialized = plan.to_json()
    assert "provider_doc" not in serialized
    assert "spacy.tokens" not in serialized


def test_default_planner_does_not_load_spacy(monkeypatch):
    def fail_if_loaded(*args, **kwargs):
        raise AssertionError("default planning must not load spaCy")

    monkeypatch.setattr(LinguisticResourcePool, "pipeline", fail_if_loaded)
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello world.")

    assert plan.texts.spoken == "Hello world."
    assert all(token.pos is None and token.tag is None for token in plan.tokens)


def test_spacy_auto_uses_fake_compatible_local_model(monkeypatch):
    loaded_models = []

    class Pipeline:
        def __init__(self):
            self.last_doc = None

        def __call__(self, text):
            self.last_doc = [
                SimpleNamespace(idx=0, text=text, pos_="NOUN", tag_="NN", lemma_=text.lower())
            ]
            return self.last_doc

    pipeline = Pipeline()

    fake_spacy = SimpleNamespace(
        util=SimpleNamespace(get_installed_models=lambda: ["en_core_web_sm"]),
        load=lambda model: loaded_models.append(model) or pipeline,
    )
    monkeypatch.setitem(sys.modules, "spacy", fake_spacy)

    analysis = LinguisticResourcePool().analyze(
        "Hello",
        LanguageRun("lang-0", 0, 5, "en-us"),
        PlannerConfig(language="en-us").linguistics.__class__(use_spacy=True),
    )

    assert loaded_models == ["en_core_web_sm"]
    assert analysis.model_name == "en_core_web_sm"
    assert analysis.provider_doc is pipeline.last_doc
    assert analysis.tokens[0].pos == "NOUN"
