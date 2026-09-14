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
