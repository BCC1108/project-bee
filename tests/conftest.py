import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def sample_strategy():
    try:
        from project_bee.core.strategy import Strategy
        return Strategy(name='hq3.5', params={'window': 20, 'stddev': 2})
    except:
        return None
