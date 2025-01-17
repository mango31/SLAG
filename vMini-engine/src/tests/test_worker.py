import pytest
from src.worker.story_worker import StoryWorker
from src.worker.run_worker import main

def test_worker_module_imports():
    """Test that worker modules can be imported"""
    assert StoryWorker
    assert main 