import argparse
import os
import tkinter as tk
import zipfile

current_path = "/"
VFS_TREE = {}


def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор UNIX")
    parser.add_argument("--vfs", default="vfs.zip", help="Путь к ZIP VFS")
    parser.add_argument("--script", default="script.txt", help="Путь к скрипту")
    return parser.parse_args()


def on_enter(event):
    global current_path
    text_widget = event.widget
    last_line_idx = text_widget.index("end-1c linestart")
    full_line = text_widget.get(last_line_idx, "end-1c")

    prompt = f"vfs-system:{current_path}$ "
    command_line = full_line.replace(prompt, "", 1).strip()
    text_widget.insert(tk.END, "\n")

    execute_command(command_line, text_widget)
    text_widget.insert(tk.END, f"vfs-system:{current_path}$ ")
    return "break"


def run_startup_script(script_path, text_widget):
    global current_path
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            cmd = line.strip()
            if not cmd:
                continue
            text_widget.insert(tk.END, f"vfs-system:{current_path}$ {cmd}\n")
            if not execute_command(cmd, text_widget):
                text_widget.insert(tk.END, "Выполнение прервано.\n")
                break


def cmd_exit(args, text_widget):
    text_widget.quit()
    return True


def cmd_clear(args, text_widget):
    text_widget.delete("1.0", tk.END)
    return True


def cmd_echo(args, text_widget):
    text_widget.insert(tk.END, " ".join(args) + "\n")
    return True


def cmd_ls(args, text_widget):
    node = get_node_by_path(current_path)
    if node is not None:
        text_widget.insert(tk.END, "  ".join(node.keys()) + "\n")
        return True
    return False


def cmd_cd(args, text_widget):
    global current_path
    # ИСПРАВЛЕНИЕ: добавляем, чтобы извлечь чистую строку из списка аргументов
    target = args[0] if args else "/"

    if target == "/":
        current_path = "/"
    else:
        if current_path != "/":
            new_p = f"{current_path}/{target}".replace("//", "/")
        else:
            new_p = f"/{target}"

        if get_node_by_path(new_p) is not None:
            current_path = new_p
        else:
            text_widget.insert(tk.END, f"cd: {target}: нет папки\n")
            return False
    return True


def resolve_path(arg_path):
    if arg_path.startswith("/"):
        full_p = arg_path
    else:
        full_p = f"{current_path}/{arg_path}".replace("//", "/")

    split_p = full_p.split("/")
    if "/".join(split_p[:-1]):
        dir_p = "/".join(split_p[:-1])
    else:
        dir_p = "/"
    name = split_p[-1]

    return dir_p, name, full_p


def cmd_cp_mv(command, args, text_widget):
    len_args = 2
    if len(args) < len_args:
        text_widget.insert(tk.END, f"{command}: требуется два аргумента\n")
        return False
    src_arg, dest_arg = args[0], args[1]
    src_dp, src_n, _ = resolve_path(src_arg)
    dest_dp, dest_n, dest_arg = resolve_path(dest_arg)

    src_node = get_node_by_path(src_dp)
    dest_node = get_node_by_path(dest_dp)

    if src_node is not None and src_n in src_node and dest_node is not None:
        if (
            dest_n in dest_node
            and isinstance(dest_node[dest_n], dict)
            and dest_arg.endswith(dest_n)
        ):
            dest_parent = dest_node[dest_n]
            final_name = src_n
        else:
            dest_parent = dest_node
            final_name = dest_n

        if command == "cp":
            dest_parent[final_name] = src_node[src_n].copy()
        else:
            dest_parent[final_name] = src_node[src_n]
            del src_node[src_n]
        return True

    text_widget.insert(
        tk.END, f"{command}: неверный путь или файл не найден\n"
    )
    return False


COMMAND_MAP = {
    "exit": cmd_exit,
    "clear": cmd_clear,
    "echo": cmd_echo,
    "ls": cmd_ls,
    "cd": cmd_cd,
}


def execute_command(command_line, text_widget):
    parts = command_line.split()
    if not parts:
        return True
    command = parts[0]
    args = parts[1:]

    if command in COMMAND_MAP:
        return COMMAND_MAP[command](args, text_widget)
    elif command in ("cp", "mv"):
        return cmd_cp_mv(command, args, text_widget)

    text_widget.insert(tk.END, f"{command}: команда не найдена\n")
    return False


def check_backspace(event):
    text_widget = event.widget
    cursor_pos = text_widget.index(tk.INSERT)
    line_start = text_widget.index("end-1c linestart")
    prompt_len = len(f"vfs-system:{current_path}$ ")
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

    if args.script == "script.txt":
        script_path = os.path.join(project_root, "script.txt")
    else:
        script_path = args.script

    if args.vfs == "vfs.zip":
        vfs_path = os.path.join(project_root, "vfs.zip")
    else:
        vfs_path = args.vfs

    root = tk.Tk()
    root.title("vfs-system")
    root.geometry("600x400")

    text = tk.Text(root, bg="black", fg="white", insertbackground="white")
    text.pack(expand=True, fill="both")

    text.insert(tk.END, "=== ОТЛАДОЧНЫЙ ВЫВОД ПАРАМЕТРОВ ===\n")
    text.insert(tk.END, f"Путь к VFS (ZIP): {vfs_path}\n")
    text.insert(tk.END, f"Путь к скрипту: {script_path}\n")
    text.insert(tk.END, "===================================\n\n")

    text.insert(tk.END, f"vfs-system:{current_path}$ ")
    text.focus_set()
    load_vfs(vfs_path, text)
    run_startup_script(script_path, text)

    text.bind("<Return>", on_enter)
    text.bind("<BackSpace>", check_backspace)
    root.mainloop()


if __name__ == "__main__":
    main()
