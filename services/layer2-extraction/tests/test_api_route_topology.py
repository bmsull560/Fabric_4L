from pathlib import Path


ROUTE_MODULES = [
    Path('services/layer2-extraction/src/layer2_extraction/api/routes/extraction.py'),
    Path('services/layer2-extraction/src/layer2_extraction/api/routes/jobs.py'),
    Path('services/layer2-extraction/src/layer2_extraction/api/routes/health.py'),
]


def test_route_modules_do_not_import_app_main_directly() -> None:
    for module in ROUTE_MODULES:
        text = module.read_text()
        assert 'from .. import main' not in text
        assert 'import layer2_extraction.api.main' not in text
