#!/usr/bin/env python
"""
Breathe ESG — Test Runner

Allows running the comprehensive Django test suite (`backend/tests.py`)
without needing a full manage.py or a pre-configured database.
It sets up the Django environment dynamically, runs the tests with a memory-only
SQLite database, and reports failures.

Usage:
  python backend/run_tests.py
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add project root directory to path to enable proper 'backend' resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    # 1. Setup Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    # 2. Initialize Django
    django.setup()
    
    # 3. Retrieve the test runner (default Django test runner)
    TestRunner = get_runner(settings)
    
    # 4. Instantiate the test runner with no/minimal extra arguments
    test_runner = TestRunner(verbosity=2, interactive=False, failfast=False)
    
    # 5. Run the tests targeting the backend package
    failures = test_runner.run_tests(['backend'])
    
    # 6. Exit with code 1 if failures exist, otherwise 0
    sys.exit(bool(failures))

if __name__ == '__main__':
    main()
