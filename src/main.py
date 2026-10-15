import argparse
import tkinter as tk
import os
import zipfile
VFS_TREE = {}

CURRENT_PATH = "/"
VFS_TREE = {}

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

    prompt = f"vfs-system:{CURRENT_PATH}$ "
    command_line = full_line.replace(prompt,"",1).strip()
    text_widget.insert(tk.END, "\n")

    execute_command(command_line, text_widget)

    text_widget.insert(tk.END, f"vfs-system:{CURRENT_PATH}$ ")
    return "break"

def run_startup_script(script_path, text_widget):
    global CURRENT_PATH

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:

            command_line = line.strip()
            if not command_line:
                continue

            text_widget.insert(tk.END, f"vfs-" \
                               f"system:{CURRENT_PATH}$ {command_line}\n")
            success = execute_command(command_line, text_widget)

            if not success:
                text_widget.insert(tk.END, "Выполнение с" \
                                   "крипта прервано из-за ошибки.\n")
                break

def execute_command(command_line, text_widget):
    global CURRENT_PATH
    parts = command_line.split()
    
    if not parts:
        return True

    command = parts[0]
    args = parts[1:]

    if command == "exit":
        text_widget.quit()
        return True
        
    elif command == "clear":  # Добавили команду очистки экрана
        text_widget.delete("1.0", tk.END)
        return True

    elif command == "echo":  # Добавили команду вывода текста
        text_widget.insert(tk.END, " ".join(args) + "\n")
        return True
        
    elif command == "ls":
        current_node = get_node_by_path(CURRENT_PATH)
        # Проверяем, что узел существует, даже если он пустой
        if current_node is not None:
            text_widget.insert(tk.END, "  ".join(current_node.keys()) + "\n")
            return True
        else:
            text_widget.insert(tk.END, "ls: папка не найдена\n")
            return False

    elif command == "cd":
        target = args[0] if args else "/"
        
        if target == "/":
            CURRENT_PATH = "/"
        else:
            if CURRENT_PATH != "/":
                new_path = f"{CURRENT_PATH}/{target}".replace("//", "/")
            else:
                new_path = f"/{target}"
            
            if get_node_by_path(new_path) is not None:
                CURRENT_PATH = new_path
            else:
                text_widget.insert(tk.END, f"cd: {target}: папки не существует\n")
                return False  # Ошибка навигации прерывает скрипт по ТЗ варианта 27
        return True
        
    else:
        text_widget.insert(tk.END, f"{command}: команда не найдена\n")
        return False
    
def check_backspace(event):
    """Блокирует BackSpace, если курсор дошел до префикса."""
    text_widget = event.widget
    cursor_pos = text_widget.index(tk.INSERT)
    line_start = text_widget.index("end-1c linestart")
    prompt_len = len(f"vfs-system:{CURRENT_PATH}$ ")
    prefix_end = f"{line_start}+{prompt_len}c"

    if text_widget.compare(cursor_pos, "<=", prefix_end):
        return "break"
def load_vfs(vfs_path, text_widget):
    global VFS_TREE
    try:
        with zipfile.ZipFile(vfs_path, "r") as z:
            for name in z.namelist():
                parts = [p for p in name.split("/") if p]
                current = VFS_TREE
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        text_widget.insert(tk.END, "VFS успешно загружена в память.\n\n")
        return True
    except (FileNotFoundError, zipfile.BadZipFile):
        text_widget.insert(tk.END, "Ошибка загрузки VFS\n")
        VFS_TREE["home"] = {"user": {}}
        return False
    
def get_node_by_path(path_str):
    """Возвращает узел дерева VFS по текстовому пути."""
    if path_str == "/":
        return VFS_TREE

    parts = [p for p in path_str.split("/") if p]
    current = VFS_TREE

    for part in parts:
        if part in current and isinstance(current[part], dict):
            current = current[part]
        else:
            return None  
            
    return current

def main():
    args = parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)

    script_path = args.script
    if script_path == "script.txt":
        script_path = os.path.join(project_root, "script.txt")

    vfs_path = args.vfs
    if vfs_path == "vfs.zip":
        vfs_path = os.path.join(project_root, "vfs.zip")

    root = tk.Tk()
    root.title("vfs-system")
    root.geometry("600x400")

    text = tk.Text(root, bg="black", fg="white", insertbackground="white")
    text.pack(expand=True, fill="both")

    text.insert(tk.END, "=== ОТЛАДОЧНЫЙ ВЫВОД ПАРАМЕТРОВ ===\n")
    text.insert(tk.END, f"Путь к VFS (ZIP): {vfs_path}\n")
    text.insert(tk.END, f"Путь к скрипту: {script_path}\n")
    text.insert(tk.END, "===================================\n\n")

    text.insert(tk.END, f"vfs-system:{CURRENT_PATH}$ ")
    text.focus_set()
    load_vfs(vfs_path, text)
    
    run_startup_script(script_path, text)

    text.bind("<Return>", on_enter)
    text.bind("<BackSpace>", check_backspace)
    root.mainloop()

if __name__ == "__main__":
    main()