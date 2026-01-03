import os
import shutil
import subprocess
from pathlib import Path

import djclick as click
from loguru import logger

from code_fetching.constants import DEFAULT_OUTPUT_DIR


@click.command()
@click.option("--repo", required=True, help="GitHub repository in format owner/repo")
@click.option(
    "--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to save fetched code"
)
@click.option(
    "--file-types", default=".py", help="Comma-separated file extensions to fetch"
)
def command(repo, output_dir, file_types):
    """Fetch code files from a GitHub repository using git clone."""

    logger.info(f"Cloning repository {repo}")

    # Construct GitHub URL
    github_url = f"https://github.com/{repo}.git"

    # Create output directory
    output_path = Path(output_dir) / repo.replace("/", "_")
    output_path.mkdir(parents=True, exist_ok=True)

    # Clone repository
    try:
        # Remove existing directory if it exists
        repo_dir = output_path / repo.split("/")[-1]
        if repo_dir.exists():
            shutil.rmtree(repo_dir)

        # Clone the specific branch
        clone_cmd = ["git", "clone", github_url, str(repo_dir)]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, check=True)

        logger.info(f"Successfully cloned repository to {repo_dir}")

        # Parse file types
        allowed_extensions = [ext.strip() for ext in file_types.split(",")]

        fetched_count = 0

        # Walk through the cloned repository and copy matching files
        for root, dirs, files in os.walk(repo_dir):
            # Skip .git directory
            if ".git" in dirs:
                dirs.remove(".git")

            for file in files:
                file_path = Path(root) / file
                file_extension = file_path.suffix

                # Check if file extension is in allowed types
                if file_extension in allowed_extensions:
                    # Calculate relative path from repo root
                    rel_path = file_path.relative_to(repo_dir)

                    # Create destination path maintaining directory structure
                    dest_path = output_path / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(file_path, dest_path)
                    fetched_count += 1
                    logger.info(f"Copied: {rel_path}")

        # Remove the cloned repository after copying files
        shutil.rmtree(repo_dir)

        logger.info(f"Successfully fetched {fetched_count} files to {output_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning repository: {e}")
        logger.error(f"Git output: {e.stderr}")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error: {e}")
        raise click.Abort()
