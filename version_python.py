import sys

def show_python_version():
    """
    """
    version_info = sys.version_info
    print(f"Повна інформація про версію Python: {sys.version}")

    major_version = version_info.major
    minor_version = version_info.minor
    micro_version = version_info.micro

    print(f"Основна версія (Major): {major_version}")
    print(f"Друга версія (Minor): {minor_version}")
    print(f"Патч-версія (Micro): {micro_version}")
    
    return (major_version, minor_version, micro_version)

def check_python_version(expected_major, expected_minor):
    """
    """
    current_version = show_python_version()
    if current_version[0] <= expected_major and current_version[1] <= expected_minor:
        print("PASS version Phython")
    else:
        print("FAIL version Phython")

def date():
    from datetime import date
    print("Copyright (c) 2014 - %d | Tech " % date.today().year)

if __name__ == "__main__":

    check_python_version(3, 8)