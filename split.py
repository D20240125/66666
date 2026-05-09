from pypdf import PdfReader, PdfWriter
import os
import csv
import time
import tkinter as tk
from tkinter import filedialog, ttk

# ====== 拖拽支持 ======
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    root = TkinterDnD.Tk()
    DND_AVAILABLE = True
except:
    root = tk.Tk()
    DND_AVAILABLE = False

root.title("PDF Tools by xinling")
root.geometry("1100x900")
root.configure(bg="#eef2f7")
import sys
import os

icon_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "icon.ico")
root.iconbitmap(icon_path)

# ====== 变量 ======
input_pdf = tk.StringVar()
output_dir = tk.StringVar()

# ====== 新增：多文件缓存 ======
multi_files = []

# ====== 颜色 ======
CARD = "#ffffff"
PRIMARY = "#4a90e2"
PRIMARY_HOVER = "#357ABD"

# ====== 主布局 ======
main = tk.Frame(root, bg="#eef2f7")
main.pack(fill="both", expand=True, padx=10, pady=10)

left = tk.Frame(main, bg="#eef2f7")
right = tk.Frame(main, bg="#1e1e1e")

left.pack(side="left", fill="both", expand=True, padx=5)
right.pack(side="right", fill="both", expand=True, padx=5)

# ====== 日志 ======
def log(msg, level="info"):
    now = time.strftime("%H:%M:%S")

    # ✅ 新增：统一路径斜杠（核心）
    if isinstance(msg, str):
        msg = msg.replace("\\", "/")

    text_log.insert("end", f"[{now}]{msg}\n", level)
    text_log.see("end")

# ====== 新增：分块日志 ======
def log_block(title):
    log("=========="+title+"==========")

def init_log_tags():
    colors = {
        "info": "#cccccc",
        "ok": "#00ffcc",
        "warn": "#ffcc00",
        "error": "#ff4d4f"
    }
    for k, v in colors.items():
        text_log.tag_config(k, foreground=v)

# ====== 卡片 ======
def card(title, parent=left):
    f = tk.Frame(parent, bg=CARD, highlightthickness=1,
                 highlightbackground="#dcdfe6")
    f.pack(fill="x", padx=15, pady=8)

    tk.Label(
        f,
        text=title,
        bg=CARD,
        font=("微软雅黑", 11, "bold"),
        fg="#333"
    ).pack(anchor="w", padx=10, pady=(6, 2))

    return f

# ====== 输入组件 ======
def styled_entry(parent, var=None):
    e = tk.Entry(parent, textvariable=var, font=("微软雅黑", 10),
                 relief="flat", highlightthickness=1,
                 highlightbackground="#c0c4cc", highlightcolor=PRIMARY)
    e.pack(fill="x", padx=10, pady=6, ipady=6)
    return e

def styled_text(parent, h=6):
    t = tk.Text(parent, height=h, font=("Consolas", 10),
                relief="flat", highlightthickness=1,
                highlightbackground="#c0c4cc", highlightcolor=PRIMARY)
    t.pack(fill="both", padx=10, pady=6)
    return t

def hover(btn):
    btn.bind("<Enter>", lambda e: btn.config(bg=PRIMARY_HOVER))
    btn.bind("<Leave>", lambda e: btn.config(bg=PRIMARY))

# ====== 文件 ======
def select_file():
    global multi_files
    # ====== 新增：支持多选 ======
    files = filedialog.askopenfilenames(filetypes=[("所有文件", "*.*")])
    if files:
        multi_files = list(files)
        input_pdf.set(files[0])
        log(f"[INFO]已选择{len(files)}个文件")
        for f in files:
            log(f"[FILE]{f}")

def select_folder():
    d = filedialog.askdirectory()
    if d:
        output_dir.set(d)
        log(f"[INFO]输出目录:{d}")

def drop(event):
    global multi_files
    try:
        files = root.tk.splitlist(event.data)
    except:
        files = [event.data.strip("{}").strip('"')]

    # ====== 新增：多文件拖拽 ======
    multi_files = list(files)

    if files:
        input_pdf.set(files[0])
        log(f"[INFO]拖入{len(files)}个文件")
        for f in files:
            log(f"[FILE]{f}")

