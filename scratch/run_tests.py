import unittest
import sys

with open("scratch/test_results.txt", "w", encoding="utf-8") as f:
    runner = unittest.TextTestRunner(stream=f, verbosity=2)
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_step2c_relevance_gating.py")
    result = runner.run(suite)
    print(f"Tests run: {result.testsRun}, Errors: {len(result.errors)}, Failures: {len(result.failures)}")
