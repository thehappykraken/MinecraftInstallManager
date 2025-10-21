from src.mpm.util.SpigetRepository import SpigetRepository
from src.mpm.util.PaperRepository import PaperRepository
from src.mpm.util.GithubRepository import GithubRepository
from src.mpm.util.ModrinthRepository import ModrinthRepository
import pytest


@pytest.fixture(autouse=True,scope='session')
def spiget_repository():
    return SpigetRepository()

@pytest.fixture(autouse=True,scope='session')
def paper_repository():
    return PaperRepository()

@pytest.fixture(autouse=True,scope='session')
def github_repository():
    return GithubRepository()

@pytest.fixture(autouse=True,scope='session')
def modrinth_repository():
    return ModrinthRepository()