# ====== 解析 ======
def parse_input(text):
    raw = text.replace("，", ",")
    out = []
    for p in raw.split(","):
        for s in p.splitlines():
            v = s.strip()
            if v:
                out.append(v)
    return out

# ====== 主逻辑 ======
def process():
    text_log.delete("1.0", "end")
    start_time = time.time()

    log_block("开始处理")

    progress["value"] = 0
    progress_label.config(text="0%")

    path = input_pdf.get()
    if not path:
        log("[ERROR]未选择PDF文件", "error")
        return

    # ====== 新增：多文件模式 ======
    if len(multi_files) > 1:
        log_block("多文件重命名")

        names = parse_input(text_names.get("1.0", "end").strip())

        if len(names) != len(multi_files):
            log("[ERROR]名称数量不一致", "error")
            return

        if len(names) != len(set(names)):
            log("[ERROR]存在重复名称", "error")
            return

        # ====== 新增：排序规则（按文件名） ======
        files_sorted = sorted(multi_files, key=lambda x: os.path.basename(x))

        for old, new in zip(files_sorted, names):
            ext = os.path.splitext(old)[1]
            newf = os.path.join(os.path.dirname(old), f"{new}{ext}")

            if os.path.exists(newf):
                log(f"[WARN]已存在:{newf}", "warn")
                continue

            try:
                os.rename(old, newf)
                log(f"[OK]{old}->{newf}", "ok")
            except Exception as e:
                log(f"[ERROR]重命名失败:{old}{str(e)}", "error")

        log_block("完成")
        return

    log(f"[INFO]输入文件:{path}")

    outdir = output_dir.get().strip() or os.getcwd()
    log(f"[INFO]输出目录:{outdir}")

    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir)
            log(f"[INFO]已创建目录:{outdir}")
        except Exception as e:
            log(f"[ERROR]输出路径无效:{e}", "error")
            return

    try:
        reader = PdfReader(path)
        total = len(reader.pages)
        log(f"[INFO]总页数:{total}")
    except Exception as e:
        log(f"[ERROR]读取失败:{str(e)}", "error")
        return

    try:
        rule = text_rules.get("1.0", "end").strip()

        if rule.isdigit():
            size = int(rule)
            splits = [size] * (total // size + 1)
        else:
            splits = [int(x) for x in parse_input(rule)]

        if not splits:
            raise ValueError

        log(f"[INFO]拆分规则:{splits}")

    except:
        log("[ERROR]拆分规则格式错误", "error")
        return

    start = 0
    output_files = []

    for i, num in enumerate(splits):
        if start >= total:
            break

        log(f"[STEP]第{i+1}段:{num}页(起始{start+1})")

        writer = PdfWriter()
        end = min(start + num, total)

        for j in range(start, end):
            writer.add_page(reader.pages[j])

        name = f"{i+1:02d}_output.pdf"
        full_path = os.path.join(outdir, name)

        try:
            with open(full_path, "wb") as f:
                writer.write(f)
            log(f"[OK]生成:{full_path}", "ok")
        except Exception as e:
            log(f"[ERROR]写入失败:{name}{str(e)}", "error")
            return

        output_files.append((full_path, num))
        start += num

        percent = (start / total) * 100
        progress["value"] = percent
        progress_label.config(text=f"{percent:.1f}%")
        root.update_idletasks()

    progress["value"] = 100
    progress_label.config(text="100%")

    if not output_files:
        log("[ERROR]未生成文件", "error")
        return

    # ====== 校验 ======
    log_block("校验")

    result = []
    err = 0

    for f, exp in output_files:
        try:
            r = PdfReader(f)
            act = len(r.pages)
            ok = act == exp
            log(f"[CHECK]{os.path.basename(f)}|期望:{exp}|实际:{act}")
            if not ok:
                err += 1
        except:
            act = "失败"
            ok = False
            err += 1

        result.append({
            "文件名": os.path.basename(f),
            "期望页数": exp,
            "实际页数": act,
            "结果": "正确" if ok else "错误"
        })

        root.update_idletasks()

    try:
        if result:
            csv_path = os.path.join(outdir, "拆分结果.csv")
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=result[0].keys())
                w.writeheader()
                w.writerows(result)
            log(f"[INFO]CSV路径:{csv_path}")
    except Exception as e:
        log(f"[ERROR]CSV写入失败:{str(e)}", "error")

    if err == 0:
        log(f"[OK]全部正确:{len(result)}个", "ok")
    else:
        log(f"[WARN]存在问题:{err}个", "warn")

    name_input = text_names.get("1.0", "end").strip()

    if name_input:
        log_block("重命名")

        names = parse_input(name_input)

        if len(names) != len(output_files):
            log("[ERROR]名称数量不一致", "error")
            return

        if len(names) != len(set(names)):
            log("[ERROR]存在重复名称", "error")
            return

        for (old, _), new in zip(output_files, names):
            newf = os.path.join(outdir, f"{new}.pdf")

            if os.path.exists(newf):
                log(f"[WARN]已存在:{newf}", "warn")
                continue

            try:
                os.rename(old, newf)
                log(f"[OK]{old}->{newf}", "ok")
            except Exception as e:
                log(f"[ERROR]重命名失败:{old}{str(e)}", "error")
    else:
        log("[INFO]未执行重命名")

    duration = time.time() - start_time
    log_block("完成")
    log(f"[INFO]输出:{len(output_files)}")
    log(f"[INFO]错误:{err}")
    log(f"[INFO]耗时:{duration:.2f}s")

