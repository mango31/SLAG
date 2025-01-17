def test_worker_imports():
    """Test that worker modules can be imported"""
    from src.worker import run_worker
    from src.worker import story_worker
    assert run_worker
    assert story_worker

if __name__ == "__main__":
    test_worker_imports()
    print("All imports successful!") 