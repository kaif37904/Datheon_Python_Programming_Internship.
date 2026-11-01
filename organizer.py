"""Automated File Organizer & Cleanup Utility

Run with:
    python organizer.py                     (asks which folder, default: Downloads)
    python organizer.py "C:\\path\\to\\folder"
    python organizer.py "C:\\path\\to\\folder" --dry-run   (only shows what would happen)
    python organizer.py "C:\\path\\to\\folder" --yes       (skip the confirmation)

What it does:
- Looks at every file directly inside the chosen folder.
- Creates category subfolders (Documents, Images, Videos, Archives, Code, ...).
- Safely moves each file into the right folder based on its extension.
- If a file with the same name already exists, the moved file is renamed
  (report.pdf -> report (1).pdf) so nothing is ever overwritten.
- Permission errors and locked files are logged and skipped.
- Writes a log to 'organizer.log' (next to this script) and prints a summary.
"""

import argparse
import logging
import os
import shutil
from collections import Counter
from pathlib import Path

CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx",
                  ".csv", ".ppt", ".pptx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Code": {".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".cs", ".php",
             ".json", ".xml", ".sql", ".ipynb", ".sh", ".bat"},
}
OTHER_FOLDER = "Others"

# Reverse lookup: extension -> category
EXTENSION_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}

LOG_FILE = Path(__file__).resolve().parent / "organizer.log"


def setup_logging():
    logger = logging.getLogger("organizer")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(fmt)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)-7s | %(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(console)
    return logger


def category_for(path):
    return EXTENSION_MAP.get(path.suffix.lower(), OTHER_FOLDER)


def unique_destination(dest_dir, name):
    """Return a path in dest_dir that does not exist yet: name, name (1), name (2)..."""
    candidate = dest_dir / name
    if not candidate.exists():
        return candidate
    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def collect_files(folder, skip_names):
    """List the files directly inside folder (no sub-folders, hidden files or symlinks)."""
    files = []
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.name.startswith(".") or entry.name in skip_names:
                continue
            if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                continue
            files.append(Path(entry.path))
    return sorted(files, key=lambda p: p.name.lower())


def organize(folder, dry_run, logger):
    folder = folder.resolve()
    skip = {Path(__file__).name, LOG_FILE.name}
    files = collect_files(folder, skip)

    moved = Counter()
    renamed = skipped = errors = 0

    if not files:
        logger.info("No files to organize in %s", folder)
        return moved, renamed, skipped, errors

    for src in files:
        category = category_for(src)
        dest_dir = folder / category
        try:
            if not dry_run:
                dest_dir.mkdir(exist_ok=True)
            dest = unique_destination(dest_dir, src.name)
            was_renamed = dest.name != src.name
            if dry_run:
                logger.info("[DRY RUN] %s -> %s/%s", src.name, category, dest.name)
            else:
                shutil.move(str(src), str(dest))
                note = " (renamed, name already existed)" if was_renamed else ""
                logger.info("Moved %s -> %s/%s%s", src.name, category, dest.name, note)
            moved[category] += 1
            renamed += was_renamed
        except PermissionError:
            logger.warning("Permission denied, skipped: %s", src.name)
            skipped += 1
        except FileExistsError:
            logger.warning("Destination already exists, skipped: %s", src.name)
            skipped += 1
        except OSError as exc:  # locked / in-use files, long paths, disk errors
            logger.error("Could not move %s: %s", src.name, exc)
            errors += 1
    return moved, renamed, skipped, errors


def print_summary(folder, moved, renamed, skipped, errors, dry_run):
    total = sum(moved.values())
    line = "=" * 44
    print("\n" + line)
    print(("DRY RUN SUMMARY" if dry_run else "EXECUTION SUMMARY").center(44))
    print(line)
    print(f"Folder          : {folder}")
    print(f"Files {'to move' if dry_run else 'moved':<9} : {total}")
    for category, count in sorted(moved.items()):
        print(f"   {category:<12} : {count}")
    print(f"Renamed (clash) : {renamed}")
    print(f"Skipped         : {skipped}")
    print(f"Errors          : {errors}")
    print(f"Log file        : {LOG_FILE}")
    print(line)


def parse_args():
    parser = argparse.ArgumentParser(description="Organize files in a folder by type.")
    parser.add_argument("folder", nargs="?", help="Folder to organize (default: ask)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without moving anything")
    parser.add_argument("--yes", "-y", action="store_true", help="Do not ask for confirmation")
    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging()

    if args.folder:
        folder = Path(args.folder).expanduser()
    else:
        default = Path.home() / "Downloads"
        answer = input(f"Folder to organize [{default}]: ").strip().strip('"')
        folder = Path(answer).expanduser() if answer else default

    if not folder.is_dir():
        logger.error("Folder not found: %s", folder)
        return

    if not args.dry_run and not args.yes:
        confirm = input(f"Move files in '{folder}' into category folders? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled. Nothing was changed.")
            return

    logger.info("Starting%s on %s", " (dry run)" if args.dry_run else "", folder)
    try:
        result = organize(folder, args.dry_run, logger)
    except PermissionError:
        logger.error("Permission denied while reading folder: %s", folder)
        return
    print_summary(folder.resolve(), *result, args.dry_run)


if __name__ == "__main__":
    main()
