from mpm.util.Repository import Plugin
import pytest
import os

modrinth_plugins = [
    'WorldEdit',
    'EssentialsX',
    'QuickShop-Hikari'
]

@pytest.mark.parametrize("plugin_name", modrinth_plugins)
def test_search_modrinth_plugins(modrinth_repository, plugin_name):
    versions = modrinth_repository.search(plugin=Plugin(plugin_name))
    assert versions is not None
    assert len(versions) > 0
    for version in versions:
        assert version.repository == modrinth_repository
        assert version.version is not None

@pytest.mark.parametrize("plugin_name", modrinth_plugins)
def test_searchall_modrinth_plugins(modrinth_repository, plugin_name):
    versions = modrinth_repository.searchAll(plugin=Plugin(plugin_name))
    assert versions is not None
    assert len(versions) > 0
    assert any(version.repository == modrinth_repository for version in versions)
    assert all(version.version is not None for version in versions)

@pytest.mark.parametrize("plugin_name", modrinth_plugins)
def test_modrinth_repository_install(modrinth_repository, plugin_name, tmp_path):
    plugin = Plugin(plugin_name)
    versions = modrinth_repository.search(plugin=plugin)
    files = versions[-1].install(tmp_path)
    assert files
    for file in files:
        assert file is not None
        assert os.path.isfile(file)

@pytest.mark.parametrize("plugin_name", modrinth_plugins)
def test_modrinth_plugin_installed_versions(plugin_name, tmp_path):
    plugin = Plugin(plugin_name)
    versions = plugin.versions
    assert versions is not None
    assert len(versions) > 0
    files = versions[-1].install(tmp_path)
    installed_versions = plugin.installedVersions(tmp_path)
    assert len(installed_versions) == 1
    assert installed_versions[0] == versions[-1]
    for file in files:
        assert file is not None
        assert os.path.isfile(file)