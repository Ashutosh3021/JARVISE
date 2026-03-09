"""
Project Detector Module

Detects project type, language, test commands, and git status.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectInfo:
    """Container for project detection results."""
    language: str
    framework: Optional[str]
    test_command: Optional[str]
    build_command: Optional[str]
    project_root: str
    has_git: bool
    git_branch: Optional[str] = None
    git_modified: Optional[list[str]] = None
    
    def __post_init__(self):
        if self.git_modified is None:
            self.git_modified = []


# Project markers for detection
PROJECT_MARKERS = {
    # Python
    "python": {
        "files": ["setup.py", "pyproject.toml", "requirements.txt", "setup.cfg"],
        "test": "pytest",
    },
    # Node.js
    "nodejs": {
        "files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "test": "npm test",
        "build": "npm run build",
    },
    # Rust
    "rust": {
        "files": ["Cargo.toml", "Cargo.lock"],
        "test": "cargo test",
        "build": "cargo build",
    },
    # Go
    "go": {
        "files": ["go.mod", "go.sum"],
        "test": "go test ./...",
        "build": "go build",
    },
    # C/C++
    "cpp": {
        "files": ["Makefile", "CMakeLists.txt", "*.pro"],
        "test": None,
        "build": "make",
    },
    # C# (.NET)
    "csharp": {
        "files": ["*.csproj", "*.sln"],
        "test": "dotnet test",
        "build": "dotnet build",
    },
    # Java
    "java": {
        "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "test": "mvn test",
        "build": "mvn build",
    },
    # Ruby
    "ruby": {
        "files": ["Gemfile", "Gemfile.lock"],
        "test": "rake test",
        "build": "bundle exec rake",
    },
    # PHP
    "php": {
        "files": ["composer.json", "composer.lock"],
        "test": "phpunit",
        "build": None,
    },
}


def detect_project(path: str = ".") -> ProjectInfo:
    """
    Detect project type by scanning for known markers.
    
    Args:
        path: Path to scan for project files
        
    Returns:
        ProjectInfo with detected project details
    """
    search_path = Path(path).resolve()
    
    # Find project root first
    root = get_project_root(search_path)
    
    # Detect language/framework
    language = "unknown"
    framework = None
    
    # Check each project type
    for lang, markers in PROJECT_MARKERS.items():
        for marker in markers["files"]:
            # Handle file patterns
            if "*" in marker:
                # Glob pattern
                if list(root.glob(marker)):
                    language = lang
                    break
            else:
                # Exact file match
                if (root / marker).exists():
                    language = lang
                    break
        
        if language != "unknown":
            break
    
    # Get test and build commands
    test_command = None
    build_command = None
    
    if language != "unknown" and language in PROJECT_MARKERS:
        test_command = PROJECT_MARKERS[language].get("test")
        build_command = PROJECT_MARKERS[language].get("build")
        
        # Special case for Python with pytest
        if language == "python" and test_command == "pytest":
            # Check if pytest is available
            test_command = "python -m pytest"
        
        # Special case for Node.js - check package.json for actual scripts
        if language == "nodejs":
            pkg_json = root / "package.json"
            if pkg_json.exists():
                try:
                    import json
                    with open(pkg_json) as f:
                        pkg = json.load(f)
                        scripts = pkg.get("scripts", {})
                        if "test" in scripts:
                            test_command = "npm test"
                        if "build" in scripts:
                            build_command = "npm run build"
                        # Detect framework from dependencies
                        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                        if "react" in deps:
                            framework = "react"
                        elif "vue" in deps:
                            framework = "vue"
                        elif "@angular/core" in deps:
                            framework = "angular"
                        elif "next" in deps:
                            framework = "next"
                except Exception:
                    pass
    
    # Check for git
    has_git = has_git_repo(root)
    git_branch = None
    git_modified = []
    
    if has_git:
        git_info = get_git_status(root)
        git_branch = git_info.get("branch")
        git_modified = git_info.get("modified", [])
    
    return ProjectInfo(
        language=language,
        framework=framework,
        test_command=test_command,
        build_command=build_command,
        project_root=str(root),
        has_git=has_git,
        git_branch=git_branch,
        git_modified=git_modified,
    )


def get_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the project root by looking for common markers.
    
    Searches up from start_path until finding a marker.
    """
    if start_path is None:
        start_path = Path.cwd()
    
    path = start_path.resolve()
    
    # Markers that indicate project root
    markers = [
        ".git",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "CMakeLists.txt",
        "Makefile",
    ]
    
    # Walk up from current directory
    while path != path.parent:
        for marker in markers:
            if (path / marker).exists():
                return path
        path = path.parent
    
    # Fall back to start_path
    return start_path


def get_test_command(project_path: str = ".") -> Optional[str]:
    """
    Get the appropriate test command for the project.
    
    Args:
        project_path: Path to the project
        
    Returns:
        Test command string or None if not detectable
    """
    project = detect_project(project_path)
    return project.test_command


def has_git_repo(path: Optional[Path] = None) -> bool:
    """
    Check if the current directory is in a git repository.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        True if in a git repository
    """
    if path is None:
        path = Path.cwd()
    
    # Walk up looking for .git directory
    search_path = path.resolve()
    while search_path != search_path.parent:
        if (search_path / ".git").is_dir():
            return True
        search_path = search_path.parent
    
    return False


def get_git_status(path: Optional[Path] = None) -> dict:
    """
    Get git status information for the repository.
    
    Args:
        path: Path within the git repository
        
    Returns:
        Dict with branch name and modified files
    """
    result = {
        "branch": None,
        "modified": [],
        "staged": [],
        "untracked": [],
    }
    
    if path is None:
        path = Path.cwd()
    
    # Find git root
    git_root = path
    if not has_git_repo(path):
        return result
    
    # Walk up to find .git
    search_path = path.resolve()
    while search_path != search_path.parent:
        if (search_path / ".git").is_dir():
            git_root = search_path
            break
        search_path = search_path.parent
    
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if branch_result.returncode == 0:
            result["branch"] = branch_result.stdout.strip()
        
        # Get modified files
        modified_result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if modified_result.returncode == 0:
            result["modified"] = [
                f for f in modified_result.stdout.strip().split("\n") if f
            ]
        
        # Get staged files
        staged_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if staged_result.returncode == 0:
            result["staged"] = [
                f for f in staged_result.stdout.strip().split("\n") if f
            ]
        
        # Get untracked files
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if untracked_result.returncode == 0:
            result["untracked"] = [
                f for f in untracked_result.stdout.strip().split("\n") if f
            ]
            
    except Exception:
        pass
    
    return result


__all__ = [
    "ProjectInfo",
    "detect_project",
    "get_test_command",
    "get_project_root",
    "has_git_repo",
    "get_git_status",
]
