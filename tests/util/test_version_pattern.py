import pytest
import re

from src.mim.util.Repository import version_pattern

# Concrete versions spanning the legacy 1.X.Y numbering, the current X.Y / X.Y.Z
# numbering, and the pre-release spellings PaperMC also publishes.
samples = [
    '1.7.10', '1.8.8', '1.13', '1.21', '1.21.4', '1.21.11',
    '26.1.1', '26.1.2', '26.2', '26.3',
    '1.13-pre7', '1.21.11-rc3', '26.3-rc-3',
]

# spec -> the exact set of samples it must full-match
expected_matches = {
    # legacy specs keep working exactly as before
    '1.21.11': {'1.21.11'},
    '1.21.x': {'1.21', '1.21.4', '1.21.11'},
    '1.x': {'1.13', '1.21'},
    '1.x.x': {'1.7.10', '1.8.8', '1.13', '1.21', '1.21.4', '1.21.11'},
    # current numbering
    '26.2': {'26.2'},
    '26.x': {'26.2', '26.3'},
    '26.1.x': {'26.1.1', '26.1.2'},
    '26.x.x': {'26.1.1', '26.1.2', '26.2', '26.3'},
    # fully wildcarded specs span both schemes
    'x.x': {'1.13', '1.21', '26.2', '26.3'},
    'x.x.x': {'1.7.10', '1.8.8', '1.13', '1.21', '1.21.4', '1.21.11',
              '26.1.1', '26.1.2', '26.2', '26.3'},
}

@pytest.mark.parametrize("spec,expected", sorted(expected_matches.items()))
def test_version_pattern_matches(spec, expected):
    pattern = version_pattern(spec)
    matched = {s for s in samples if re.fullmatch(pattern, s)}
    assert matched == expected

@pytest.mark.parametrize("spec", sorted(expected_matches))
def test_version_pattern_excludes_prereleases(spec):
    pattern = version_pattern(spec)
    for prerelease in ['1.13-pre7', '1.21.11-rc3', '26.3-rc-3']:
        assert not re.fullmatch(pattern, prerelease)

def test_version_pattern_escapes_literal_separators():
    # The '.' separators are literal, not the regex any-character wildcard
    assert not re.fullmatch(version_pattern('1.21.4'), '1x21x4')
    assert not re.fullmatch(version_pattern('26.2'), '2662')
