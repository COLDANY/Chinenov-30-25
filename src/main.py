import argparse
import tkinter as tk
import os

CURRENT_PATH = "/"
def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор командной строки " \
    "UNIX")
    parser.add_argument(
        "--vfs",
        default="vfs.zip",
        help="Путь к ZIP-архиву виртуальной файловой системы",
    )

    parser.add_argument(
        "--script",
        default="script.txt",
        help="Путь к стартовому текстовому скрипту",
    )
    return parser.parse_args()

def on_enter(event):
    global CURRENT_PATH
    
    text_widget = event.widget
    last_line_idx = text_widget.index("end-1c linestart")
    full_line = text_widget.get(last_line_idx, "end-1c")

    prompt = f"vfs-machine:{CURRENT_PATH}$ "
    command_line = full_line.replace(prompt,"",1).strip()
    text_widget.insert(tk.END, "\n")

    execute_command(command_line, text_widget)

    text_widget.insert(tk.END, f"vfs-machine:{CURRENT_PATH}$ ")
    return "break"

def run_startup_script(script_path, text_widget):
    global CURRENT_PATH

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:

            command_line = line.strip()
            if not command_line:
                continue

            text_widget.insert(tk.END, f"vfs-" \
                               "system:{CURRENT_PATH}$ {command_line}\n")
            success = execute_command(command_line, text_widget)

            if not success:
                text_widget.insert(tk.END, "Выполнение с" \
                                   "крипта прервано из-за ошибки.\n")
                break

def execute_command(command_line, text_widget):
    parts = command_line.split()
    
    if not parts:
        return True

    command = parts[0]
    args = parts[1:]

    if command == "exit":
        text_widget.quit()
        return True
        
    elif command in ("ls", "cd"):
        output = f"Вызвана заглушка {command} с аргументами: {args}\n"
        text_widget.insert(tk.END, output)
        return True
        
    else:
        text_widget.insert(tk.END, f"{command}: команда не найдена\n")
        return False
    
def check_backspace(event):
    """Блокирует BackSpace, если курсор дошел до префикса."""
    text_widget = event.widget
    cursor_pos = text_widget.index(tk.INSERT)
    line_start = text_widget.index("end-1c linestart")
    prompt_len = len(f"vfs-machine:{CURRENT_PATH}$  ")
    prefix_end = f"{line_start}+{prompt_len}c"

    if text_widget.compare(cursor_pos, "<=", prefix_end):
        return "break"

def main():
    args = parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    script_path = args.script
    if script_path == "script.txt":
        script_path = os.path.join(project_root, "script.txt")

    root = tk.Tk()
    root.title("vfs-machine")
    root.geometry("600x400")
    text = tk.Text(root, bg="black", fg="white", insertbackground="white")
    text.pack(expand = True, fill = "both")

    text.insert(tk.END, "=== ОТЛАДОЧНЫЙ ВЫВОД ПАРАМЕТРОВ ===\n")
    text.insert(tk.END, f"Путь к VFS (ZIP): {args.vfs}\n")
    text.insert(tk.END, f"Путь к скрипту: {script_path}\n")
    text.insert(tk.END, "===================================\n\n")

    text.focus_set()
    text.insert(tk.END, f"vfs-machine:{CURRENT_PATH}$ ")

    run_startup_script(script_path, text)

    text.bind("<Return>", on_enter)
    text.bind("<BackSpace>", check_backspace)

    root.mainloop()

if __name__ == "__main__":
    main()