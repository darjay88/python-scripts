#!/usr/bin/env python3
import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff', '.JPG', '.HEIC', '.PNG', '.webp', '.bmp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.3gp'}


def exif_date(path: Path):
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            tag_map = {TAGS.get(k, k): v for k, v in exif.items()}
            for key in ('DateTimeOriginal', 'DateTimeDigitized', 'DateTime'):
                if key in tag_map:
                    raw = str(tag_map[key]).strip().replace(':', '-', 2)
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S%z'):
                        try:
                            return datetime.strptime(raw, fmt)
                        except ValueError:
                            pass
    except Exception:
        return None
    return None


def file_date(path: Path):
    dt = exif_date(path)
    if dt:
        return dt
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts)


def unique_dest(dest: Path):
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    parent = dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def organize(src: Path, dst: Path, dry_run: bool, move_files: bool):
    for root, _, files in os.walk(src):
        root_path = Path(root)
        for name in files:
            path = root_path / name
            ext = path.suffix.lower()
            if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
                continue
            dt = file_date(path)
            year = str(dt.year)
            month = f"{dt.month:02d}"
            day = f"{dt.day:02d}"
            target_dir = dst / year / month / day
            target = unique_dest(target_dir / path.name)
            if dry_run:
                print(f"{path} -> {target}")
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            if move_files:
                shutil.move(str(path), str(target))
            else:
                shutil.copy2(str(path), str(target))
            print(f"{path} -> {target}")


def main():
    parser = argparse.ArgumentParser(description='Organize photos by year/date.')
    parser.add_argument('source', help='Source folder containing photos')
    parser.add_argument('destination', help='Destination folder for organized photos')
    parser.add_argument('--move', action='store_true', help='Move files instead of copying')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    args = parser.parse_args()

    src = Path(args.source).expanduser().resolve()
    dst = Path(args.destination).expanduser().resolve()

    if not src.exists() or not src.is_dir():
        raise SystemExit(f'Source folder not found: {src}')

    organize(src, dst, args.dry_run, args.move)


if __name__ == '__main__':
    main()
