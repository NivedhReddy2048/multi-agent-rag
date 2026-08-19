# Contributing to EKIP

Thank you for your interest in contributing to the Educational Knowledge Intelligence Platform (EKIP)!

## Development Workflow

1. Fork and clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the full integration test suite to verify stability:
   ```bash
   python -m pytest tests/test_knowledge_synthesis.py tests/test_student_workspace.py tests/test_knowledge_verification.py tests/test_learning_modules.py tests/test_production_engineering.py tests/test_multi_user_platform.py
   ```
4. Create a feature branch and submit a Pull Request.
