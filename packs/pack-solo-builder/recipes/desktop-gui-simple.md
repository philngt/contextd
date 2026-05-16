# Recipe: Desktop GUI Simple

Tool có giao diện form/button để dùng cá nhân — không terminal, không browser. Chạy như app native.

## When to use

Task signals:
- "Tôi không muốn mở terminal"
- "Cần form click chuột, vài button"
- "Tool dùng cá nhân, không share team"
- "Drag-drop file rồi click Run"

Không phải:
- Cần share team → recipe `team-shared-web-tool` (web app dễ share hơn nhiều)
- Logic phức tạp với nhiều screen → cân nhắc Streamlit vẫn được

## Tech Stack

| Component | Chọn | Note |
|-----------|------|------|
| Language | Python 3.11+ | |
| GUI library | `tkinter` (built-in) hoặc `PySimpleGUI` | tkinter đủ; PySimpleGUI wrap tkinter cho code ngắn hơn |
| Alternative GUI | `PyWebView` | Wrap web app thành desktop window — dùng nếu UI cần đẹp |
| Packaging | `PyInstaller` | Build `.exe` / binary để click chạy không cần Python |

### Linux/macOS native

```bash
python3 -m venv .venv
source .venv/bin/activate
# tkinter built-in (Linux có thể cần): sudo apt install python3-tk
pip install PySimpleGUI    # optional, cho code ngắn hơn
python tool.py
```

### Windows native

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install PySimpleGUI    # optional
python tool.py
```

### Windows + Docker — KHÔNG dùng được dễ

GUI app cần X server / display server. Trên Windows + Docker phải chạy VcXsrv (X server) — phức tạp, không recommend.

⚠️ **Nếu cần share team**: chuyển sang recipe `team-shared-web-tool`. GUI native không hợp share.

### Build standalone .exe / binary (optional, dùng PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed tool.py
# Output: dist/tool.exe (Windows) hoặc dist/tool (Linux/macOS)
```

User chỉ cần double-click file `.exe`, không cần cài Python.

## Trade-offs

**Vì sao tkinter / PySimpleGUI**:
- Built-in Python (tkinter) — không cần install gì thêm
- Code ngắn cho form đơn giản
- Cross-platform (Linux/macOS/Windows) cùng 1 file Python

**Vì sao KHÔNG**:
- **PyQt / PySide**: tốt hơn UI nhưng license phức tạp, học mất tuần.
- **Electron**: cần Node + JS, output app 100MB+.
- **Streamlit**: web app, mở browser — nếu user OK thì Streamlit dễ hơn nhiều, dùng cho cả share team.
- **GTK**: setup khó trên Windows.

## Skeleton — PySimpleGUI

```python
# tool.py — File converter GUI
import PySimpleGUI as sg
from pathlib import Path

sg.theme("LightBlue3")

layout = [
    [sg.Text("File input:"), sg.Input(key="-IN-"), sg.FileBrowse(file_types=(("Excel", "*.xlsx"),))],
    [sg.Text("Output folder:"), sg.Input(default_text="output", key="-OUT-"), sg.FolderBrowse()],
    [sg.Text("Filter status:"), sg.Combo(["Open", "Closed", "All"], default_value="Open", key="-STATUS-")],
    [sg.Button("Run", size=(10, 1)), sg.Button("Exit", size=(10, 1))],
    [sg.Multiline(size=(60, 10), key="-LOG-", autoscroll=True)],
]

window = sg.Window("My File Tool", layout)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Exit"):
        break
    if event == "Run":
        in_path = Path(values["-IN-"])
        out_dir = Path(values["-OUT-"])
        if not in_path.exists():
            window["-LOG-"].print(f"[ERROR] File không tồn tại: {in_path}")
            continue
        out_dir.mkdir(exist_ok=True)
        # logic xử lý ở đây
        try:
            # vd: import pandas; df = pd.read_excel(in_path); ...
            window["-LOG-"].print(f"[OK] Processed {in_path.name} -> {out_dir}")
        except Exception as e:
            window["-LOG-"].print(f"[ERROR] {e}")

window.close()
```

## Skeleton — Tkinter (built-in, không cần PySimpleGUI)

```python
# tool.py — Simple form
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def run():
    path = entry_file.get()
    if not path:
        messagebox.showerror("Error", "Chọn file trước")
        return
    log.insert(tk.END, f"Processing {path}...\n")
    # logic ở đây
    log.insert(tk.END, f"Done!\n")

def browse():
    path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
    entry_file.delete(0, tk.END)
    entry_file.insert(0, path)

root = tk.Tk()
root.title("My Tool")
root.geometry("500x400")

tk.Label(root, text="File input:").pack(anchor="w", padx=10, pady=5)
frame = tk.Frame(root)
frame.pack(fill="x", padx=10)
entry_file = tk.Entry(frame)
entry_file.pack(side="left", fill="x", expand=True)
tk.Button(frame, text="Browse", command=browse).pack(side="right", padx=5)

tk.Button(root, text="Run", command=run, width=10).pack(pady=10)
log = scrolledtext.ScrolledText(root, height=15)
log.pack(fill="both", expand=True, padx=10, pady=5)

root.mainloop()
```

## Decision tree

✅ **Match recipe này KHI**:
- Dùng cá nhân (1 người, 1 máy)
- User refuse mở terminal/browser
- Form đơn giản (≤ 5 button, ≤ 10 input fields)
- Output text/file đủ — không cần chart phức tạp

❌ **KHÔNG match KHI**:
- Cần share team → `team-shared-web-tool`
- UI cần đẹp / phức tạp → cân nhắc PyWebView hoặc chuyển web app
- Cần cài trên 10+ máy → Streamlit + Docker dễ deploy hơn
- User OK với browser → Streamlit dễ build hơn nhiều
