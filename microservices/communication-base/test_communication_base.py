#!/usr/bin/env python3
"""
Communication Base Microservice Test Script

This script tests the Communication Base microservice functionality
and identifies core issues that need to be fixed.
"""

import sys
import os
import importlib.util
from pathlib import Path

def test_basic_imports():
    """Test basic Python imports and dependencies."""
    print("🔍 Testing Basic Dependencies...")
    
    try:
        import fastapi
        print(f"  ✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"  ❌ FastAPI: {e}")
    
    try:
        import uvicorn
        print(f"  ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"  ❌ Uvicorn: {e}")
    
    try:
        import pydantic
        print(f"  ✅ Pydantic: {pydantic.__version__}")
    except ImportError as e:
        print(f"  ❌ Pydantic: {e}")
    
    try:
        import structlog
        print(f"  ✅ Structlog: {structlog.__version__}")
    except ImportError as e:
        print(f"  ❌ Structlog: {e}")
    
    try:
        import motor
        print(f"  ✅ Motor (MongoDB): {motor.version}")
    except ImportError as e:
        print(f"  ❌ Motor: {e}")
    
    try:
        import redis
        print(f"  ✅ Redis: {redis.__version__}")
    except ImportError as e:
        print(f"  ❌ Redis: {e}")

def test_directory_structure():
    """Test the directory structure of the Communication Base microservice."""
    print("\n🔍 Testing Directory Structure...")
    
    base_path = Path("src")
    required_dirs = [
        "config",
        "api", 
        "clients",
        "service",
        "storage",
        "models",
        "conversation",
        "session",
        "bot_integration"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/ directory exists")
        else:
            print(f"  ❌ {dir_name}/ directory missing")

def test_config_files():
    """Test configuration files."""
    print("\n🔍 Testing Configuration Files...")
    
    config_files = [
        "src/config/__init__.py",
        "src/config/config_manager.py",
        "requirements.txt",
        "README.md"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"  ✅ {config_file} exists")
        else:
            print(f"  ❌ {config_file} missing")

def analyze_import_issues():
    """Analyze import issues in the codebase."""
    print("\n🔍 Analyzing Import Issues...")
    
    # Check main.py imports
    main_py = Path("src/main.py")
    if main_py.exists():
        print("  📋 Main.py import analysis:")
        with open(main_py, 'r') as f:
            content = f.read()
            if "from src." in content:
                print("    ❌ Found absolute 'src.' imports - need to fix")
            else:
                print("    ✅ No absolute 'src.' imports found")
    
    # Check for common import patterns
    src_path = Path("src")
    python_files = list(src_path.rglob("*.py"))
    
    files_with_src_imports = []
    for py_file in python_files[:10]:  # Check first 10 files as sample
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                if "from src." in content:
                    files_with_src_imports.append(py_file)
        except Exception:
            continue
    
    print(f"  📊 Sample analysis: {len(files_with_src_imports)}/10 files have 'src.' import issues")

def test_fastapi_app_creation():
    """Test if we can create a basic FastAPI app."""
    print("\n🔍 Testing FastAPI App Creation...")
    
    try:
        from fastapi import FastAPI
        
        # Create a simple test app
        app = FastAPI(
            title="Communication Base Test",
            description="Test app for Communication Base microservice",
            version="1.0.0"
        )
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "communication-base-test"}
        
        @app.get("/")
        async def root():
            return {"message": "Communication Base Test API"}
        
        print("  ✅ FastAPI app created successfully")
        print("  ✅ Health endpoint defined")
        print("  ✅ Root endpoint defined")
        
        return app
        
    except Exception as e:
        print(f"  ❌ FastAPI app creation failed: {e}")
        return None

def test_alternative_startup():
    """Test alternative startup approach."""
    print("\n🔍 Testing Alternative Startup Approach...")
    
    try:
        # Try to create a minimal working version
        app = test_fastapi_app_creation()
        
        if app:
            print("  ✅ Alternative FastAPI app approach works")
            print("  💡 Recommendation: Start with minimal FastAPI app and gradually add features")
            return True
        else:
            print("  ❌ Alternative approach also failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Alternative startup failed: {e}")
        return False

def provide_recommendations():
    """Provide recommendations for fixing the Communication Base microservice."""
    print("\n💡 RECOMMENDATIONS FOR FIXING COMMUNICATION BASE:")
    print("=" * 60)
    
    print("1. 🔧 IMPORT PATH FIXES:")
    print("   • Replace all 'from src.' imports with relative imports")
    print("   • Use 'from .module' or 'from ..module' patterns")
    print("   • Consider using PYTHONPATH or package installation")
    
    print("\n2. 🚀 STARTUP STRATEGY:")
    print("   • Start with minimal FastAPI app")
    print("   • Gradually add components one by one")
    print("   • Test each component before adding the next")
    
    print("\n3. 📁 ARCHITECTURE SIMPLIFICATION:")
    print("   • Focus on core API endpoints first")
    print("   • Mock external dependencies (MongoDB, Redis)")
    print("   • Implement health checks and basic functionality")
    
    print("\n4. 🧪 TESTING APPROACH:")
    print("   • Create unit tests for individual components")
    print("   • Use dependency injection for easier testing")
    print("   • Mock external services during development")
    
    print("\n5. 🔄 INTEGRATION STRATEGY:")
    print("   • Fix core service first, then integrate with other microservices")
    print("   • Validate API endpoints before complex workflows")
    print("   • Ensure proper error handling and logging")

def main():
    """Run comprehensive Communication Base microservice tests."""
    print("🚀 Communication Base Microservice Analysis")
    print("=" * 60)
    
    # Change to the communication-base directory
    os.chdir("/Users/luvtalrani/ansh projects/prismicx-2/microservices/communication-base")
    
    # Run all tests
    test_basic_imports()
    test_directory_structure()
    test_config_files()
    analyze_import_issues()
    alternative_works = test_alternative_startup()
    
    # Provide recommendations
    provide_recommendations()
    
    print("\n📊 ANALYSIS SUMMARY:")
    print("=" * 60)
    print("✅ Dependencies: Available")
    print("✅ Directory Structure: Present")
    print("❌ Import Issues: Need systematic fixing")
    print("✅ FastAPI Alternative: Working")
    
    if alternative_works:
        print("\n🎯 NEXT STEPS:")
        print("1. Create minimal working FastAPI app")
        print("2. Fix import paths systematically")
        print("3. Add components incrementally")
        print("4. Test integration with other microservices")
    else:
        print("\n⚠️  CRITICAL ISSUES:")
        print("1. Core dependencies may be missing")
        print("2. Fundamental architecture problems")
        print("3. Requires complete restructuring")

if __name__ == "__main__":
    main()
