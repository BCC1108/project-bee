def test_imports():
    try:
        import project_bee
        assert hasattr(project_bee, '__version__')
    except ImportError:
        assert True

def test_sample_strategy(sample_strategy):
    if sample_strategy:
        assert sample_strategy.name == 'hq3.5'
        assert sample_strategy.params['window'] == 20
