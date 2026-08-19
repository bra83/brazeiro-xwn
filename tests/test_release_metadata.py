from pathlib import Path
import tomllib

import barbara

ROOT=Path(__file__).resolve().parents[1]


def test_pyproject_and_runtime_version_match_final_1_0():
    data=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
    assert data['project']['name']=='motor-barbara'
    assert data['project']['version']=='1.0.0'
    assert barbara.__version__=='1.0.0'


def test_acceptance_matrix_has_no_partial_or_absent_required_item():
    text=(ROOT/'docs'/'RELEASE_1_0_ACCEPTANCE.md').read_text(encoding='utf-8')
    rows=[line for line in text.splitlines() if line.startswith('| ') and '---' not in line and 'Requisito obrigatório' not in line]
    assert rows
    assert all('| COMPLETO |' in row for row in rows)
    assert not any('| PARCIAL |' in row or '| AUSENTE |' in row for row in rows)


def test_release_notes_and_readme_are_present_and_identify_installable_artifact():
    notes=(ROOT/'docs'/'RELEASE_NOTES_1.0.md').read_text(encoding='utf-8')
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    assert 'Motor Barbara 1.0.0' in notes
    assert 'motor-barbara-1.0.0' in readme
    assert 'wheel' in notes.lower() and 'wheel' in readme.lower()
