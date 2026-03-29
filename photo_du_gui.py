#!/usr/bin/env python3
import hashlib
import os
import shutil
from pathlib import Path
from tkinter import Tk, Button, Label, Entry, Frame, Listbox, Scrollbar, Toplevel, Checkbutton, StringVar, messagebox
from tkinter.ttk import Combobox, Progressbar
from PIL import Image

IMAGE_EXTS = {'.jpg', '.HEIC', '.PNG', '.JPG', '.TIF', '.TIFF', '.JPEG', '.jpeg', '.png', '.heic', '.tif', '.tiff', '.webp', '.bmp', '.gif'}


def sha256(path: Path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def ahash(path: Path, size=8):
    with Image.open(path) as img:
        img = img.convert('L').resize((size, size), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = ''.join('1' if p >= avg else '0' for p in pixels)
    return int(bits, 2)


def hamming(a, b):
    return (a ^ b).bit_count()


def collect(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in IMAGE_EXTS:
                yield p


def exact_duplicates(root: Path):
    size_groups = {}
    for p in collect(root):
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
                hash_groups.setdefault(sha256(p), []).append(p)
            except OSError:
                pass
        for group in hash_groups.values():
            if len(group) > 1:
                groups.append(group)
    return groups


def similar_photos(root: Path, threshold=5):
    items = []
    for p in collect(root):
        try:
            items.append((p, ahash(p)))
        except Exception:
            pass
    groups = []
    used = set()
    for i, (p1, h1) in enumerate(items):
        if i in used:
            continue
        group = [p1]
        used.add(i)
        for j in range(i + 1, len(items)):
            if j in used:
                continue
            p2, h2 = items[j]
            if hamming(h1, h2) <= threshold:
                group.append(p2)
                used.add(j)
        if len(group) > 1:
            groups.append(group)
    return groups


def keep_one(group, strategy):
    if strategy == 'oldest':
        return min(group, key=lambda p: p.stat().st_mtime)
    if strategy == 'newest':
        return max(group, key=lambda p: p.stat().st_mtime)
    return min(group, key=lambda p: len(str(p)))


class PhotoDuplicateGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title('Photo Duplicate Tool')
        self.root.geometry('800x600')

        frame = Frame(self.root)
        frame.pack(padx=10, pady=10, fill='both', expand=True)

        Label(frame, text='Folder:').pack(anchor='w')
        self.folder_entry = Entry(frame, width=70)
        self.folder_entry.pack(anchor='w', pady=(0,5), fill='x')
        Button(frame, text='Browse...', command=self.browse_folder).pack(anchor='w')

        Label(frame, text='Mode:').pack(anchor='w', pady=(10,0))
        self.mode_var = StringVar(value='exact')
        self.mode_combo = Combobox(frame, textvariable=self.mode_var, values=['exact', 'similar'], state='readonly')
        self.mode_combo.pack(anchor='w')

        self.threshold_frame = Frame(frame)
        self.threshold_frame.pack(anchor='w', pady=(0,10), fill='x')
        Label(self.threshold_frame, text='Threshold (similar mode):').pack(side='left')
        self.threshold_var = StringVar(value='5')
        self.threshold_entry = Entry(self.threshold_frame, textvariable=self.threshold_var, width=10)
        self.threshold_entry.pack(side='left', padx=(5,0))

        Button(frame, text='Find Duplicates', command=self.find_duplicates).pack(pady=10)

        self.progress = Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0,10))

        Label(frame, text='Results:').pack(anchor='w')
        list_frame = Frame(frame)
        list_frame.pack(fill='both', expand=True)

        self.listbox = Listbox(list_frame)
        scrollbar = Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        Button(frame, text='Move to duplicates/', command=self.move_duplicates).pack(pady=5)
        Button(frame, text='Delete duplicates', command=self.delete_duplicates).pack(pady=5)
        Button(frame, text='Quit', command=self.root.quit).pack(pady=5)

    def browse_folder(self):
        from tkinter.filedialog import askdirectory
        folder = askdirectory()
        if folder:
            self.folder_entry.delete(0, 'end')
            self.folder_entry.insert(0, folder)

    def find_duplicates(self):
        folder = Path(self.folder_entry.get())
        if not folder.exists():
            messagebox.showerror('Error', 'Please select a valid folder')
            return

        self.progress.start()
        self.listbox.delete(0, 'end')
        self.root.update()

        try:
            mode = self.mode_var.get()
            threshold = int(self.threshold_var.get())
            if mode == 'exact':
                groups = exact_duplicates(folder)
            else:
                groups = similar_photos(folder, threshold)

            for i, group in enumerate(groups, 1):
                self.listbox.insert('end', f'Group {i}: {len(group)} photos')
                for p in group:
                    self.listbox.insert('end', f'  {p}')
                self.listbox.insert('end', '')
        except Exception as e:
            messagebox.showerror('Error', str(e))
        finally:
            self.progress.stop()

    def move_duplicates(self):
        if not messagebox.askyesno('Confirm', 'Move duplicates to duplicates/ folder?'):
            return
        self._manage_duplicates('move')

    def delete_duplicates(self):
        if not messagebox.askyesno('Confirm', 'Delete duplicates (keeping newest)?'):
            return
        self._manage_duplicates('delete')

    def _manage_duplicates(self, action):
        folder = Path(self.folder_entry.get())
        mode = self.mode_var.get()
        threshold = int(self.threshold_var.get())
        if mode == 'exact':
            groups = exact_duplicates(folder)
        else:
            groups = similar_photos(folder, threshold)

        dup_root = folder.parent / 'duplicates'
        dup_root.mkdir(exist_ok=True)

        for group in groups:
            keeper = keep_one(group, 'newest')
            for p in group:
                if p == keeper:
                    continue
                if action == 'delete':
                    p.unlink(missing_ok=True)
                else:
                    target = dup_root / p.name
                    if target.exists():
                        stem, suffix = target.stem, target.suffix
                        n = 1
                        while (dup_root / f'{stem}_{n}{suffix}').exists():
                            n += 1
                        target = dup_root / f'{stem}_{n}{suffix}'
                    shutil.move(str(p), str(target))
        messagebox.showinfo('Done', f'{action.title()}ed duplicates')
        self.find_duplicates()


def main():
    app = PhotoDuplicateGUI()
    app.root.mainloop()


if __name__ == '__main__':
    main()
