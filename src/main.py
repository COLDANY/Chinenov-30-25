import argparse
import os
import tkinter as tk
import zipfile

CURRENT_PATH = "/"
VFS_TREE = {}


def parse_args():
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор UNIX")
    parser.add_argument("--vfs", default="vfs.zip", help="Путь к ZIP VFS")
    parser.add_argument("--script", default="script.txt", help="Путь к скрипту")
    return parser.parse_args()


def on_enter(event):
    """Обработчик нажатия клавиши Enter."""
    global CURRENT_PATH
    text_widget = event.widget
    last_line_idx = text_widget.index("end-1c linestart")
    full_line = text_widget.get(last_line_idx, "end-1c")

    prompt = f"vfs-system:{CURRENT_PATH}$ "
    command_line = full_line.replace(prompt, "", 1).strip()
    text_widget.insert(tk.END, "\n")

    execute_command(command_line, text_widget)
    text_widget.insert(tk.END, f"vfs-system:{CURRENT_PATH}$ ")
    return "break"


def run_startup_script(script_path, text_widget):
    """Выполняет стартовый скрипт построчно до первой ошибки."""
    global CURRENT_PATH
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            cmd = line.strip()
            if not cmd:
                continue
            text_widget.insert(tk.END, f"vfs-system:{CURRENT_PATH}$ {cmd}\n")
            if not execute_command(cmd, text_widget):
                text_widget.insert(tk.END, "Выполнение прервано.\n")
                break


def cmd_exit(args, text_widget):
    """Выход из программы."""
    text_widget.quit()
    return True


def cmd_clear(args, text_widget):
    """Очистка экрана."""
    text_widget.delete("1.0", tk.END)
    return True


def cmd_echo(args, text_widget):
    """Вывод текста."""
    text_widget.insert(tk.END, " ".join(args) + "\n")
    return True


def cmd_ls(args, text_widget):
    """Просмотр содержимого каталога VFS."""
    node = get_node_by_path(CURRENT_PATH)
    if node is not None:
        text_widget.insert(tk.END, "  ".join(node.keys()) + "\n")
        return True
    return False


def cmd_cd(args, text_widget):
    """Смена текущей директории."""
    global CURRENT_PATH
    target = args[0] if args else "/"
    
    if target == "/":
        CURRENT_PATH = "/"
    else:
        new_p = (
            f"{CURRENT_PATH}/{target}".replace("//", "/")
            if CURRENT_PATH != "/"
            else f"/{target}"
        )
        if get_node_by_path(new_p) is not None:
            CURRENT_PATH = new_p
        else:
            text_widget.insert(tk.END, f"cd: {target}: нет папки\n")
            return False
    return True


def cmd_cp_mv(command, args, text_widget):
    """Копирование и перемещение элементов VFS."""
    if len(args) < 2:
        text_widget.insert(tk.END, f"{command}: требуется два аргумента\n")
        return False

    src_arg, dest_arg = args[0], args[1]
    src_f = (
        src_arg
        if src_arg.startswith("/")
        else f"{CURRENT_PATH}/{src_arg}".replace("//", "/")
    )
    src_dp = "/".join(src_f.split("/")[:-1]) if "/".join(src_f.split("/")[:-1]) else "/"
    src_n = src_f.split("/")[-1]

    dest_f = (
        dest_arg
        if dest_arg.startswith("/")
        else f"{CURRENT_PATH}/{dest_arg}".replace("//", "/")
    )
    dest_dp = (
        "/".join(dest_f.split("/")[:-1]) if "/".join(dest_f.split("/")[:-1]) else "/"
    )
    dest_n = dest_f.split("/")[-1]

    src_node = get_node_by_path(src_dp)
    dest_node = get_node_by_path(dest_dp)

    if src_node is not None and src_n in src_node and dest_node is not None:
        if (
            dest_n in dest_node
            and isinstance(dest_node[dest_n], dict)
            and dest_arg.endswith(dest_n)
        ):
            dest_parent = dest_node[dest_n]
            final_dest_name = src_n
        else:
            dest_parent = dest_node
            final_dest_name = dest_n

        if command == "cp":
            dest_parent[final_dest_name] = src_node[src_n].copy()
        else:
            dest_parent[final_dest_name] = src_node[src_n]
            del src_node[src_n]
        return True
    text_widget.insert(tk.END, f"{command}: неверный путь или файл не найден\n")
    return False


# Картотека команд для исключения цикломатической сложности (McCabe = 1)
COMMAND_MAP = {
    "exit": cmd_exit,
    "clear": cmd_clear,
    "echo": cmd_echo,
    "ls": cmd_ls,
    "cd": cmd_cd,
}


def execute_command(command_line, text_widget):
    """Маршрутизатор команд через паттерн словарь-диспетчер."""
    parts = command_line.split()
    if not parts:
        return True

    command = parts[0]
    args = parts[1:]

    # Ищем команду в словаре готовых функций
    if command in COMMAND_MAP:
        return COMMAND_MAP[command](args, text_widget)
    elif command in ("cp", "mv"):
        return cmd_cp_mv(command, args, text_widget)

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
    """Загружает структуру архива в память."""
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
    """Возвращает узел дерева VFS по пути."""
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
    """Точка входа."""
    args = parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)

    script_path = (
        os.path.join(project_root, "script.txt")
        if args.script == "script.txt"
        else args.script
    )
    vfs_path = (
        os.path.join(project_root, "vfs.zip")
        if args.vfs == "vfs.zip"
        else args.vfs
    )

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