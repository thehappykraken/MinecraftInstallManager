import os
import pytest
import re

minecraft_versions = ['1.21.11', '1.21.x', '26.2', 'x.x']

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
    re_comp = re.compile(minecraft_version.replace('x','\d*'))
    assert versions is not None
    assert len(versions) > 0
    for version in versions:
        assert version.repository == paper_repository
        assert re_comp.fullmatch(version.server_version)

def test_paper_repository_install(paper_repository, tmp_path):
    servers = paper_repository.list()
    paper_server = servers[0]
    file = paper_repository.install(paper_server, tmp_path)
    assert file is not None
    assert os.path.isfile(file)
