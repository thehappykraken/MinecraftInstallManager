from mpm.util.Repository import Plugin
import pytest
import os

spiget_plugins = [
    ('Death Chest','101066'),
    # ('GlobalEffects','113887')
]

@pytest.mark.parametrize("plugin_name,plugin_id", spiget_plugins)
def test_search_spiget_plugins(spiget_repository, plugin_name, plugin_id):
    versions = spiget_repository.search(plugin=Plugin(plugin_name,plugin_id))
    assert versions is not None
    assert len(versions) > 0
    for version in versions:
        assert version.repository == spiget_repository
        assert version.version is not None

@pytest.mark.parametrize("plugin_name,plugin_id", spiget_plugins)
def test_searchall_spiget_plugins(spiget_repository, plugin_name, plugin_id):
    versions = spiget_repository.searchAll(plugin=Plugin(plugin_name,plugin_id))
    assert versions is not None
    assert len(versions) > 0
    assert any(version.repository == spiget_repository for version in versions)
    assert all(version.version is not None for version in versions)

@pytest.mark.parametrize("plugin_name,plugin_id", spiget_plugins)
def test_spiget_repository_install(spiget_repository, plugin_name, plugin_id, tmp_path):
    plugin = Plugin(plugin_name,plugin_id)
    versions = spiget_repository.search(plugin=plugin)
    files = versions[-1].install(tmp_path)
    assert files
    for file in files:
        assert file is not None
        assert os.path.isfile(file)

@pytest.mark.parametrize("plugin_name,plugin_id", spiget_plugins)
def test_spiget_plugin_installed_versions(spiget_repository, plugin_name, plugin_id, tmp_path):
    plugin = Plugin(plugin_name,plugin_id)
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