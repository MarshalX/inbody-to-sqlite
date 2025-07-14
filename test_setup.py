#!/usr/bin/env python3
"""Test script to validate the InBody to SQLite setup."""

import os
import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print('🧪 Testing imports...')

    try:
        from inbody_to_sqlite.models import InBodyResult, SegmentalAnalysis  # noqa: F401

        print('✅ Models imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import models: {e}')
        return False

    try:
        from inbody_to_sqlite.database import InBodyDatabase  # noqa: F401

        print('✅ Database module imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import database: {e}')
        return False

    try:
        from inbody_to_sqlite.image_processor import InBodyImageProcessor  # noqa: F401

        print('✅ Image processor imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import image processor: {e}')
        return False

    try:
        from inbody_to_sqlite.main import InBodyProcessor  # noqa: F401

        print('✅ Main processor imported successfully')
    except ImportError as e:
        print(f'❌ Failed to import main processor: {e}')
        return False

    return True


def test_database():
    """Test database initialization."""
    print('\n🗄️  Testing database...')

    try:
        from inbody_to_sqlite.database import InBodyDatabase

        # Test database creation
        db = InBodyDatabase('test.db')
        print('✅ Database initialized successfully')

        # Test getting stats
        stats = db.get_processing_stats()
        print(f'✅ Database stats: {stats}')

        # Clean up test database
        test_db_path = Path('test.db')
        if test_db_path.exists():
            test_db_path.unlink()
            print('✅ Test database cleaned up')

        return True
    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False


def test_environment():
    """Test environment setup."""
    print('\n🌍 Testing environment...')

    # Check for .env.example
    if Path('.env.example').exists():
        print('✅ .env.example file exists')
    else:
        print('❌ .env.example file missing')

    # Check if .env exists (optional)
    if Path('.env').exists():
        print('✅ .env file exists')

        # Check for API key (without revealing it)
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print('✅ OPENAI_API_KEY is set')
        else:
            print('⚠️  OPENAI_API_KEY not found in .env')
    else:
        print('⚠️  .env file not found (create one from .env.example)')

    # Check images folder
    if Path('images').exists():
        print('✅ Images folder exists')
    else:
        print('⚠️  Images folder not found')

    return True


def test_dependencies():
    """Test that all dependencies are available."""
    print('\n📦 Testing dependencies...')

    try:
        import openai  # noqa: F401

        print('✅ OpenAI library available')
    except ImportError:
        print('❌ OpenAI library not installed')
        return False

    try:
        import pydantic  # noqa: F401

        print('✅ Pydantic library available')
    except ImportError:
        print('❌ Pydantic library not installed')
        return False

    try:
        from PIL import Image  # noqa: F401

        print('✅ Pillow library available')
    except ImportError:
        print('❌ Pillow library not installed')
        return False

    try:
        from dotenv import load_dotenv  # noqa: F401

        print('✅ python-dotenv library available')
    except ImportError:
        print('❌ python-dotenv library not installed')
        return False

    return True


def main():
    """Run all tests."""
    print('🚀 InBody to SQLite Setup Validation')
    print('=' * 40)

    tests = [
        test_dependencies,
        test_imports,
        test_database,
        test_environment,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f'💥 Test {test.__name__} crashed: {e}')

    print('\n' + '=' * 40)
    print(f'📊 Results: {passed}/{total} tests passed')

    if passed == total:
        print('🎉 All tests passed! Setup is ready.')
        print('\nNext steps:')
        print("1. Add your InBody scan images to the 'images' folder")
        print('2. Set up your OpenAI API key in .env')
        print('3. Run: python -m inbody_to_sqlite ./images')
    else:
        print('⚠️  Some tests failed. Please check the output above.')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
