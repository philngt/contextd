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
| Language | Workspace-supported Python, pinned | Verify Tcl/Tk + packaging trên từng target OS |
| GUI library | `tkinter` baseline | Standard Python interface to Tcl/Tk; ít dependency hơn cho form nhỏ |
| Optional GUI layer | `PySimpleGUI` hoặc `PyWebView` | Chỉ chọn sau khi review license/support/version và UI requirement |
| Packaging | `PyInstaller` | Build `.exe` / binary để click chạy không cần Python |

### Linux/macOS native

```bash
python3 -m venv .venv
source .venv/bin/activate
# tkinter built-in (Linux có thể cần): sudo apt install python3-tk
python -m tkinter          # verify Tcl/Tk runtime mở được window
# optional dependency phải pin trong requirements/lock file
python tool.py
```

### Windows native

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m tkinter          # verify Tcl/Tk runtime
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

Build artifact phải tạo/test riêng trên từng target OS/architecture; đừng giả định một binary cross-compile chạy mọi nơi.

## Trade-offs

**Vì sao tkinter baseline**:
- Python distribution thường cung cấp interface Tcl/Tk, nhưng setup phải verify bằng `python -m tkinter` trên target.
- Phù hợp form/event flow nhỏ và tránh thêm web runtime.
- Source có thể dùng chung, nhưng packaging/UI behavior phải test riêng trên từng OS.

**Vì sao KHÔNG**:
- **PySide/Qt**: hợp UI nhiều screen/widget hoặc accessibility/native behavior cao hơn; thêm dependency, packaging và license review.
- **Electron/webview**: hợp khi team đã sở hữu web stack; thêm runtime/distribution surface.
- **Streamlit**: hợp browser workflow và sharing; không phải desktop-native UX.
- **GTK/other native toolkit**: chọn theo target OS/team support, không theo recipe default.

## Optional skeleton — PySimpleGUI (pin/review dependency first)

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
- Form/event/state đủ nhỏ để một window hoặc vài dialog vẫn dễ hiểu/test
- Output text/file đủ — không cần chart phức tạp

❌ **KHÔNG match KHI**:
- Cần share team → `team-shared-web-tool`
- UI cần đẹp / phức tạp → cân nhắc PyWebView hoặc chuyển web app
- Distribution/updates trên nhiều máy cần installer/update/signing plan; cân nhắc web deployment nếu nó giảm vận hành
- User OK với browser → Streamlit dễ build hơn nhiều

Baseline review `2026-08-20`: [Python tkinter documentation](https://docs.python.org/3/library/tkinter.html) và [PySimpleGUI project status](https://docs.pysimplegui.com/FAQ/). Nếu chọn optional wrapper, pin release đã test và re-check support/license trước build.
