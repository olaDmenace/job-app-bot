#!/usr/bin/env python3
"""
System Requirements Checker for Job Application Bot

This script checks if your system meets the requirements to run the Job Application Bot.
"""

import os
import sys
import platform
import subprocess
import shutil
import json

def print_banner():
    """Print banner"""
    print("\n" + "=" * 80)
    print(" Job Application Bot - System Requirements Checker ".center(80, "="))
    print("=" * 80)

def check_python_version():
    """Check Python version"""
    print("\n📊 Python Version:")
    
    major, minor, micro = sys.version_info[:3]
    version_str = f"{major}.{minor}.{micro}"
    
    MIN_PYTHON = (3, 8, 0)
    if sys.version_info < MIN_PYTHON:
        print(f"❌ Python {version_str} detected. This project requires Python {'.'.join(map(str, MIN_PYTHON))} or higher.")
        return False
    
    print(f"✅ Python {version_str} detected (required: {'.'.join(map(str, MIN_PYTHON))} or higher)")
    return True

def check_chrome_installation():
    """Check if Chrome is installed"""
    print("\n🌐 Chrome Browser:")
    
    # Check Chrome on different platforms
    chrome_installed = False
    chrome_version = "Not detected"
    
    system = platform.system()
    if system == "Windows":
        try:
            # Check Chrome on Windows
            from winreg import HKEY_CURRENT_USER, OpenKey, QueryValueEx
            with OpenKey(HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon") as key:
                chrome_version = QueryValueEx(key, "version")[0]
                chrome_installed = True
        except:
            # Alternative check using 'where'
            try:
                result = subprocess.run(["where", "chrome"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True, 
                                      check=True)
                if result.stdout:
                    chrome_installed = True
                    chrome_version = "Version unknown"
            except:
                pass
    elif system == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, "--version"], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True, 
                                          check=True)
                    chrome_version = result.stdout.strip()
                    chrome_installed = True
                    break
                except:
                    pass
    else:  # Linux
        try:
            chrome_executable = shutil.which("google-chrome") or shutil.which("chrome")
            if chrome_executable:
                result = subprocess.run([chrome_executable, "--version"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True, 
                                      check=True)
                chrome_version = result.stdout.strip()
                chrome_installed = True
        except:
            pass
    
    if chrome_installed:
        print(f"✅ Chrome is installed: {chrome_version}")
        return True
    else:
        print("❌ Chrome is not installed or could not be detected.")
        print("   Please install Chrome from https://www.google.com/chrome/")
        return False

def check_chromedriver():
    """Check if ChromeDriver is installed"""
    print("\n🔧 ChromeDriver:")
    
    # Check for ChromeDriver in project's drivers directory
    system = platform.system()
    driver_filename = "chromedriver.exe" if system == "Windows" else "chromedriver"
    driver_path = os.path.join("drivers", driver_filename)
    
    if os.path.exists(driver_path):
        try:
            # Verify ChromeDriver by running it with --version flag
            if system != "Windows":
                # Ensure it's executable on Unix-like systems
                subprocess.run(["chmod", "+x", driver_path], check=True)
                
            result = subprocess.run(
                [driver_path, "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ ChromeDriver is installed: {result.stdout.strip()}")
                return True
        except:
            pass
    
    # Check ChromeDriver in PATH
    chromedriver_in_path = shutil.which("chromedriver")
    if chromedriver_in_path:
        try:
            result = subprocess.run(
                [chromedriver_in_path, "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            if result.returncode == 0:
                print(f"✅ ChromeDriver found in PATH: {result.stdout.strip()}")
                print(f"   Location: {chromedriver_in_path}")
                
                # Suggest copying it to the drivers directory
                print(f"   Consider copying it to {os.path.abspath('drivers')} for the application to use.")
                return True
        except:
            pass
    
    print("❌ ChromeDriver not found.")
    print("   Please download ChromeDriver from https://chromedriver.chromium.org/downloads")
    print(f"   and place it in the '{os.path.abspath('drivers')}' directory.")
    
    # Create drivers directory if it doesn't exist
    if not os.path.exists("drivers"):
        try:
            os.makedirs("drivers")
            print("   'drivers' directory created.")
        except:
            print("   Failed to create 'drivers' directory.")
    
    return False

def check_selenium():
    """Check if Selenium is installed"""
    print("\n🤖 Selenium:")
    
    try:
        import selenium
        print(f"✅ Selenium is installed (version: {selenium.__version__})")
        return True
    except ImportError:
        print("❌ Selenium is not installed.")
        print("   Please install it with: pip install selenium")
        return False

def check_dependencies():
    """Check other dependencies"""
    print("\n📦 Other Dependencies:")
    
    dependencies = {
        "pandas": "Data manipulation",
        "python-dotenv": "Environment variables",
        "requests": "HTTP requests",
        "beautifulsoup4": "HTML parsing",
        "lxml": "XML processing",
        "tqdm": "Progress bars"
    }
    
    all_installed = True
    
    for package, description in dependencies.items():
        try:
            module = __import__(package.replace("-", "_"))
            version = getattr(module, "__version__", "Unknown")
            print(f"✅ {package} is installed (version: {version}) - {description}")
        except ImportError:
            print(f"❌ {package} is not installed - {description}")
            print(f"   Please install it with: pip install {package}")
            all_installed = False
    
    return all_installed

def check_disk_space():
    """Check available disk space"""
    print("\n💾 Disk Space:")
    
    try:
        # Get disk usage of current directory
        if platform.system() == "Windows":
            # Windows-specific code
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.getcwd()), None, None, ctypes.pointer(free_bytes))
            free_gb = free_bytes.value / (1024 ** 3)
        else:
            # Unix-like systems
            import shutil
            total, used, free = shutil.disk_usage(os.getcwd())
            free_gb = free / (1024 ** 3)
        
        # Need at least 500MB for database, browser cache, etc.
        min_space_gb = 0.5
        
        if free_gb < min_space_gb:
            print(f"❌ Low disk space: {free_gb:.2f} GB available (minimum {min_space_gb:.2f} GB recommended)")
            return False
        else:
            print(f"✅ Sufficient disk space: {free_gb:.2f} GB available")
            return True
    except Exception as e:
        print(f"⚠️ Could not check disk space: {str(e)}")
        return True  # Assume it's OK if we can't check

def create_environment_report():
    """Create a JSON report of the environment"""
    print("\n📋 Creating Environment Report...")
    
    report = {
        "timestamp": import_helper("datetime").datetime.now().isoformat(),
        "system": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        },
        "dependencies": {}
    }
    
    # Check key packages
    packages = [
        "selenium", "pandas", "requests", "beautifulsoup4", 
        "python-dotenv", "lxml", "tqdm"
    ]
    
    for package in packages:
        try:
            module = import_helper(package.replace("-", "_"))
            version = getattr(module, "__version__", "Unknown")
            report["dependencies"][package] = {
                "installed": True,
                "version": version
            }
        except ImportError:
            report["dependencies"][package] = {
                "installed": False,
                "version": None
            }
    
    # Save the report
    report_path = "system_check_report.json"
    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to {report_path}")
    except Exception as e:
        print(f"❌ Failed to save report: {str(e)}")
    
    return report

def import_helper(module_name):
    """Helper to import modules"""
    try:
        return __import__(module_name)
    except ImportError:
        return None

def main():
    """Main function"""
    print_banner()
    
    # Run all checks
    python_ok = check_python_version()
    chrome_ok = check_chrome_installation()
    chromedriver_ok = check_chromedriver()
    selenium_ok = check_selenium()
    dependencies_ok = check_dependencies()
    disk_space_ok = check_disk_space()
    
    # Create environment report
    create_environment_report()
    
    # Summary
    print("\n" + "=" * 80)
    print(" Summary ".center(80, "="))
    print("=" * 80)
    
    checks = [
        ("Python Version", python_ok),
        ("Chrome Browser", chrome_ok),
        ("ChromeDriver", chromedriver_ok),
        ("Selenium", selenium_ok),
        ("Dependencies", dependencies_ok),
        ("Disk Space", disk_space_ok)
    ]
    
    for check, status in checks:
        print(f"{check}: {'✅ Pass' if status else '❌ Fail'}")
    
    print("=" * 80)
    
    # Overall status
    if all(status for _, status in checks):
        print("\n✅ Your system meets all requirements!")
        print("\nNext steps:")
        print("1. Run 'python setup.py' to complete the setup")
        print("2. Configure your credentials in the .env file")
        print("3. Start scraping with 'python job_scraper_cli.py'")
    else:
        print("\n⚠️ Your system does not meet all requirements.")
        print("Please fix the issues above before running the job scraper.")
        print("Refer to INSTALLATION.md for detailed setup instructions.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()