#!/usr/bin/env python3
import argparse
import hashlib
import os
import shutil
from pathlib import Path

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.tif', '.tiff', '.webp', '.bmp', '.gif'}


def file_hash(path: Path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in IMAGE_EXTS:
                yield p


def find_duplicate_groups(root: Path):
    size_groups = {}
    for p in collect_files(root):
        try:
            size_groups.setdefault(p.stat().st_size, []).append(p)
        except OSError:
            pass

    groups = []
    for paths in size_groups.values():
        if len(paths) < 2:
            continue
        hash_groups = {}
        for p in paths:
            try:
                hash_groups.setdefault(file_hash(p), []).append(p)
            except OSError:
                pass
        for group in hash_groups.values():
            if len(group) > 1:
                groups.append(group)
    return groups


def keep_one(group, strategy):
    if strategy == 'oldest':
        return min(group, key=lambda p: p.stat().st_mtime)
    if strategy == 'newest':
        return max(group, key=lambda p: p.stat().st_mtime)
    return min(group, key=lambda p: len(str(p)))


def main():
    parser = argparse.ArgumentParser(description='Find and optionally move or delete duplicate photos.')
    parser.add_argument('folder', help='Folder to scan')
    parser.add_argument('--action', choices=['report', 'move', 'delete'], default='report')
    parser.add_argument('--duplicates-dir', default='duplicates', help='Folder to move duplicates into')
    parser.add_argument('--keep', choices=['oldest', 'newest', 'path'], default='path', help='Which copy to keep in each group')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    args = parser.parse_args()

    root = Path(args.folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f'Folder not found: {root}')

    groups = find_duplicate_groups(root)
    print(f'Found {len(groups)} duplicate groups')

    if args.action == 'report':
        for i, group in enumerate(groups, 1):
            print(f'Group {i}:')
            for p in group:
                print(p)
        return

    dup_root = Path(args.duplicates_dir).expanduser().resolve()
    if args.action == 'move' and not args.dry_run:
        dup_root.mkdir(parents=True, exist_ok=True)

    for i, group in enumerate(groups, 1):
        keeper = keep_one(group, args.keep)
        for p in group:
            if p == keeper:
                continue
            if args.action == 'delete':
                if args.dry_run:
                    print(f'[DRY RUN] delete {p}')
                else:
                    print(f'delete {p}')
                    p.unlink(missing_ok=True)
            elif args.action == 'move':
                target = dup_root / p.name
                if target.exists():
                    stem, suffix = target.stem, target.suffix
                    n = 1
                    while (dup_root / f'{stem}_{n}{suffix}').exists():
                        n += 1
                    target = dup_root / f'{stem}_{n}{suffix}'
                if args.dry_run:
                    print(f'[DRY RUN] move {p} -> {target}')
                else:
                    print(f'move {p} -> {target}')
                    shutil.move(str(p), str(target))


if __name__ == '__main__':
    main()
