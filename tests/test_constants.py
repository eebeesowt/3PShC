"""Тесты на детектор моделей и фильтры под input/test-pattern профиль.
Чистая логика, никаких внешних зависимостей.
"""
import pytest

from core.constants import ProjectorStates as S


# ---- detect_input_profile ----


@pytest.mark.parametrize("model,expected", [
    # DIRECT_RZ — старые WUXGA RZ-серии и старые RQ без SDM
    ("RZ120", S.PROFILE_DIRECT_RZ),
    ("RZ970", S.PROFILE_DIRECT_RZ),
    ("FRZ120C", S.PROFILE_DIRECT_RZ),
    ("RQ22K", S.PROFILE_DIRECT_RZ),
    ("RQ32K", S.PROFILE_DIRECT_RZ),
    ("RQ50K", S.PROFILE_DIRECT_RZ),
    ("RQ13K", S.PROFILE_DIRECT_RZ),
    # SDM_RQ25 — серия 2022-2023 с обязательным SDM-слотом
    ("RQ25K", S.PROFILE_SDM_RQ25),
    ("SRQ25KC", S.PROFILE_SDM_RQ25),
    ("RQ18K", S.PROFILE_SDM_RQ25),
    ("SRQ18KC", S.PROFILE_SDM_RQ25),
    ("RZ24K", S.PROFILE_SDM_RQ25),
    ("RZ17K", S.PROFILE_SDM_RQ25),
    # HYBRID_RQ7 — RZ7/RZ6/RQ7/RQ6 серии (PT-RQ7L, PT-RQ7LBEJ и пр.)
    ("RZ7L", S.PROFILE_HYBRID_RQ7),
    ("RZ6", S.PROFILE_HYBRID_RQ7),
    ("RQ7L", S.PROFILE_HYBRID_RQ7),
    ("RQ7LBEJ", S.PROFILE_HYBRID_RQ7),
    ("RQ6", S.PROFILE_HYBRID_RQ7),
    # Граничные случаи: цифры не должны путать regex
    ("RZ240", S.PROFILE_DIRECT_RZ),     # не RZ24
    ("RQ70K", S.PROFILE_DIRECT_RZ),     # не RQ7
    ("RQ250K", S.PROFILE_DIRECT_RZ),    # не RQ25
    # Unknown — пустая строка или совсем не Panasonic
    ("", S.PROFILE_UNKNOWN),
    ("XYZ123", S.PROFILE_UNKNOWN),
])
def test_detect_input_profile(model, expected):
    assert S.detect_input_profile(model) == expected


# ---- input_sources_for_model ----


def test_direct_rz_inputs_have_dvi_no_sdm():
    inputs = S.input_sources_for_model('RZ120')
    assert 'DVI-D (direct)' in inputs
    assert 'COMPUTER1/RGB1 (direct)' in inputs
    assert 'SDI1 (direct)' in inputs
    # Никаких SLOT-входов на RZ120 быть не должно
    assert not any('SLOT:' in name for name in inputs)


def test_sdm_rq25_inputs_have_displayport_and_slots_only():
    inputs = S.input_sources_for_model('RQ25K')
    assert 'DisplayPort' in inputs
    assert 'SLOT: 12G SDI (SDM)' in inputs
    assert 'SLOT: PressIT (SDM)' in inputs
    # Прямые SDI/DVI/RGB на RQ25K отсутствуют
    assert 'SDI1 (direct)' not in inputs
    assert 'DVI-D (direct)' not in inputs
    assert 'COMPUTER1/RGB1 (direct)' not in inputs


def test_hybrid_rq7_has_direct_dl_plus_slots():
    inputs = S.input_sources_for_model('RQ7LBEJ')
    assert 'HDMI1' in inputs
    assert 'Digital Link (direct)' in inputs   # уникальная RQ7-фишка
    assert 'SLOT: 12G SDI (SDM)' in inputs
    # Но DisplayPort и DVI на RQ7-серии нет
    assert 'DisplayPort' not in inputs
    assert 'DVI-D (direct)' not in inputs


def test_unknown_model_shows_full_list():
    inputs = S.input_sources_for_model('')
    assert inputs == S.INPUT_SOURCES


# ---- test_patterns_for_model ----


def test_direct_rz_has_convergence_no_focus_level():
    patterns = S.test_patterns_for_model('RZ120')
    assert 'Convergence' in patterns
    assert 'Focus Level 0%' not in patterns
    assert 'Focus Level 50%' not in patterns


def test_sdm_rq25_no_convergence_has_focus_level():
    patterns = S.test_patterns_for_model('RQ25K')
    assert 'Convergence' not in patterns
    assert 'Focus Level 0%' in patterns
    assert 'Focus Level 100%' in patterns


def test_hybrid_rq7_excludes_both_convergence_and_focus_level():
    """PT-RQ7-серия (RZ7/RZ6/RQ7/RQ6): по PDF нет ни OTS:11, ни OTS:32/33/34.
    Focus Level — эксклюзив SDM_RQ25 серии."""
    patterns = S.test_patterns_for_model('RQ7L')
    assert 'Convergence' not in patterns
    assert 'Focus Level 0%' not in patterns
    assert 'Focus Level 50%' not in patterns
    assert 'Focus Level 100%' not in patterns
    # Универсальные паттерны должны остаться
    assert 'Off' in patterns
    assert 'Cross Hatch' in patterns
    assert 'Focus' in patterns  # OTS:78 — не путать с Focus Level


def test_unknown_model_shows_full_test_pattern_list():
    assert S.test_patterns_for_model('') == S.TEST_PATTERNS


# ---- detect_family (display label) ----


@pytest.mark.parametrize("model,expected", [
    ('RZ120', S.FAMILY_RZ),
    ('RZ24K', S.FAMILY_RZ),
    ('RQ25K', S.FAMILY_RQ),
    ('RQ7LBEJ', S.FAMILY_RQ),
    ('SRQ25KC', S.FAMILY_RQ),
    ('', S.FAMILY_UNKNOWN),
    ('XYZ', S.FAMILY_UNKNOWN),
])
def test_detect_family(model, expected):
    assert S.detect_family(model) == expected
