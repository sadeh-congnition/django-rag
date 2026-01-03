from pathlib import Path
import shutil

from django.db import transaction
import djclick as click
from loguru import logger

from synthetic_data_generator.models import PythonFile, Project



@click.command()
@click.argument('path')
@click.option('--delete', is_flag=True, help='Delete the directory after loading Python modules into database')
def command(path, delete: bool=False):
    """Recursively traverse the given path and store Python files in the database."""
    logger.info(f"Starting traversal of path: {path}")
    
    python_files_found = 0
    python_files_stored = 0
    
    try:
        with transaction.atomic():
            # Create or get the project
            project_name = Path(path).name
            project, created = Project.objects.get_or_create(
                name=project_name,
                defaults={'root_path': str(Path(path).absolute())}
            )
            
            if created:
                logger.success(f"Created new project: {project_name}")
            
            for python_file_path in find_python_files(Path(path)):
                python_files_found += 1
                
                # Convert to relative path for storage
                relative_path = str(python_file_path.relative_to(Path(path)))
                
                # Read file content
                try:
                    with open(python_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logger.warning(f"Skipping binary file: {python_file_path}")
                    continue
                except Exception as e:
                    logger.error(f"Error reading file {python_file_path}: {e}")
                    continue
                
                # Store in database
                python_file, created = PythonFile.objects.update_or_create(
                    module_path=relative_path,
                    defaults={'content': content, 'project': project}
                )
                
                if created:
                    python_files_stored += 1
                    logger.success(f"Stored: {relative_path}")
                else:
                    logger.info(f"Updated: {relative_path}")
    
    except Exception as e:
        logger.error(f"Error during traversal: {e}")
        return
    
    logger.success(
        f"Completed! Found {python_files_found} Python files, "
        f"stored {python_files_stored} new files."
    )
    
    if delete:
        try:
            project_path = Path(path)
            if project_path.exists() and project_path.is_dir():
                shutil.rmtree(project_path)
                logger.success(f"Deleted directory: {project_path}")
            else:
                logger.warning(f"Directory not found or not a directory: {project_path}")
        except Exception as e:
            logger.error(f"Error deleting directory {path}: {e}")

def find_python_files(path):
    """Generator that yields all Python files in the given path recursively, skipping virtual env directories."""
    # Common virtual environment directory names
    venv_dirs = {'venv', '.venv', 'env', '.env', 'virtualenv', '.virtualenv', 'envs', '.envs'}
    
    for item in path.rglob('*.py'):
        if item.is_file():
            # Check if any parent directory is a virtual environment directory
            skip_file = False
            for parent in item.parents:
                if parent.name in venv_dirs:
                    skip_file = True
                    break
            
            if not skip_file:
                yield item
