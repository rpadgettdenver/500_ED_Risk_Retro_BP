"""
Suggested File Name: run_all_tests.py
File Location: /Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP/tests/
Use: Run all integration tests and generate comprehensive test report

This script runs all test suites and provides a summary report.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = '/Users/robertpadgett/Projects/01_My_Notebooks/500_ED_Risk_Retro_BP'
sys.path.insert(0, project_root)


def run_test_suite(test_name: str, test_module: str):
    """Run a single test suite"""
    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")
    
    try:
        if test_module == 'integration':
            from test_integration_suite import IntegrationTestSuite
            suite = IntegrationTestSuite()
            return suite.run_all_tests()
            
        elif test_module == 'consistency':
            from test_python_bigquery_consistency import PythonBigQueryConsistencyTest
            tester = PythonBigQueryConsistencyTest()
            tester.run_consistency_test()
            return True
            
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test suites"""
    print("="*80)
    print("🧪 ENERGIZE DENVER COMPREHENSIVE TEST RUNNER")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Define test suites
    test_suites = [
        ("Integration Test Suite", "integration"),
        ("Python-BigQuery Consistency Test", "consistency")
    ]
    
    # Track results
    results = {
        'total': len(test_suites),
        'passed': 0,
        'failed': 0
    }
    
    # Run each test suite
    for test_name, test_module in test_suites:
        success = run_test_suite(test_name, test_module)
        
        if success:
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL TEST SUMMARY")
    print("="*80)
    print(f"Total Test Suites: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results['failed'] == 0:
        print("\n🎉 ALL TEST SUITES PASSED!")
        print("The Energize Denver system is working correctly with the corrected penalty rates.")
    else:
        print(f"\n⚠️  {results['failed']} test suite(s) failed. Please review the errors above.")
    
    print("\n📁 Test results saved in: tests/test_results/")
    print("="*80)
    
    return results['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
