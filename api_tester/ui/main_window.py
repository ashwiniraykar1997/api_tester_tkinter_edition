import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import psycopg2
import json
import time
from datetime import datetime
import os, sys

class ApiTesterApp:
    def __init__(self):
    
        def resource_path(relative_path):
            """Get absolute path to resource, works for dev and for PyInstaller .exe"""
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        self.root = tk.Tk()
        self.root.title("API Tester - Tkinter Edition")
        self.root.geometry("950x700")
        # os.makedirs(resource_path("data"), exist_ok=True)

        icon_path = resource_path("assets\\icons\\app.ico") 
        
        self.root.iconbitmap(icon_path)


        self.dark_mode = False  # Track theme state

        # Connect DB first
        self.connect_db()

        # Then create GUI widgets
        self.create_widgets()

    # -------------------------
    # DATABASE CONNECTION
    # -------------------------
    def connect_db(self):
        try:
            self.conn = psycopg2.connect(
                dbname="api_tester_db",
                user="postgres",       # change as needed
                password="postgres",
                host="localhost",
                port="5432"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            self.cursor = None
            messagebox.showerror("Database Error", str(e))

    # -------------------------
    # MAIN UI
    # -------------------------
    def create_widgets(self):
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="URL:").pack(side="left")
        self.url_entry = ttk.Entry(frame_top, width=60)
        self.url_entry.pack(side="left", padx=5)

        self.method_var = tk.StringVar(value="GET")
        ttk.Combobox(
            frame_top,
            textvariable=self.method_var,
            values=["GET", "POST", "PUT", "DELETE"],
            width=8
        ).pack(side="left")

        ttk.Button(frame_top, text="Send", command=self.send_request).pack(side="left", padx=5)
        ttk.Button(frame_top, text="History", command=self.open_history_window).pack(side="left", padx=5)
        
        # 🌙 Add Dark Mode button here
        self.dark_mode_button = tk.Button(frame_top, text="🌙 Dark Mode", command=self.toggle_theme)
        self.dark_mode_button.pack(side="left", padx=5)

        # -----------------------------
        # Request/Response Section
        # -----------------------------
        frame_mid = ttk.Frame(self.root, padding=10)
        frame_mid.pack(fill="both", expand=True)

        # Headers
        ttk.Label(frame_mid, text="Headers (JSON):").pack(anchor="w")
        self.headers_text = tk.Text(frame_mid, height=5, font=("Consolas", 10))
        self.add_scrollbar(self.headers_text, frame_mid)

        # Body
        ttk.Label(frame_mid, text="Body (JSON):").pack(anchor="w", pady=(5, 0))
        self.body_text = tk.Text(frame_mid, height=5, font=("Consolas", 10))
        self.add_scrollbar(self.body_text, frame_mid)

        # Response
        ttk.Label(frame_mid, text="Response:").pack(anchor="w", pady=(10, 0))
        self.response_text = tk.Text(frame_mid, height=12, font=("Consolas", 10))
        self.add_scrollbar(self.response_text, frame_mid)

        # Response Buttons
        btn_frame = ttk.Frame(frame_mid)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="💾 Save Response", command=self.save_response).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🧹 Clear", command=self.clear_response).pack(side="left", padx=5)

    # -------------------------
    # SCROLLBAR HELPER
    # -------------------------
    def add_scrollbar(self, text_widget, parent):
        scroll_y = tk.Scrollbar(parent, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll_y.set)
        text_widget.pack(fill="x", pady=3)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    # -------------------------
    # SEND REQUEST
    # -------------------------
    def send_request(self):
        url = self.url_entry.get().strip()
        method = self.method_var.get()
        headers = self.parse_json(self.headers_text.get("1.0", tk.END))
        body = self.parse_json(self.body_text.get("1.0", tk.END))

        if not url:
            messagebox.showwarning("Warning", "Please enter a valid URL.")
            return

        try:
            start_time = time.time()
            response = requests.request(method, url, headers=headers, json=body if body else None)
            elapsed = round(time.time() - start_time, 3)

            result = {
                "status_code": response.status_code,
                "elapsed": elapsed,
                "headers": dict(response.headers),
                "body": response.text
            }

            formatted = json.dumps(result, indent=4)
            self.response_text.delete("1.0", tk.END)
            self.response_text.insert(tk.END, formatted)

            self.save_to_db(method, url, headers, body, response, elapsed)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def parse_json(self, text):
        try:
            return json.loads(text.strip()) if text.strip() else {}
        except json.JSONDecodeError:
            messagebox.showerror("JSON Error", "Invalid JSON format")
            return None

    # -------------------------
    # SAVE TO DATABASE
    # -------------------------
    def save_to_db(self, method, url, headers, body, response, elapsed):
        if not self.cursor:
            messagebox.showerror("Error", "Database not connected.")
            return

        try:
            query = """
            INSERT INTO api_history (method, url, headers, body, status_code, response_time, response_body)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (
                method, url, json.dumps(headers), json.dumps(body),
                response.status_code, elapsed, response.text
            ))
            self.conn.commit()

            # ✅ Automatically back up after each request
            self.backup_history_to_json()

        except Exception as e:
            messagebox.showerror("DB Save Error", str(e))

    # -------------------------
    # HISTORY WINDOW
    # -------------------------
    def open_history_window(self):
        if not self.cursor:
            messagebox.showerror("Error", "Database not connected.")
            return

        win = tk.Toplevel(self.root)
        win.title("Request History")
        win.geometry("850x450")

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("ID", "Method", "URL", "Status", "Time", "Date")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        self.tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="View Details", command=self.show_selected_details).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Export to JSON", command=self.export_to_json).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Backup to history.json", command=self.backup_history_to_json).pack(side="left", padx=5)

        self.load_history_data()

    def load_history_data(self):
        try:
            self.cursor.execute("SELECT id, method, url, status_code, response_time, created_at FROM api_history ORDER BY created_at DESC")
            rows = self.cursor.fetchall()
            for row in rows:
                self.tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def show_selected_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a request to view details.")
            return

        item = self.tree.item(selected[0])
        record_id = item["values"][0]

        try:
            self.cursor.execute("SELECT * FROM api_history WHERE id = %s", (record_id,))
            row = self.cursor.fetchone()
            if not row:
                return

            details_win = tk.Toplevel(self.root)
            details_win.title(f"Request #{record_id}")
            details_win.geometry("700x500")

            text = tk.Text(details_win, font=("Consolas", 10))
            text.pack(fill="both", expand=True)

            details = {
                "Method": row[1],
                "URL": row[2],
                "Headers": row[3],
                "Body": row[4],
                "Status Code": row[5],
                "Response Time": row[6],
                "Response Body": row[7],
                "Created At": str(row[8]),
            }

            formatted = json.dumps(details, indent=4, default=str)
            text.insert("1.0", formatted)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # -------------------------
    # EXPORT & BACKUP
    # -------------------------
    def export_to_json(self):
        try:
            self.cursor.execute("SELECT * FROM api_history ORDER BY created_at DESC")
            rows = self.cursor.fetchall()
            if not rows:
                messagebox.showinfo("Info", "No records to export.")
                return

            records = []
            for row in rows:
                records.append({
                    "id": row[0],
                    "method": row[1],
                    "url": row[2],
                    "headers": row[3],
                    "body": row[4],
                    "status_code": row[5],
                    "response_time": row[6],
                    "response_body": row[7],
                    "created_at": str(row[8])
                })

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Save History As"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=4)
                messagebox.showinfo("Success", f"History exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


    def backup_history_to_json(self):
        try:
            # ✅ Determine base directory for both dev and exe
            if getattr(sys, 'frozen', False):
                # If running from PyInstaller .exe (→ Go one level up from dist/)
                base_dir = os.path.abspath(os.path.join(os.path.dirname(sys.executable), ".."))
            else:
                # If running from source (main_window.py inside ui/)
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

            # ✅ Correct path to the data folder in project root
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            backup_path = os.path.join(data_dir, "history.json")

            # Fetch all records
            self.cursor.execute("SELECT * FROM api_history ORDER BY created_at DESC")
            rows = self.cursor.fetchall()

            if not rows:
                messagebox.showinfo("Info", "No records found to back up.")
                return

            records = []
            for row in rows:
                records.append({
                    "id": row[0],
                    "method": row[1],
                    "url": row[2],
                    "headers": row[3],
                    "body": row[4],
                    "status_code": row[5],
                    "response_time": row[6],
                    "response_body": row[7],
                    "created_at": str(row[8])
                })

            # ✅ Save to the correct project-level path
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=4)

            messagebox.showinfo("Backup", f"History backed up to {backup_path}")

        except Exception as e:
            messagebox.showerror("Backup Error", str(e))

    # -------------------------
    # SAVE / CLEAR RESPONSE
    # -------------------------
    def save_response(self):
        response_data = self.response_text.get("1.0", tk.END).strip()
        if not response_data:
            messagebox.showinfo("Info", "No response to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response_data)
            messagebox.showinfo("Saved", f"Response saved to {file_path}")

    def clear_response(self):
        self.response_text.delete("1.0", tk.END)

    # -------------------------
    # DARK MODE TOGGLE
    # -------------------------
    def toggle_theme(self):
        self.dark_mode = not getattr(self, "dark_mode", False)

        bg = "#2b2b2b" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"

        # Update main window background
        self.root.configure(bg=bg)

        # Update all Text widgets
        for widget in self.root.winfo_children():
            self._apply_theme_recursively(widget, bg, fg)

        # Update button text
        self.dark_mode_button.configure(
            text="☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode"
        )

    def _apply_theme_recursively(self, widget, bg, fg):
        """Recursively apply dark/light colors to all child widgets"""
        try:
            if isinstance(widget, (tk.Text, tk.Entry)):
                widget.configure(bg=bg, fg=fg, insertbackground=fg)
            elif isinstance(widget, (ttk.Frame, tk.Frame, tk.LabelFrame)):
                widget.configure(bg=bg)
            elif isinstance(widget, tk.Label):
                widget.configure(bg=bg, fg=fg)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=bg, fg=fg, activebackground=fg, activeforeground=bg)
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._apply_theme_recursively(child, bg, fg)


        # Optional: Apply ttk theme if using ttk widgets
        # self.apply_ttk_theme()


    # -------------------------
    # RUN APP
    # -------------------------
    def run(self):
        self.root.mainloop()

