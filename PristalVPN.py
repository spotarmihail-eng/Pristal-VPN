import concurrent.futures
import csv
import json
import os
import socket
import subprocess
import threading
import time
import tkinter as tk
import winreg
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import webbrowser
import ctypes

APP = "Pristal VPN"
ROOT = Path(__file__).resolve().parent
CORE = ROOT / "sing-box.exe"
CONFIG = ROOT / "pristal-sing-box.json"
TIMEOUT = 2.5
SOURCES = [
    ("SOCKS5", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "socks"),
    ("HTTP", "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "http"),
]

def download_list(url):
    req = Request(url, headers={"User-Agent": "PristalVPN/0.1"})
    with urlopen(req, timeout=20) as response:
        return response.read(3_000_000).decode("utf-8", "replace")

def parse_line(line, scheme):
    line = line.strip()
    if not line or line.startswith("#") or ":" not in line:
        return None
    try:
        host, port_text = line.rsplit(":", 1)
        port = int(port_text)
        if not host or not 1 <= port <= 65535:
            return None
        return {"scheme": scheme, "host": host.strip("[]"), "port": port}
    except (ValueError, TypeError):
        return None

def tcp_probe(item):
    started = time.perf_counter()
    try:
        with socket.create_connection((item["host"], item["port"]), timeout=TIMEOUT):
            return item, round((time.perf_counter() - started) * 1000), True
    except OSError:
        return item, None, False

class PristalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pristal VPN")
        self.root.geometry("900x610")
        self.root.minsize(740, 480)
        self.proxies = {}
        self.process = None
        self.old_enabled = None
        self.old_server = None
        self.busy = False
        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        header = ttk.Frame(self.root, padding=14)
        header.pack(fill="x")
        ttk.Label(header, text="PRISTAL VPN", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        ttk.Label(header, text="Бесплатный менеджер публичных прокси для Windows",
                  foreground="#555").pack(anchor="w")
        actions = ttk.Frame(self.root, padding=(14, 4))
        actions.pack(fill="x")
        self.scan_button = ttk.Button(actions, text="Найти прокси", command=self.scan)
        self.scan_button.pack(side="left")
        ttk.Button(actions, text="Официальный sing-box", command=lambda: webbrowser.open(
            "https://github.com/SagerNet/sing-box/releases")).pack(side="left", padx=8)

        columns = ("type", "host", "port", "latency", "status")
        self.table = ttk.Treeview(self.root, columns=columns, show="headings")
        for key, label, width in [
            ("type", "Тип", 90), ("host", "Сервер", 440), ("port", "Порт", 80),
            ("latency", "TCP отклик", 110), ("status", "Статус", 120)
        ]:
            self.table.heading(key, text=label)
            self.table.column(key, width=width, anchor="w" if key == "host" else "center")
        self.table.pack(fill="both", expand=True, padx=14, pady=8)

        buttons = ttk.Frame(self.root, padding=(14, 4))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Запустить выбранный", command=self.start_selected).pack(side="left")
        ttk.Button(buttons, text="Остановить", command=self.stop).pack(side="left", padx=8)
        ttk.Button(buttons, text="Экспорт CSV", command=self.export).pack(side="left")
        warning = ("Внимание: проверяется только доступность TCP-порта, не работа протокола, "
                   "анонимность или безопасность. Не вводите через публичные прокси пароли, "
                   "платёжные данные и другую чувствительную информацию.")
        ttk.Label(self.root, text=warning, wraplength=860, foreground="#8a4b00",
                  padding=12).pack(fill="x")
        self.status = tk.StringVar(value="Нажмите «Найти прокси».")
        ttk.Label(self.root, textvariable=self.status, relief="sunken",
                  anchor="w", padding=7).pack(fill="x", side="bottom")

    def set_status(self, value):
        self.root.after(0, lambda: self.status.set(value))

    def scan(self):
        if self.busy:
            return
        self.busy = True
        self.scan_button.configure(state="disabled")
        for row in self.table.get_children():
            self.table.delete(row)
        self.proxies.clear()
        self.status.set("Загружаю открытые списки прокси…")
        threading.Thread(target=self.scan_worker, daemon=True).start()

    def scan_worker(self):
        unique = {}
        for _, url, scheme in SOURCES:
            try:
                for line in download_list(url).splitlines():
                    item = parse_line(line, scheme)
                    if item:
                        unique[(scheme, item["host"], item["port"])] = item
            except Exception as exc:
                self.set_status(f"Источник временно недоступен: {exc}")
        candidates = list(unique.values())[:400]
        self.set_status(f"Найдено {len(candidates)} адресов. Проверяю TCP-доступность…")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=80) as pool:
            for item, latency, ok in pool.map(tcp_probe, candidates):
                if ok:
                    results.append((item, latency))
        results.sort(key=lambda result: result[1])

        def finish():
            for item, latency in results:
                row = self.table.insert("", "end", values=(
                    item["scheme"].upper(), item["host"], item["port"],
                    f"{latency} мс", "TCP доступен"))
                self.proxies[row] = {**item, "latency": latency}
            self.status.set(
                f"Найдено {len(results)} TCP-доступных адресов из {len(candidates)}. "
                "Это не гарантия, что прокси работает.")
            self.busy = False
            self.scan_button.configure(state="normal")
        self.root.after(0, finish)

    def selected(self):
        selection = self.table.selection()
        return self.proxies.get(selection[0]) if selection else None

    def start_selected(self):
        item = self.selected()
        if not item:
            messagebox.showinfo(APP, "Сначала выберите прокси в списке.")
            return
        if not CORE.exists():
            messagebox.showwarning(
                APP, "Рядом с PristalVPN.py не найден sing-box.exe. "
                "Скачайте архив Windows AMD64 с официальной страницы релизов "
                "и поместите sing-box.exe рядом с программой.")
            webbrowser.open("https://github.com/SagerNet/sing-box/releases")
            return
        config = {
            "log": {"level": "warn"},
            "inbounds": [{
                "type": "mixed", "tag": "local-in",
                "listen": "127.0.0.1", "listen_port": 2080
            }],
            "outbounds": [{
                "type": item["scheme"], "tag": "proxy",
                "server": item["host"], "server_port": item["port"]
            }, {"type": "direct", "tag": "direct"}],
            "route": {"final": "proxy"}
        }
        CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            self.process = subprocess.Popen(
                [str(CORE), "run", "-c", str(CONFIG)],
                cwd=str(ROOT), creationflags=creationflags)
            self.enable_system_proxy()
            self.status.set(
                f"Локальный прокси запущен: 127.0.0.1:2080 через "
                f"{item['host']}:{item['port']}")
            messagebox.showinfo(
                APP, "Прокси запущен. Windows настроена на 127.0.0.1:2080. "
                "Это системный HTTP-прокси, а не полноценный VPN-туннель. "
                "Игры и UDP-приложения могут его не использовать.")
        except Exception as exc:
            messagebox.showerror(APP, f"Не удалось запустить sing-box: {exc}")
            self.stop()

    def enable_system_proxy(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                            winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
            try:
                self.old_enabled = winreg.QueryValueEx(key, "ProxyEnable")[0]
            except OSError:
                self.old_enabled = 0
            try:
                self.old_server = winreg.QueryValueEx(key, "ProxyServer")[0]
            except OSError:
                self.old_server = ""
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "127.0.0.1:2080")
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)

    def restore_system_proxy(self):
        if self.old_enabled is None:
            return
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD,
                                  int(self.old_enabled))
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ,
                                  str(self.old_server or ""))
            ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0)
        except OSError:
            pass
        self.old_enabled = None
        self.old_server = None

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        self.restore_system_proxy()
        self.status.set("Остановлено; прежние настройки системного прокси восстановлены.")

    def export(self):
        if not self.proxies:
            messagebox.showinfo(APP, "Сначала найдите прокси.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="pristal-proxies.csv")
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["type", "server", "port", "tcp_latency_ms"])
            for item in sorted(self.proxies.values(), key=lambda x: x["latency"]):
                writer.writerow([item["scheme"], item["host"], item["port"], item["latency"]])
        self.status.set(f"Список сохранён: {filename}")

    def close(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    window = tk.Tk()
    PristalApp(window)
    window.mainloop()