# ====== UI ======
c_tip = card("📘 使用说明")
tk.Label(
    c_tip,
    text=(
        "1. 选择或拖入 PDF 文件\n"
        "2. 输入拆分规则（如：2,3,5 或 单个数字）\n"
        "3. 可选填写新文件名（逐行或逗号分隔）\n"
        "4. 点击开始处理\n"
        "※ 输出路径为空时默认当前目录"
    ),
    bg=CARD, fg="#666", justify="left", font=("微软雅黑", 9)
).pack(anchor="w", padx=10, pady=6)

c1 = card("📂 PDF文件")
e = styled_entry(c1, input_pdf)
if DND_AVAILABLE:
    e.drop_target_register(DND_FILES)
    e.dnd_bind("<<Drop>>", drop)

btn_file = tk.Button(c1, text="选择文件", bg=PRIMARY, fg="white", relief="flat", command=select_file)
btn_file.pack(pady=6)
hover(btn_file)

c_out = card("📁 输出路径")
styled_entry(c_out, output_dir)
btn_folder = tk.Button(c_out, text="选择文件夹", bg=PRIMARY, fg="white", relief="flat", command=select_folder)
btn_folder.pack(pady=6)
hover(btn_folder)

c2 = card("📝 拆分规则")
text_rules = styled_text(c2, 5)

c3 = card("🏷 新文件名")
text_names = styled_text(c3, 5)

btn_run = tk.Button(left, text="🚀 开始处理", height=2,
                    bg=PRIMARY, fg="white",
                    font=("微软雅黑", 12, "bold"),
                    command=process)
btn_run.pack(pady=12, fill="x", padx=20)
hover(btn_run)

progress = ttk.Progressbar(left)
progress.pack(fill="x", padx=20)
progress_label = tk.Label(left, text="0%", bg="#eef2f7")
progress_label.pack()

tk.Label(right, text="运行日志", bg="#1e1e1e", fg="white").pack(anchor="w", padx=10)

frame_log = tk.Frame(right, bg="#1e1e1e")
frame_log.pack(fill="both", expand=True, padx=10, pady=10)

scroll_y = tk.Scrollbar(frame_log)
scroll_y.pack(side="right", fill="y")

scroll_x = tk.Scrollbar(frame_log, orient="horizontal")
scroll_x.pack(side="bottom", fill="x")

text_log = tk.Text(frame_log, bg="#111", fg="#eee",
                   insertbackground="white",
                   font=("Consolas", 10),
                   yscrollcommand=scroll_y.set,
                   xscrollcommand=scroll_x.set,
                   wrap="none")

text_log.pack(fill="both", expand=True)

scroll_y.config(command=text_log.yview)
scroll_x.config(command=text_log.xview)

init_log_tags()

# ====== 新增：防崩溃 ======
import traceback, sys
def global_exception_hook(exc_type, exc_value, exc_traceback):
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        log("[ERROR]崩溃\n"+err, "error")
    except:
        print(err)

sys.excepthook = global_exception_hook

log("[INFO]程序已启动")

if not DND_AVAILABLE:
    log("[WARN]未安装tkinterdnd2", "warn")

root.mainloop()