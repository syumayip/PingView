import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
import socket
from ping3 import ping
from ttkthemes import ThemedTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import defaultdict

class PingInfoViewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PingInfoView - Python Version")
        self.root.geometry("1200x900")

        # 目標輸入框
        self.target_label = tk.Label(root, text="目標 (IP 或域名，每行一個):")
        self.target_label.pack(pady=5)
        self.target_text = tk.Text(root, height=10, width=100)
        self.target_text.pack(pady=5)

        # 導入 TXT 文件按鈕
        self.import_button = tk.Button(root, text="導入 TXT 文件", command=self.import_txt)
        self.import_button.pack(pady=5)

        # Ping 設置框架
        self.settings_frame = tk.Frame(root)
        self.settings_frame.pack(pady=10)

        # Ping 間隔設置
        self.interval_label = tk.Label(self.settings_frame, text="Ping 間隔 (秒):")
        self.interval_label.grid(row=0, column=0, padx=5)
        self.interval_entry = tk.Entry(self.settings_frame, width=10)
        self.interval_entry.insert(0, "2")  # 默認間隔為 2 秒
        self.interval_entry.grid(row=0, column=1, padx=5)

        # Ping 超時設置
        self.timeout_label = tk.Label(self.settings_frame, text="Ping 超時 (秒):")
        self.timeout_label.grid(row=0, column=2, padx=5)
        self.timeout_entry = tk.Entry(self.settings_frame, width=10)
        self.timeout_entry.insert(0, "1")  # 默認超時為 1 秒
        self.timeout_entry.grid(row=0, column=3, padx=5)

        # 協議選擇
        self.protocol_label = tk.Label(self.settings_frame, text="協議:")
        self.protocol_label.grid(row=0, column=4, padx=5)
        self.protocol_var = tk.StringVar(value="ICMP")  # 默認為 ICMP
        self.protocol_menu = ttk.Combobox(self.settings_frame, textvariable=self.protocol_var, values=["ICMP", "TCP"])
        self.protocol_menu.grid(row=0, column=5, padx=5)

        # 開始/停止按鈕
        self.start_button = tk.Button(root, text="開始 Ping", command=self.start_ping)
        self.start_button.pack(pady=5)
        self.stop_button = tk.Button(root, text="停止 Ping", command=self.stop_ping, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # 結果顯示表格
        self.tree = ttk.Treeview(root, columns=("Target", "Status", "Response Time", "Protocol"), show="headings")
        self.tree.heading("Target", text="目標")
        self.tree.heading("Status", text="狀態")
        self.tree.heading("Response Time", text="響應時間 (ms)")
        self.tree.heading("Protocol", text="協議")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # 圖表框架
        self.chart_frame = tk.Frame(root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 初始化圖表
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 導出按鈕
        self.export_button = tk.Button(root, text="導出結果", command=self.export_results)
        self.export_button.pack(pady=5)

        # 狀態變量
        self.is_pinging = False
        self.targets = []
        self.ping_threads = []
        self.history = defaultdict(list)  # 用於存儲 Ping 歷史數據

    def import_txt(self):
        """從 TXT 文件導入目標地址"""
        file_path = filedialog.askopenfilename(filetypes=[("TXT 文件", "*.txt")])
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                targets = file.read().splitlines()
                self.target_text.delete("1.0", tk.END)
                self.target_text.insert("1.0", "\n".join(targets))
        except Exception as e:
            messagebox.showerror("錯誤", f"無法讀取文件: {e}")

    def start_ping(self):
        """開始 Ping 操作"""
        # 獲取目標列表
        self.targets = self.target_text.get("1.0", tk.END).strip().splitlines()
        if not self.targets:
            messagebox.showwarning("警告", "請輸入至少一個目標！")
            return

        # 獲取 Ping 間隔和超時時間
        try:
            interval = float(self.interval_entry.get())
            timeout = float(self.timeout_entry.get())
            if interval <= 0 or timeout <= 0:
                raise ValueError("間隔和超時必須大於 0")
        except ValueError as e:
            messagebox.showwarning("警告", f"無效的輸入: {e}")
            return

        # 清空表格和歷史數據
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.history.clear()

        # 啟用停止按鈕，禁用開始按鈕
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_pinging = True

        # 啟動多線程 Ping
        for target in self.targets:
            thread = threading.Thread(target=self.ping_target, args=(target, interval, timeout))
            thread.daemon = True
            thread.start()
            self.ping_threads.append(thread)

    def stop_ping(self):
        """停止 Ping 操作"""
        self.is_pinging = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def ping_target(self, target, interval, timeout):
        """Ping 單個目標"""
        while self.is_pinging:
            # 根據協議選擇 Ping 方法
            protocol = self.protocol_var.get()
            if protocol == "ICMP":
                response_time = self.icmp_ping(target, timeout)
            elif protocol == "TCP":
                response_time = self.tcp_ping(target, timeout)
            else:
                response_time = None

            # 更新表格和歷史數據
            status = "在線" if response_time is not None else "離線"
            response_time_display = f"{response_time:.2f}" if response_time else "超時"
            self.history[target].append(response_time if response_time else 0)  # 存儲歷史數據

            # 更新 UI
            self.root.after(0, self.update_table, target, status, response_time_display, protocol)
            self.root.after(0, self.update_chart)

            # 等待下一次 Ping
            time.sleep(interval)

    def update_table(self, target, status, response_time, protocol):
        """更新表格"""
        self.tree.insert("", tk.END, values=(target, status, response_time, protocol))

    def update_chart(self):
        """更新圖表"""
        self.ax.clear()
        for target, data in self.history.items():
            self.ax.plot(data, label=target)
        self.ax.set_xlabel("Ping 次數")
        self.ax.set_ylabel("響應時間 (ms)")
        self.ax.legend()
        self.canvas.draw()

    def icmp_ping(self, target, timeout):
        """ICMP Ping"""
        try:
            response_time = ping(target, timeout=timeout, unit='ms')
            return response_time
        except Exception:
            return None

    def tcp_ping(self, target, timeout):
        """TCP Ping"""
        try:
            start_time = time.time()
            with socket.create_connection((target, 80), timeout=timeout):
                return (time.time() - start_time) * 1000  # 轉換為毫秒
        except Exception:
            return None

    def export_results(self):
        """導出結果到文件"""
        if not self.targets:
            messagebox.showwarning("警告", "沒有可導出的數據！")
            return

        # 選擇文件路徑
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if not file_path:
            return

        # 寫入 CSV 文件
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["目標", "狀態", "響應時間 (ms)", "協議"])
            for row in self.tree.get_children():
                writer.writerow(self.tree.item(row)["values"])

        messagebox.showinfo("導出成功", f"結果已導出到 {file_path}")

if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # 使用 ttkthemes 美化界面
    app = PingInfoViewApp(root)
    root.mainloop()
