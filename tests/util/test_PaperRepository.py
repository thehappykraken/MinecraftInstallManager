import os
import pytest
import re

minecraft_versions = ['1.21.11', '1.21.x', '1.x.x', '26.2', '26.x', '26.x.x', 'x.x', 'x.x.x']

# spec -> (versions the search must return, versions it must not return).
# Exact regex behavior is covered offline by tests/util/test_version_pattern.py;
# this pins the spec semantics against what PaperMC actually publishes.
search_expectations = [
    ('1.21.11', ['1.21.11'], ['1.21', '1.21.10', '26.2']),
    ('1.21.x', ['1.21', '1.21.4', '1.21.11'], ['1.20.6', '26.2']),
    ('1.x.x', ['1.21', '1.21.11', '1.8.8'], ['26.2', '26.1.2']),
    ('26.2', ['26.2'], ['26.1.2', '1.21.11']),
    ('26.x', ['26.2'], ['26.1.2', '1.21.11']),
    ('26.x.x', ['26.2', '26.1.2'], ['1.21.11']),
    ('x.x', ['1.21', '26.2'], ['1.21.11', '26.1.2']),
    ('x.x.x', ['1.21', '1.21.11', '26.2', '26.1.2'], []),
]

def test_list_paper_servers(paper_repository):
    servers = paper_repository.list()
    assert len(servers) > 0
    for server in servers:
        assert server.repository == paper_repository
        assert server.name.startswith('Paper')
        assert server.server_version is not None
        assert server.minecraft_version is not None

@pytest.mark.parametrize("minecraft_version", minecraft_versions)
def test_search_paper_servers(paper_repository, minecraft_version):
    versions = paper_repository.search(minecraft_version=minecraft_version)
    assert versions is not None
    assert len(versions) > 0
    for version in versions:
        assert version.repository == paper_repository
        # Searches resolve to memoized Server instances, never fresh objects
        assert version in paper_repository.list()
        # Only concrete releases, never pre-releases such as 26.3-rc-3
        assert re.fullmatch(r'\d+(\.\d+)+', version.server_version)

@pytest.mark.parametrize("minecraft_version,included,excluded", search_expectations)
def test_search_paper_servers_spec_semantics(paper_repository, minecraft_version, included, excluded):
    found = {server.minecraft_version for server in paper_repository.search(minecraft_version=minecraft_version)}
    assert set(included) <= found
    assert not (set(excluded) & found)

def test_paper_repository_install(paper_repository, tmp_path):
    servers = paper_repository.list()
    paper_server = servers[0]
    file = paper_repository.install(paper_server, tmp_path)
    assert file is not None
    assert os.path.isfile(file)
