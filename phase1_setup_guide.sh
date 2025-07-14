#!/bin/bash
# =============================================================================
# PHASE 1: AGENTORCHESTRA SETUP SCRIPT
# =============================================================================

# File: setup_phase1.sh
# Purpose: Automated setup script for Phase 1 fixes

set -e  # Exit on any error

echo "🚀 AgentOrchestra Phase 1 Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is installed
check_python() {
    print_info "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION found"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    print_status "pip3 found"
}

# Create virtual environment
create_venv() {
    print_info "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    print_status "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        print_info "Please create requirements.txt with the dependencies from the artifacts"
        exit 1
    fi
    
    pip install -r requirements.txt
    print_status "Dependencies installed"
    
    # Install development dependencies if available
    if [ -f "requirements-dev.txt" ]; then
        read -p "Install development dependencies? (y/N): " install_dev
        if [[ $install_dev =~ ^[Yy]$ ]]; then
            pip install -r requirements-dev.txt
            print_status "Development dependencies installed"
        fi
    fi
}

# Setup environment variables
setup_environment() {
    print_info "Setting up environment variables..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status ".env file created from .env.example"
        else
            # Create basic .env file
            cat > .env << EOF
# Flask Configuration
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///agentorchestra.db

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Application Settings
TASK_QUEUE_SIZE=1000
METRICS_RETENTION_HOURS=24
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Service Settings
ORCHESTRATION_WORKER_THREADS=4
TASK_EXECUTION_TIMEOUT=300
HEALTH_CHECK_INTERVAL=30

# External Services
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
EOF
            print_status ".env file created with secure defaults"
        fi
    else
        print_warning ".env file already exists"
    fi
    
    # Validate SECRET_KEY
    if grep -q "your-super-secret-key-change-this" .env 2>/dev/null; then
        print_warning "Please update the SECRET_KEY in .env file"
        # Generate new secret key
        NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i.bak "s/your-super-secret-key-change-this/$NEW_SECRET/" .env
        print_status "SECRET_KEY updated with secure random value"
    fi
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    # Create necessary directories
    mkdir -p src/models
    mkdir -p src/utils
    mkdir -p src/routes
    mkdir -p src/services
    mkdir -p static
    mkdir -p logs
    mkdir -p instance
    
    # Create __init__.py files
    touch src/__init__.py
    touch src/models/__init__.py
    touch src/utils/__init__.py
    touch src/routes/__init__.py
    touch src/services/__init__.py
    
    print_status "Directory structure created"
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    
    # Check if setup_database.py exists
    if [ -f "setup_database.py" ]; then
        python3 setup_database.py
        print_status "Database initialized"
    else
        print_warning "setup_database.py not found"
        print_info "You can initialize the database manually after creating the script"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Test import of main modules
    python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from src.models.database import db
    print('✅ Database module imports successfully')
except ImportError as e:
    print(f'❌ Database module import failed: {e}')
    exit(1)

try:
    from src.utils.validation import AgentSchema
    print('✅ Validation module imports successfully')
except ImportError as e:
    print(f'❌ Validation module import failed: {e}')
    exit(1)

try:
    from src.config import get_config
    print('✅ Configuration module imports successfully')
except ImportError as e:
    print(f'❌ Configuration module import failed: {e}')
    exit(1)

print('✅ All core modules verified')
"
    
    if [ $? -eq 0 ]; then
        print_status "Installation verification passed"
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

# Test basic functionality
test_application() {
    print_info "Testing application startup..."
    
    # Set test environment
    export SECRET_KEY="test-secret-key"
    export FLASK_ENV="testing"
    
    # Test app creation
    python3 -c "
from main import create_app
try:
    app, socketio = create_app('testing')
    print('✅ Application creates successfully')
    
    with app.app_context():
        from src.models.database import db
        db.create_all()
        print('✅ Database tables create successfully')
        
except Exception as e:
    print(f'❌ Application test failed: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_status "Application test passed"
    else
        print_error "Application test failed"
        exit 1
    fi
}

# Main setup function
main() {
    echo "Starting Phase 1 setup process..."
    echo
    
    # Run setup steps
    check_python
    create_venv
    
    # Activate virtual environment for the rest of the script
    source venv/bin/activate
    
    install_dependencies
    create_directories
    setup_environment
    init_database
    verify_installation
    test_application
    
    echo
    echo "🎉 Phase 1 setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Start the application: python main.py"
    echo "3. Open browser to: http://localhost:5000"
    echo
    echo "Development commands:"
    echo "- Run tests: pytest"
    echo "- Format code: black ."
    echo "- Check types: mypy src/"
    echo
}

# Run main function
main

# =============================================================================
# File: verify_phase1.py
# Purpose: Python verification script for Phase 1 fixes
# =============================================================================

#!/usr/bin/env python3
"""
Verification script for AgentOrchestra Phase 1 fixes
This script checks that all critical issues have been resolved
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, success: bool = True):
    """Print colored status message"""
    color = Colors.GREEN if success else Colors.RED
    symbol = "✅" if success else "❌"
    print(f"{color}{symbol} {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return (project_root / file_path).exists()

def check_import(module_name: str) -> Tuple[bool, str]:
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)

def verify_circular_imports() -> bool:
    """Verify that circular imports are fixed"""
    print_info("Checking circular import fixes...")
    
    # Check that database.py exists
    if not check_file_exists("src/models/database.py"):
        print_status("database.py file missing", False)
        return False
    
    # Check that models import from database.py
    try:
        from src.models.database import db
        print_status("Database import successful")
        
        from src.models.user import User
        from src.models.agent import Agent
        from src.models.workflow import Workflow
        print_status("All model imports successful")
        
        return True
    except ImportError as e:
        print_status(f"Import failed: {e}", False)
        return False

def verify_missing_models() -> bool:
    """Verify that missing model files are created"""
    print_info("Checking missing model files...")
    
    required_models = [
        "src/models/database.py",
        "src/models/user.py", 
        "src/models/agent.py",
        "src/models/workflow.py"
    ]
    
    all_exist = True
    for model_file in required_models:
        if check_file_exists(model_file):
            print_status(f"{model_file} exists")
        else:
            print_status(f"{model_file} missing", False)
            all_exist = False
    
    # Check model classes exist
    try:
        from src.models.workflow import Workflow, WorkflowExecution, WorkflowStep, Task
        print_status("All workflow models available")
    except ImportError as e:
        print_status(f"Workflow models import failed: {e}", False)
        all_exist = False
    
    return all_exist

def verify_input_validation() -> bool:
    """Verify that input validation is implemented"""
    print_info("Checking input validation...")
    
    # Check validation files exist
    validation_files = [
        "src/utils/__init__.py",
        "src/utils/validation.py",
        "src/utils/responses.py"
    ]
    
    all_exist = True
    for val_file in validation_files:
        if check_file_exists(val_file):
            print_status(f"{val_file} exists")
        else:
            print_status(f"{val_file} missing", False)
            all_exist = False
    
    # Check validation imports
    try:
        from src.utils.validation import AgentSchema, TaskSchema, WorkflowSchema
        from src.utils.validation import validate_json
        print_status("Validation schemas and decorators available")
    except ImportError as e:
        print_status(f"Validation import failed: {e}", False)
        all_exist = False
    
    # Check response utilities
    try:
        from src.utils.responses import success_response, error_response
        print_status("Response utilities available")
    except ImportError as e:
        print_status(f"Response utilities import failed: {e}", False)
        all_exist = False
    
    return all_exist

def verify_secure_configuration() -> bool:
    """Verify that secure configuration is implemented"""
    print_info("Checking secure configuration...")
    
    # Check config file exists
    if not check_file_exists("src/config.py"):
        print_status("config.py missing", False)
        return False
    
    # Check configuration import
    try:
        from src.config import get_config, BaseConfig, DevelopmentConfig, ProductionConfig
        print_status("Configuration classes available")
    except ImportError as e:
        print_status(f"Configuration import failed: {e}", False)
        return False
    
    # Check environment file
    if check_file_exists(".env.example"):
        print_status(".env.example template exists")
    else:
        print_warning(".env.example template missing")
    
    # Check SECRET_KEY requirement
    try:
        config = get_config('production')
        # This should fail if SECRET_KEY is not set
        test_secret = config.SECRET_KEY
        if test_secret and len(test_secret) > 20:
            print_status("SECRET_KEY configuration secure")
        else:
            print_warning("SECRET_KEY may not be properly configured")
    except Exception:
        print_status("Production config requires SECRET_KEY (this is correct)")
    
    return True

def verify_updated_main() -> bool:
    """Verify that main.py is updated properly"""
    print_info("Checking main application...")
    
    if not check_file_exists("main.py"):
        print_status("main.py missing", False)
        return False
    
    # Check main application can be imported
    try:
        from main import create_app
        print_status("Main application imports successfully")
    except ImportError as e:
        print_status(f"Main application import failed: {e}", False)
        return False
    
    # Test app creation with testing config
    try:
        os.environ['SECRET_KEY'] = 'test-secret-key-for-verification'
        app, socketio = create_app('testing')
        print_status("Application creates successfully")
        
        # Test database creation
        with app.app_context():
            from src.models.database import db
            db.create_all()
            print_status("Database tables create successfully")
        
        return True
    except Exception as e:
        print_status(f"Application creation failed: {e}", False)
        return False

def check_requirements() -> bool:
    """Check that requirements.txt has necessary dependencies"""
    print_info("Checking requirements...")
    
    if not check_file_exists("requirements.txt"):
        print_status("requirements.txt missing", False)
        return False
    
    required_packages = [
        'Flask',
        'Flask-SQLAlchemy', 
        'Flask-CORS',
        'Flask-SocketIO',
        'marshmallow',
        'python-dotenv',
        'requests'
    ]
    
    try:
        with open(project_root / "requirements.txt", 'r') as f:
            requirements_content = f.read()
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements_content:
                missing_packages.append(package)
        
        if missing_packages:
            print_status(f"Missing packages in requirements.txt: {missing_packages}", False)
            return False
        else:
            print_status("All required packages in requirements.txt")
            return True
            
    except Exception as e:
        print_status(f"Could not read requirements.txt: {e}", False)
        return False

def main():
    """Main verification function"""
    print(f"{Colors.BOLD}🔍 AgentOrchestra Phase 1 Verification{Colors.ENDC}")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all verification checks
    checks = [
        ("Circular Import Fixes", verify_circular_imports),
        ("Missing Model Files", verify_missing_models), 
        ("Input Validation", verify_input_validation),
        ("Secure Configuration", verify_secure_configuration),
        ("Updated Main Application", verify_updated_main),
        ("Requirements File", check_requirements)
    ]
    
    for check_name, check_function in checks:
        print(f"\n{Colors.BOLD}{check_name}:{Colors.ENDC}")
        try:
            result = check_function()
            if not result:
                all_checks_passed = False
        except Exception as e:
            print_status(f"Check failed with exception: {e}", False)
            all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 50)
    if all_checks_passed:
        print_status("🎉 All Phase 1 checks passed! Your fixes are working correctly.")
        print_info("You can now proceed to Phase 2 (Service Architecture)")
        return 0
    else:
        print_status("❌ Some checks failed. Please review the issues above.", False)
        print_info("Fix the failing checks before proceeding to Phase 2")
        return 1

if __name__ == '__main__':
    sys.exit(main())

# =============================================================================
# File: PHASE1_CHECKLIST.md
# Purpose: Phase 1 implementation checklist
# =============================================================================

# Phase 1: Critical Fixes Implementation Checklist

## ✅ Files to Create/Update

### 1. Database and Models
- [ ] `src/models/database.py` - Centralized database instance
- [ ] `src/models/user.py` - Updated user model with fixed imports
- [ ] `src/models/agent.py` - Updated agent models with fixed imports  
- [ ] `src/models/workflow.py` - **NEW** Complete workflow models

### 2. Input Validation
- [ ] `src/utils/__init__.py` - Make utils a package
- [ ] `src/utils/validation.py` - Marshmallow schemas and decorators
- [ ] `src/utils/responses.py` - Standardized API responses

### 3. Configuration Management
- [ ] `src/config.py` - Secure configuration classes
- [ ] `.env.example` - Environment variable template
- [ ] `.gitignore` - Updated gitignore for security

### 4. Application Updates
- [ ] `main.py` - Updated main application with security
- [ ] `requirements.txt` - Updated dependencies
- [ ] `requirements-dev.txt` - Development dependencies

### 5. Setup and Verification
- [ ] `setup_database.py` - Database initialization script
- [ ] `setup_phase1.sh` - Automated setup script
- [ ] `verify_phase1.py` - Verification script

## 🔧 Implementation Steps

### Step 1: Backup Current Code
```bash
# Create backup of current code
cp -r . ../agentorchestra-backup
```

### Step 2: Create New Files
1. Create all files from the artifacts above
2. Ensure proper directory structure:
   ```
   src/
   ├── models/
   │   ├── __init__.py
   │   ├── database.py
   │   ├── user.py
   │   ├── agent.py
   │   └── workflow.py
   └── utils/
       ├── __init__.py
       ├── validation.py
       └── responses.py
   ```

### Step 3: Update Existing Files
1. Replace `main.py` with new secure version
2. Update `requirements.txt` 
3. Create `.env` from `.env.example`

### Step 4: Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Set Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env and set secure SECRET_KEY
# You can generate one with:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 6: Initialize Database
```bash
# Run database setup
python3 setup_database.py
```

### Step 7: Verify Implementation
```bash
# Run verification script
python3 verify_phase1.py

# Test application startup
python3 main.py
```

## 🚨 Critical Points to Remember

1. **SECRET_KEY**: Must be set in environment variables
2. **Database**: All models now import from `src.models.database`
3. **Validation**: All API endpoints should use validation decorators
4. **Responses**: Use standardized response format
5. **Configuration**: Use environment-based configuration

## 🎯 Success Criteria

- [ ] Application starts without import errors
- [ ] Database tables create successfully  
- [ ] All model imports work correctly
- [ ] Validation schemas are functional
- [ ] Configuration loads from environment
- [ ] No hardcoded secrets in code
- [ ] Verification script passes all checks

## 🚀 Next Steps After Phase 1

Once Phase 1 is complete and verified:
1. Test basic API endpoints
2. Verify database operations
3. Check validation on API calls
4. Proceed to Phase 2 (Service Architecture)

---

**Time Estimate**: 2-4 hours
**Difficulty**: Medium  
**Impact**: Critical - Fixes foundation issues