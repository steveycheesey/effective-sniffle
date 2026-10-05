from collections import Counter
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def scan_directory(target_path: Path) -> tuple[Counter, int]:
    """Scan the target directory and return a Counter of file extensions and the total byte size."""
    extension_counter: Counter[str] = Counter()
    total_size = 0

    for file_path in target_path.rglob('*'):
        if file_path.is_file():
            extension = file_path.suffix.lower() or 'no_extension'
            extension_counter[extension] += 1
            total_size += file_path.stat().st_size

    return extension_counter, total_size

def format_bytes(size: int) -> str:
    """Format bytes as a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def main() -> None:
    # Set the target path to the current working directory, or specify a different path if needed
    target = Path.cwd()

    console.print(f"[bold cyan]Scanning directory:[/bold cyan] {target.resolve()}\n")
    counts, total_bytes = scan_directory(target)

    #Build formatted table using Rich
    table = Table(title= "Directory Summary", show_header=True, header_style="bold magenta")
    table.add_column("File Extension", style="dim")
    table.add_column("Count", justify="right")

    for ext, count in counts.most_common(10):
        table.add_row(ext, str(count))

    console.print(table)
    console.print(f"\n[green]Total Size:[/green] {format_bytes(total_bytes)}")
    console.print(f"[yellow]Last Scanned:[/yellow] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if __name__ == "__main__":
        main()