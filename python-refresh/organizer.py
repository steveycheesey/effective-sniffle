"""Automated Workspace & Log Organizer - Full Implementation:
Categorization, Collision Handling, File Movement, and JSON/CSV Logging.
"""

from collections.abc import Sequence
import csv
from datetime import datetime
import json
from pathlib import Path
import shutil
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

def resolve_collision(destination_dir: Path, filename: str) -> Path:
    """Returns a unique file path in the destination directory.
    If filename already exists, appends a numeric suffix before the extension."""
    candidate_path = destination_dir / filename
    if not candidate_path.exists():
        return candidate_path

    # Extraxt base name and extension: "report.pdf" -> stem="report", suffix=".pdf"
    file_path = Path(filename)
    stem = file_path.stem
    suffix = file_path.suffix

    counter = 1
    while candidate_path.exists():
        candidate_path = destination_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    return candidate_path

# =========================================================
# 3. EXECUTION LOGIC & LOGGING
# =========================================================

def execute_moves(
    workspace_dir: Path, planned_moves: list[tuple[Path, str]]) -> list[dict[str, str | int]]:
    """Executes the planned file moves and logs the results."""
    audit_records: list[dict[str, str | int]] = []

    for source_file, category in planned_moves:
        # Create destination folder if it doesn't exist
        dest_dir = workspace_dir / category
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Get file size before moving
        file_size = source_file.stat().st_size

        # Find safe destination path to avoid overwriting
        final_dest_path = resolve_collision(dest_dir, source_file.name)

        # Move the file
        shutil.move(str(source_file), str(final_dest_path))

        # Log the move
        audit_records.append(
            {
                "original_filename": source_file.name,
                "category": category,
                "file_path": str(final_dest_path.name),
                "size_bytes": file_size,
                "organized_at": datetime.now().isoformat(),
            }
        )

    return audit_records

def export_audit_logs(
    workspace_dir: Path, audit_records: Sequence[dict[str, str | int]]) -> tuple[Path, Path]:
    """Exports the audit records to both JSON and CSV files in the workspace directory."""
    json_path = workspace_dir / "organization_audit.json"
    csv_path = workspace_dir / "organization_audit.csv"

    # 1. Export JSON log (readable with 2-space indentation)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_records, f, indent=2)

        # 2. Export CSV log
    if audit_records:
        fieldnames = audit_records[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(audit_records)

    return json_path, csv_path

# ========================================================
# 4. WORKSPACE GENERATOR AND MAIN
# ========================================================

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
        if not mock_file.exists():
            mock_file.touch()

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

    if not planned_moves:
        console.print("[bold red]Workspace is already organized. No files to move.[/bold red]")
        return

    # FOR TESTING Display the plan in a Rich table
    """table = Table(
            title="Planned File Moves (Dry Run)", 
            show_header=True, 
            header_style="bold yellow",
        )
        table.add_column("Source File", style="dim")
        table.add_column("Extension")
        table.add_column("Target Folder", style="bold green")
    """

    # Execute moves on disk
    console.print(f"[bold cyan]Executing file organization for {len(planned_moves)} files...[/bold cyan]")
    audit_records = execute_moves(workspace, planned_moves)

    # Export audit logs
    json_log, csv_log = export_audit_logs(workspace, audit_records)

    # Display completion summary
    summary_table = Table(title="Organization Summary", header_style="bold magenta")
    summary_table.add_column("Source File", style="dim")
    summary_table.add_column("Category", style="green")
    summary_table.add_column("Final Output Name")

    for record in audit_records:
        summary_table.add_row(
            str(record["original_filename"]),
            str(record["category"]),
            str(record["file_path"]),
        )

    """ TESTING: Display the planned moves in a Rich table (dry run)
    for file_path, category in planned_moves:
        summary_table.add_row(
            file_path.name,
            file_path.suffix or "[none]",
            f"{category}/",
        )
    """

    console.print(summary_table)
    console.print(f"\n[bold white]JSON Audit Log:[/bold white] {json_log.resolve()}")
    console.print(f"[bold white]CSV Audit Log:[/bold white] {csv_log.resolve()}")


if __name__ == "__main__":
    main()
    
