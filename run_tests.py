#!/usr/bin/env python3
"""
Script để chạy tất cả tests cho VPS Manager
"""

import os
import sys
import subprocess
import argparse

def run_tests(test_type='all', verbose=False, coverage=False):
    """Chạy tests theo loại"""
    
    # Thêm thư mục hiện tại vào Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Cài đặt pytest arguments
    pytest_args = ['python', '-m', 'pytest']
    
    if verbose:
        pytest_args.append('-v')
    
    if coverage:
        pytest_args.extend(['--cov=core', '--cov=ui', '--cov-report=html'])
    
    # Chọn tests theo loại
    if test_type == 'unit':
        pytest_args.extend(['tests/test_*.py', '-k', 'not integration'])
    elif test_type == 'integration':
        pytest_args.extend(['tests/test_api_integration.py'])
    elif test_type == 'api':
        pytest_args.extend(['tests/test_*.py', '-k', 'api'])
    elif test_type == 'models':
        pytest_args.extend(['tests/test_models.py'])
    elif test_type == 'scheduler':
        pytest_args.extend(['tests/test_scheduler.py'])
    elif test_type == 'validation':
        pytest_args.extend(['tests/test_validation.py'])
    elif test_type == 'ui':
        pytest_args.extend(['tests/test_ui_components.py', 'tests/test_javascript_functionality.py'])
    elif test_type == 'forms':
        pytest_args.extend(['tests/test_form_validation.py'])
    elif test_type == 'frontend':
        pytest_args.extend(['tests/test_ui_components.py', 'tests/test_javascript_functionality.py', 'tests/test_form_validation.py'])
    else:
        # Chạy tất cả tests
        pytest_args.append('tests/')
    
    # Thêm arguments khác
    pytest_args.extend([
        '--tb=short',  # Short traceback
        '--strict-markers',  # Strict markers
        '--disable-warnings'  # Disable warnings
    ])
    
    print(f"🚀 Chạy tests: {test_type}")
    print(f"📝 Command: {' '.join(pytest_args)}")
    print("-" * 50)
    
    try:
        # Chạy pytest
        result = subprocess.run(pytest_args, capture_output=False)
        
        if result.returncode == 0:
            print("✅ Tất cả tests đã pass!")
        else:
            print("❌ Một số tests đã fail!")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Lỗi khi chạy tests: {e}")
        return 1

def run_specific_test(test_file):
    """Chạy test file cụ thể"""
    if not os.path.exists(test_file):
        print(f"❌ Test file không tồn tại: {test_file}")
        return 1
    
    pytest_args = ['python', '-m', 'pytest', test_file, '-v']
    
    print(f"🚀 Chạy test file: {test_file}")
    print(f"📝 Command: {' '.join(pytest_args)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(pytest_args, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Lỗi khi chạy test: {e}")
        return 1

def list_tests():
    """Liệt kê tất cả test files"""
    tests_dir = 'tests'
    if not os.path.exists(tests_dir):
        print("❌ Thư mục tests không tồn tại")
        return
    
    print("📋 Danh sách test files:")
    print("-" * 50)
    
    test_files = []
    for file in os.listdir(tests_dir):
        if file.startswith('test_') and file.endswith('.py'):
            test_files.append(file)
    
    if not test_files:
        print("❌ Không tìm thấy test files nào")
        return
    
    for i, file in enumerate(sorted(test_files), 1):
        print(f"{i:2d}. {file}")
    
    print(f"\n📊 Tổng cộng: {len(test_files)} test files")

def check_test_environment():
    """Kiểm tra môi trường test"""
    print("🔍 Kiểm tra môi trường test:")
    print("-" * 50)
    
    # Kiểm tra Python version
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Kiểm tra thư mục tests
    tests_dir = 'tests'
    if os.path.exists(tests_dir):
        test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
        print(f"📁 Tests directory: {tests_dir} ({len(test_files)} files)")
    else:
        print(f"❌ Tests directory: {tests_dir} không tồn tại")
    
    # Kiểm tra pytest
    try:
        import pytest
        print(f"🧪 Pytest: {pytest.__version__}")
    except ImportError:
        print("❌ Pytest chưa được cài đặt")
    
    # Kiểm tra thư mục core
    core_dir = 'core'
    if os.path.exists(core_dir):
        core_files = [f for f in os.listdir(core_dir) if f.endswith('.py')]
        print(f"📁 Core directory: {core_dir} ({len(core_files)} files)")
    else:
        print(f"❌ Core directory: {core_dir} không tồn tại")
    
    # Kiểm tra thư mục ui
    ui_dir = 'ui'
    if os.path.exists(ui_dir):
        ui_files = [f for f in os.listdir(ui_dir) if f.endswith('.py')]
        print(f"📁 UI directory: {ui_dir} ({len(ui_files)} files)")
    else:
        print(f"❌ UI directory: {ui_dir} không tồn tại")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='VPS Manager Test Runner')
    parser.add_argument('--type', '-t', choices=['all', 'unit', 'integration', 'api', 'models', 'scheduler', 'validation', 'ui', 'forms', 'frontend'], 
                       default='all', help='Loại test để chạy')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Chạy với coverage report')
    parser.add_argument('--list', '-l', action='store_true', help='Liệt kê test files')
    parser.add_argument('--check', action='store_true', help='Kiểm tra môi trường test')
    parser.add_argument('--file', '-f', help='Chạy test file cụ thể')
    
    args = parser.parse_args()
    
    print("🧪 VPS Manager Test Runner")
    print("=" * 50)
    
    if args.check:
        check_test_environment()
        return 0
    
    if args.list:
        list_tests()
        return 0
    
    if args.file:
        return run_specific_test(args.file)
    
    return run_tests(args.type, args.verbose, args.coverage)

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 