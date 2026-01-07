#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
from shutil import which

from setuptools import setup
from setuptools.command.build_py import build_py

# Project paths
SETUP_DIR = Path(__file__).parent.resolve()
PROTO_DIR = SETUP_DIR / "s2clientprotocol"


def find_protoc():
    """Find the protoc compiler executable."""
    # Check environment variable first
    if "PROTOC" in os.environ and Path(os.environ["PROTOC"]).exists():
        return os.environ["PROTOC"]

    # Try to find in PATH
    protoc = which("protoc")
    if protoc:
        return protoc

    sys.exit(
        "ERROR: protoc compiler not found!\n"
        "Please install protobuf compiler:\n"
        "  - Ubuntu/Debian: apt-get install protobuf-compiler\n"
        "  - macOS: brew install protobuf\n"
        "  - Windows: Download from https://github.com/protocolbuffers/protobuf/releases\n"
        "Or set PROTOC environment variable to point to protoc executable."
    )


def get_proto_files(root_dir):
    """Find all .proto files under the root directory."""
    proto_files = []
    for path in Path(root_dir).rglob("*.proto"):
        proto_files.append(path)
    return proto_files


def compile_proto(source, python_out, proto_path):
    """Compile a .proto file to Python using protoc."""
    protoc = find_protoc()

    # Verify protoc version for compatibility warning
    try:
        version_output = subprocess.check_output(
            [protoc, "--version"], stderr=subprocess.STDOUT, text=True
        )
        print(f"Using {version_output.strip()}")
    except subprocess.CalledProcessError:
        pass

    protoc_command = [
        protoc,
        f"--proto_path={proto_path}",
        f"--python_out={python_out}",
        f"--pyi_out={python_out}",
        str(source),
    ]

    print(f"Compiling {source.relative_to(SETUP_DIR)}...")

    try:
        subprocess.run(protoc_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        sys.exit(
            f"\nERROR: Failed to compile {source}\n"
            f"Command: {' '.join(protoc_command)}\n"
            f"Error: {e.stderr}\n"
            f"\nMake sure you have protoc version 3.0 or higher.\n"
            f"For protobuf 6.33 compatibility, version 25.0+ is recommended."
        )


class BuildPy(build_py):
    """Custom build command that compiles .proto files."""

    def run(self):
        """Build Python modules and compile protobuf files."""
        print("\n" + "=" * 70)
        print("Compiling Protocol Buffer files...")
        print("=" * 70 + "\n")

        proto_files = get_proto_files(PROTO_DIR)

        if not proto_files:
            print("WARNING: No .proto files found!")

        for proto_file in proto_files:
            compile_proto(source=proto_file, python_out=SETUP_DIR, proto_path=SETUP_DIR)

        # Ensure __init__.py exists in the package
        init_file = PROTO_DIR / "__init__.py"
        if not init_file.exists():
            print(f"Creating {init_file.relative_to(SETUP_DIR)}...")
            init_file.touch()

        print("\n" + "=" * 70)
        print("Protocol Buffer compilation complete!")
        print("=" * 70 + "\n")

        # Run the standard build
        super().run()


# Minimal setup() call - most config is in pyproject.toml
setup(
    cmdclass={
        "build_py": BuildPy,
    },
)
