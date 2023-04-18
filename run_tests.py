
import pytest
def run_all_tests():
    """Run the tests."""
    TEST_PATH='./etmfa/tests/unit/test_attr_soa.py'
    exit_code = pytest.main([TEST_PATH, '-x', '--verbose','-s','--durations=100'])
    return exit_code 
if __name__ == '__main__':
    run_all_tests()