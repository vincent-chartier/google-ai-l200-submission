"""Tests for Terraform Infrastructure as Code (IaC) configurations and Containerization."""

import os
import shutil
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TERRAFORM_DIR = REPO_ROOT / "terraform"
MODULES_DIR = TERRAFORM_DIR / "modules"
ENVIRONMENTS_DIR = TERRAFORM_DIR / "environments"


def test_terraform_directory_structure():
    """Verifies that all required modular directories and files exist."""
    assert TERRAFORM_DIR.exists(), "terraform/ directory must exist"
    assert (TERRAFORM_DIR / "main.tf").exists()
    assert (TERRAFORM_DIR / "variables.tf").exists()
    assert (TERRAFORM_DIR / "outputs.tf").exists()
    assert (TERRAFORM_DIR / "versions.tf").exists()
    assert (TERRAFORM_DIR / "terraform.tfvars.example").exists()
    assert (TERRAFORM_DIR / "README.md").exists()

    expected_modules = [
        "apis",
        "iam",
        "secrets",
        "storage",
        "registry",
        "networking",
        "cloud_run",
        "monitoring",
    ]
    for mod in expected_modules:
        mod_dir = MODULES_DIR / mod
        assert mod_dir.exists(), f"Module {mod} must exist"
        assert (mod_dir / "main.tf").exists(), f"{mod}/main.tf missing"
        assert (mod_dir / "variables.tf").exists(), f"{mod}/variables.tf missing"
        assert (mod_dir / "outputs.tf").exists(), f"{mod}/outputs.tf missing"

    for env in ["dev", "prod"]:
        env_dir = ENVIRONMENTS_DIR / env
        assert env_dir.exists(), f"Environment {env} must exist"
        assert (env_dir / "main.tf").exists(), f"{env}/main.tf missing"
        assert (env_dir / "variables.tf").exists(), f"{env}/variables.tf missing"
        assert (env_dir / "outputs.tf").exists(), f"{env}/outputs.tf missing"
        assert (env_dir / "terraform.tfvars").exists(), f"{env}/terraform.tfvars missing"


def test_dockerfile_and_ci_cd_configuration():
    """Verifies Dockerfile and Cloud Build CI/CD files."""
    dockerfile = REPO_ROOT / "Dockerfile"
    dockerignore = REPO_ROOT / ".dockerignore"
    cloudbuild = REPO_ROOT / "cloudbuild.yaml"

    assert dockerfile.exists(), "Dockerfile must exist at repository root"
    content = dockerfile.read_text()
    assert "FROM python:3.12-slim" in content
    assert "EXPOSE 8080" in content
    assert "HEALTHCHECK" in content
    assert "appuser" in content  # Non-root user security practice

    assert dockerignore.exists(), ".dockerignore must exist"
    ignore_content = dockerignore.read_text()
    assert "venv" in ignore_content
    assert "*.tfstate" in ignore_content

    assert cloudbuild.exists(), "cloudbuild.yaml must exist"
    build_content = cloudbuild.read_text()
    assert "build-image" in build_content
    assert "push-image" in build_content
    assert "terraform-validate" in build_content


@pytest.mark.skipif(shutil.which("terraform") is None, reason="terraform CLI not installed")
def test_terraform_fmt_check():
    """Verifies that all Terraform files adhere to standard formatting."""
    res = subprocess.run(
        ["terraform", "fmt", "-check", "-recursive", str(TERRAFORM_DIR)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"terraform fmt check failed:\n{res.stdout}\n{res.stderr}"


@pytest.mark.skipif(shutil.which("terraform") is None, reason="terraform CLI not installed")
def test_terraform_root_module_validation():
    """Validates the root Terraform module."""
    # Run terraform init
    init_res = subprocess.run(
        ["terraform", "init", "-backend=false"],
        cwd=str(TERRAFORM_DIR),
        capture_output=True,
        text=True,
    )
    assert init_res.returncode == 0, f"Root terraform init failed:\n{init_res.stderr}"

    # Run terraform validate
    val_res = subprocess.run(
        ["terraform", "validate"],
        cwd=str(TERRAFORM_DIR),
        capture_output=True,
        text=True,
    )
    assert val_res.returncode == 0, f"Root terraform validate failed:\n{val_res.stderr}"


@pytest.mark.skipif(shutil.which("terraform") is None, reason="terraform CLI not installed")
def test_terraform_environments_validation():
    """Validates dev and prod environment Terraform modules."""
    for env in ["dev", "prod"]:
        env_dir = ENVIRONMENTS_DIR / env
        init_res = subprocess.run(
            ["terraform", "init", "-backend=false"],
            cwd=str(env_dir),
            capture_output=True,
            text=True,
        )
        assert init_res.returncode == 0, f"{env} terraform init failed:\n{init_res.stderr}"

        val_res = subprocess.run(
            ["terraform", "validate"],
            cwd=str(env_dir),
            capture_output=True,
            text=True,
        )
        assert val_res.returncode == 0, f"{env} terraform validate failed:\n{val_res.stderr}"


def test_iam_least_privilege_and_security():
    """Verifies that IAM module and security configurations follow least privilege."""
    iam_main = (MODULES_DIR / "iam" / "main.tf").read_text()
    assert "roles/dlp.user" in iam_main
    assert "roles/secretmanager.secretAccessor" in iam_main
    assert "roles/aiplatform.user" in iam_main
    assert "roles/cloudtrace.agent" in iam_main
    assert "roles/logging.logWriter" in iam_main
    assert "roles/monitoring.metricWriter" in iam_main
    assert "roles/storage.objectUser" in iam_main
    # Ensure excessive admin roles are NOT assigned to runtime SA
    assert "roles/owner" not in iam_main
    assert "roles/editor" not in iam_main

    storage_main = (MODULES_DIR / "storage" / "main.tf").read_text()
    assert 'public_access_prevention    = "enforced"' in storage_main
    assert "uniform_bucket_level_access = true" in storage_main
