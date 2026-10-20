"""Automated Workspace & Log Organizer - Stage 1 & 2: Categorization & Dry Run."""

from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# =========================================================
# 1. CONFIGURATION (Human-friendly rules)
# =========================================================
FILE_CATEGORIES: dict[str, list[str]] = {
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Code": [".py", ".js", ".html", ".css", "json"],
}

# The name of our fallback folder for unmapped file extensions
DEFAULT_CATEGORY = "Miscellaneous"


# =========================================================
# 2. HELPER FUNCTIONS
# =========================================================


def build_extension_map(categories: dict[str, list[str]]) -> dict[str, str]:
    """Inverts category rules into direct extension -> category lookup table.
    
    Example input: {'Images': ['.png', '.jpg']}
    Example output: {'.png': 'Images', '.jpg': 'Images'}
    """
    mapping: dict[str, str] = {}
    for category, extensions in categories.items():
        for ext in extensions:
            # Normalize to lowercase so .PNG and .png are treated the same
            mapping[ext.lower()] = category
    return mapping

def plan_file_moves(target_path: Path, extension_map: dict[str, str]) -> list[tuple[Path, str]]:
    """Scans target directory and determines category for each top-level file.
    Returns a list of tuples: (file_path, category_name)
    """
    planned_moves: list[tuple[Path, str]] = []

    # `iterdir()` yields all items directly inside target_dir (non recursive)
    for item in target_path.iterdir():
        
        # Rule 1: Ignore directories so we don't move existing folders
        if not item.is_file():
            continue
        
        # Rule 2: Ignore our script or log files if they are in the same directory
        if item.name.startswith("organizer"):
            continue

        # Extract extension
        ext = item.suffix.lower()

        # Look up category in 0(1) time; fallback to DEFAULT_CATEGORY if not found
        category = extension_map.get(ext, DEFAULT_CATEGORY)

        planned_moves.append((item, category))
    
    return planned_moves

# =========================================================
# 3. TEST ENVIRONMENT SETUP
# =========================================================

def setup_sample_workspace(workspace_dir: Path) -> None:
    """Creates a temporary sandbox folder with mock files for safe testing."""
    workspace_dir.mkdir(exist_ok=True)

    sample_files = [
        "quarterly_report.pdf",
        "team_photo.jpg",
        "project_notes.txt",
        "raw_data.csv", # Not in any category, should go to Miscellaneous
        "backup.zip",
        "script.py",
        "unknown_file.xyz",  # This will go to Miscellaneous
    ]

    for filename in sample_files:
        mock_file = workspace_dir / filename
        # `touch()` creates an empty file if it doesn't exist
        mock_file.touch(exist_ok=True)

# =========================================================
# 4. MAIN FUNCTION
# =========================================================

def main() -> None:
    # Set up test sandbox folder inside the current working directory
    workspace = Path.cwd() / "test_workspace"

    console.print(f"[bold cyan]Setting up test workspace at:[/bold cyan] [magenta]{workspace}[/magenta]\n")
    setup_sample_workspace(workspace)

    # Invert the config for fast lookup
    ext_map = build_extension_map(FILE_CATEGORIES)

    # Scan and plan moves (dry run mode)
    planned_moves = plan_file_moves(workspace, ext_map)

    # Display the plan in a Rich table
    table = Table(
        title="Planned File Moves (Dry Run)", 
        show_header=True, 
        header_style="bold yellow",
    )
    table.add_column("Source File", style="dim")
    table.add_column("Extension")
    table.add_column("Target Folder", style="bold green")

    for file_path, category in planned_moves:
        table.add_row(
            file_path.name,
            file_path.suffix or "[none]",
            f"{category}/",
        )

    console.print(table)
    console.print(f"\n[bold white]Total items planned for organization:[/bold white] {len(planned_moves)}"
    )
    console.print("[yellow]Notice: No files have been moved yet. This is a simulation.[/yellow]"
    )

if __name__ == "__main__":
    main()
    
