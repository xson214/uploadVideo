import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import csv
from tinydb import TinyDB
import subprocess

class CSVGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🗂️ AuTo Upload Tiktok")
        self.root.geometry("1800x900")  # Tăng width lên 1800px để chứa 9 cột
        self.root.configure(bg='#2c3e50')
        
        # Khởi tạo TinyDB
        self.db = TinyDB('accounts.json')
        
        # Cấu hình style cho ttk
        self.setup_styles()
        
        # Header
        self.create_header()
        
        # Main container
        self.create_main_container()
        
        # Control panel
        self.create_control_panel()
        
        # Data table
        self.create_data_table()
        
        # Status bar
        self.create_status_bar()
        
        self.data = []
        self.load_from_db()
    
    def setup_styles(self):
        """Cấu hình styles cho giao diện"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style cho buttons
        style.configure('Modern.TButton',
                       background='#3498db',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        style.map('Modern.TButton',
                 background=[('active', '#2980b9')])
        
        # Style cho buttons nguy hiểm (Delete, Stop)
        style.configure('Danger.TButton',
                       background='#e74c3c',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        style.map('Danger.TButton',
                 background=[('active', '#c0392b')])
        
        # Style cho buttons thành công (Save, Run)
        style.configure('Success.TButton',
                       background='#27ae60',
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(10, 8))
        style.map('Success.TButton',
                 background=[('active', '#229954')])
        
        # Style cho Treeview
        style.configure('Modern.Treeview',
                       background='#ecf0f1',
                       fieldbackground='#ecf0f1',
                       foreground='#2c3e50',
                       borderwidth=0,
                       rowheight=30)
        style.configure('Modern.Treeview.Heading',
                       background='#34495e',
                       foreground='white',
                       borderwidth=0,
                       relief='flat')
        style.map('Modern.Treeview',
                 background=[('selected', '#3498db')])
        
        # Style cho Checkbutton
        style.configure('Modern.TCheckbutton',
                       background='#34495e',
                       foreground='white',
                       focuscolor='none')
        
    def create_header(self):
        """Tạo header với logo và tiêu đề"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo và tiêu đề
        title_frame = tk.Frame(header_frame, bg='#34495e')
        title_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(title_frame, 
                              text="📊 Auto Upload Tiktok",
                              font=('Arial', 24, 'bold'),
                              bg='#34495e',
                              fg='white')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(title_frame,
                                 text="Quản lý và chỉnh sửa dữ liệu CSV một cách chuyên nghiệp",
                                 font=('Arial', 11),
                                 bg='#34495e',
                                 fg='#bdc3c7')
        subtitle_label.pack()
    
    def create_main_container(self):
        """Tạo container chính"""
        self.main_container = tk.Frame(self.root, bg='#ecf0f1')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def create_control_panel(self):
        """Tạo panel điều khiển với thiết kế card"""
        # Control panel container
        control_container = tk.Frame(self.main_container, bg='#ecf0f1')
        control_container.pack(fill=tk.X, pady=(0, 15))
        
        # File operations card
        file_card = tk.Frame(control_container, bg='white', relief='solid', bd=1)
        file_card.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        file_label = tk.Label(file_card, text="📁 File Operations", 
                             font=('Arial', 10, 'bold'),
                             bg='white', fg='#2c3e50')
        file_label.pack(pady=(10, 5))
        
        file_button_frame = tk.Frame(file_card, bg='white')
        file_button_frame.pack(padx=15, pady=(0, 15))
        
        self.import_button = ttk.Button(file_button_frame, text="📤 Import CSV", 
                                       command=self.import_csv, style='Modern.TButton')
        self.import_button.pack(side=tk.LEFT, padx=2)
        
        # Data operations card
        data_card = tk.Frame(control_container, bg='white', relief='solid', bd=1)
        data_card.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        data_label = tk.Label(data_card, text="✏️ Data Operations", 
                             font=('Arial', 10, 'bold'),
                             bg='white', fg='#2c3e50')
        data_label.pack(pady=(10, 5))
        
        data_button_frame = tk.Frame(data_card, bg='white')
        data_button_frame.pack(padx=15, pady=(0, 15))
        
        self.add_button = ttk.Button(data_button_frame, text="➕ Add Row", 
                                    command=self.add_row, style='Success.TButton')
        self.add_button.pack(side=tk.LEFT, padx=2)
        
        self.edit_button = ttk.Button(data_button_frame, text="✏️ Edit Row", 
                                     command=self.edit_row, style='Modern.TButton')
        self.edit_button.pack(side=tk.LEFT, padx=2)
        
        self.delete_button = ttk.Button(data_button_frame, text="🗑️ Delete Row", 
                                       command=self.delete_row, style='Danger.TButton')
        self.delete_button.pack(side=tk.LEFT, padx=2)
        
        # Process control card
        process_card = tk.Frame(control_container, bg='white', relief='solid', bd=1)
        process_card.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        process_label = tk.Label(process_card, text="⚙️ Process Control", 
                                font=('Arial', 10, 'bold'),
                                bg='white', fg='#2c3e50')
        process_label.pack(pady=(10, 5))
        
        process_button_frame = tk.Frame(process_card, bg='white')
        process_button_frame.pack(padx=15, pady=(0, 15))
        
        self.run_button = ttk.Button(process_button_frame, text="▶️ Run", 
                                    command=self.run_process, style='Success.TButton')
        self.run_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(process_button_frame, text="⏹️ Stop", 
                                     command=self.stop_process, style='Danger.TButton')
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # Options card
        options_card = tk.Frame(control_container, bg='white', relief='solid', bd=1)
        options_card.pack(side=tk.LEFT, pady=5)
        
        options_label = tk.Label(options_card, text="⚡ Options", 
                                font=('Arial', 10, 'bold'),
                                bg='white', fg='#2c3e50')
        options_label.pack(pady=(10, 5))
        
        options_frame = tk.Frame(options_card, bg='white')
        options_frame.pack(padx=15, pady=(0, 15))
        
        # Checkbox Upload
        self.upload_var = tk.BooleanVar()
        self.upload_checkbox = tk.Checkbutton(
            options_frame, text="🔄 Upload", variable=self.upload_var, 
            command=self.toggle_upload, bg='white', fg='#2c3e50',
            selectcolor='#3498db', font=('Arial', 9)
        )
        self.upload_checkbox.pack(anchor='w')

        # Checkbox check dash
        self.check_dash = tk.BooleanVar()
        self.check_dash_checkbox = tk.Checkbutton(
            options_frame, text="Check dash", variable=self.check_dash,
            bg='white', fg='#2c3e50', selectcolor='#3498db', font=('Arial', 9)
        )
        self.check_dash_checkbox.pack(anchor='w')

        # Checkbox report
        self.report_var = tk.BooleanVar()
        self.report_checkbox = tk.Checkbutton(
            options_frame, text="📊 Report", variable=self.report_var,
            bg='white', fg='#2c3e50', selectcolor='#3498db', font=('Arial', 9)
        )
        self.report_checkbox.pack(anchor='w')
    
    def create_data_table(self):
        """Tạo bảng dữ liệu với thiết kế đẹp"""
        # Table container
        table_container = tk.Frame(self.main_container, bg='white', relief='solid', bd=1)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Table header
        table_header = tk.Frame(table_container, bg='#34495e', height=40)
        table_header.pack(fill=tk.X)
        table_header.pack_propagate(False)
        
        table_title = tk.Label(table_header, text="📋 Data Table", 
                              font=('Arial', 12, 'bold'),
                              bg='#34495e', fg='white')
        table_title.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Scrollable frame for treeview
        tree_frame = tk.Frame(table_container, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Updated Treeview với 9 cột (thêm "Path Output")
        self.tree = ttk.Treeview(tree_frame, columns=(
            "Tên thiết bị", "Tên tk", "Ảnh acc", "Ảnh id", "Ảnh sản phẩm", "Caption", 
            "Path Folder", "Path File TXT", "Path Output"
        ), show="headings", style='Modern.Treeview')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Updated headers với 9 cột bao gồm "Path Output"
        headers = {
            "Tên thiết bị": "📱 Tên thiết bị",
            "Tên tk": "👤 Tên tk", 
            "Ảnh acc": "🖼️ Ảnh acc",
            "Ảnh id": "🆔 Ảnh id",
            "Ảnh sản phẩm": "📸Tên sản phẩm",
            "Caption": "📝 Caption",
            "Path Folder": "📁 Path Folder",
            "Path File TXT": "📄 Path File TXT",
            "Path Output": "🚀 Path Output"
        }
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=160, anchor="w")  # Giảm width xuống 160 để fit 9 cột
        
        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double click event
        self.tree.bind('<Double-1>', lambda e: self.edit_row())
    
    def create_status_bar(self):
        """Tạo thanh trạng thái"""
        self.status_bar = tk.Frame(self.root, bg='#34495e', height=30)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_bar, text="Ready", 
                                    bg='#34495e', fg='white',
                                    font=('Arial', 9))
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Row count
        self.row_count_label = tk.Label(self.status_bar, text="Rows: 0", 
                                       bg='#34495e', fg='#bdc3c7',
                                       font=('Arial', 9))
        self.row_count_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def update_status(self, message, count=None):
        """Cập nhật thanh trạng thái"""
        self.status_label.config(text=message)
        if count is not None:
            self.row_count_label.config(text=f"Rows: {count}")
        self.root.update_idletasks()
    
    def auto_save_to_db(self):
        """Tự động lưu vào database với 9 cột"""
        try:
            self.db.truncate()
            self.db.insert_multiple([{
                "ten_thiet_bi": row[0],
                "ten_tk": row[1],
                "anh_acc": row[2],
                "anh_id": row[3],
                "anh_san_pham": row[4],
                "caption": row[5],
                "path_folder": row[6],
                "path_file_txt": row[7],
                "path_output": row[8] if len(row) > 8 else ""
            } for row in self.data if any(row)])
            
            self.update_status("Auto-saved to database ✅", len(self.data))
        except Exception as e:
            self.update_status("Auto-save failed ❌")
            messagebox.showerror("❌ Error", f"Failed to auto-save data:\n{str(e)}")
    
    # ================== PROCESS CONTROL ==================
    def run_process(self):
        """Chạy upload.py"""
        if not hasattr(self, 'process') or self.process.poll() is not None:
            self.process = subprocess.Popen(["python", "upload.py"])
            self.update_status("Upload started! ▶️")
            messagebox.showinfo("✅ Success", "Upload process started successfully!")
        else:
            messagebox.showwarning("⚠️ Warning", "Upload process is already running!")

    def stop_process(self):
        """Dừng upload.py"""
        if hasattr(self, 'process') and self.process.poll() is None:
            self.process.terminate()
            self.update_status("Process stopped ⏹️")
            messagebox.showinfo("ℹ️ Info", "Process stopped successfully!")
        else:
            messagebox.showwarning("⚠️ Warning", "No process is currently running!")

    def toggle_upload(self):
        """Khi tick/untick checkbox Upload"""
        if self.upload_var.get():
            self.run_process()
        else:
            self.stop_process()

    # ================== CSV & DB ==================
    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        self.update_status("Importing CSV...")
        
        self.data = []
        self.tree.delete(*self.tree.get_children())
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)  # bỏ header nếu có
                
                prev_device = None
                row_count = 0
                for row in reader:
                    # Kiểm tra tối thiểu 9 cột
                    if len(row) < 9:
                        # Thêm cột trống nếu thiếu
                        while len(row) < 9:
                            row.append("")
                    
                    device = row[0].strip()
                    if device == '' and prev_device:
                        row[0] = prev_device
                    else:
                        if prev_device and prev_device != device:
                            self.tree.insert("", "end", values=("", "", "", "", "", "", "", "", ""))
                            self.data.append(["", "", "", "", "", "", "", "", ""])
                        prev_device = device
                    self.data.append(row[:9])  # Chỉ lấy 9 cột đầu tiên
                    self.tree.insert("", "end", values=tuple(row[:9]))
                    row_count += 1
            
            self.update_status("CSV imported successfully! ✅", row_count)
            messagebox.showinfo("✅ Success", f"CSV imported successfully!\nLoaded {row_count} rows.")
            self.auto_save_to_db()  # Tự động lưu sau khi import
        except Exception as e:
            self.update_status("Import failed ❌")
            messagebox.showerror("❌ Error", f"Failed to import CSV:\n{str(e)}")
    
    def add_row(self):
        self.edit_window(None, is_add=True)
    
    def edit_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Warning", "Please select a row to edit!")
            return
        item = self.tree.item(selected[0])
        values = item['values']
        self.edit_window(values, is_add=False, selected=selected[0])
    
    def delete_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Warning", "Please select a row to delete!")
            return
        
        if messagebox.askyesno("🗑️ Confirm Delete", "Are you sure you want to delete this row?"):
            index = self.tree.index(selected[0])
            del self.data[index]
            self.tree.delete(selected[0])
            self.update_status("Row deleted ✅", len(self.data))
            self.auto_save_to_db()  # Tự động lưu sau khi xóa
            messagebox.showinfo("✅ Success", "Row deleted and auto-saved successfully!")
    
    def edit_window(self, values, is_add=False, selected=None):
        edit_win = tk.Toplevel(self.root)
        edit_win.title("✏️ Edit Row" if not is_add else "➕ Add New Row")
        edit_win.geometry("800x950")  # Tăng height lên 950px để chứa field mới
        edit_win.configure(bg='#ecf0f1')
        edit_win.resizable(False, False)
        
        # Center the window
        edit_win.transient(self.root)
        edit_win.grab_set()
        
        # Header
        header_frame = tk.Frame(edit_win, bg='#34495e', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame, 
                               text="✏️ Edit Row Details" if not is_add else "➕ Add New Row",
                               font=('Arial', 16, 'bold'),
                               bg='#34495e', fg='white')
        header_label.pack(expand=True)
        
        # Form container
        form_frame = tk.Frame(edit_win, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Updated labels với 9 trường bao gồm Path Output
        labels = ["📱 Tên thiết bị", "👤 Tên tk", "🖼️ Ảnh acc", "🆔 Ảnh id", 
                 "📸 Ảnh sản phẩm", "📝 Caption", "📁 Path Folder", "📄 Path File TXT", "🚀 Path Output"]
        entries = []

        def get_connected_devices():
            try:
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')[1:]  # Bỏ dòng đầu tiên
                devices = [line.split()[0] for line in lines if 'device' in line]
                return devices
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to get connected devices:\n{str(e)}")
                return ["(Error)"]
            
        for i, label in enumerate(labels):
            # Label
            label_frame = tk.Frame(form_frame, bg='white')
            label_frame.pack(fill=tk.X, pady=(10, 5))
            
            tk.Label(label_frame, text=label, 
                    font=('Arial', 10, 'bold'),
                    bg='white', fg='#2c3e50').pack(anchor='w')
            
            if i == 0:  # Tên thiết bị
                devices = get_connected_devices()
                entry = ttk.Combobox(form_frame, values=devices, font=('Arial', 11))
                entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
                if values and i < len(values):
                    entry.set(values[i])
            else:
                entry = tk.Entry(form_frame, font=('Arial', 11), 
                               relief='solid', bd=1, bg='#f8f9fa')
                entry.pack(fill=tk.X, ipady=8, pady=(0, 5))
                if values and i < len(values):
                    entry.insert(0, values[i])
            entries.append(entry)        

        # Button frame
        button_frame = tk.Frame(form_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=20)
        
        def save_edit():
            new_values = [entry.get() for entry in entries]
            # Đảm bảo có đủ 9 cột
            while len(new_values) < 9:
                new_values.append("")
            
            if is_add:
                if self.data and self.data[-1][0] != new_values[0]:
                    self.tree.insert("", "end", values=("", "", "", "", "", "", "", "", ""))
                    self.data.append(["", "", "", "", "", "", "", "", ""])
                self.tree.insert("", "end", values=tuple(new_values))
                self.data.append(new_values)
                self.update_status("Row added ✅", len(self.data))
                self.auto_save_to_db()  # Tự động lưu sau khi thêm
                messagebox.showinfo("✅ Success", "Row added and auto-saved successfully!")
            else:
                index = self.tree.index(selected)
                self.data[index] = new_values
                self.tree.item(selected, values=tuple(new_values))
                self.update_status("Row updated ✅", len(self.data))
                self.auto_save_to_db()  # Tự động lưu sau khi chỉnh sửa
                messagebox.showinfo("✅ Success", "Row updated and auto-saved successfully!")
            edit_win.destroy()
        
        def cancel_edit():
            edit_win.destroy()
        
        # Buttons
        save_btn = tk.Button(button_frame, text="💾 Save", command=save_edit,
                            bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                            relief='flat', padx=20, pady=10, cursor='hand2')
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", command=cancel_edit,
                              bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'),
                              relief='flat', padx=20, pady=10, cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def save_to_db(self):
        """Manual save function (kept for compatibility)"""
        self.auto_save_to_db()
        messagebox.showinfo("✅ Success", "Data saved to accounts.json successfully!")
    
    def load_from_db(self):
        try:
            self.update_status("Loading from database...")
            self.tree.delete(*self.tree.get_children())
            self.data = []
            
            records = self.db.all()
            for row in records:
                # Updated để xử lý schema mới với 9 cột
                values = (
                    row.get("ten_thiet_bi", ""),
                    row.get("ten_tk", ""),
                    row.get("anh_acc", ""),
                    row.get("anh_id", ""),
                    row.get("anh_san_pham", ""),
                    row.get("caption", ""),
                    row.get("path_folder", ""),
                    row.get("path_file_txt", ""),
                    row.get("path_output", "")
                )
                self.tree.insert("", "end", values=values)
                self.data.append(list(values))
            
            self.update_status("Data loaded successfully! ✅", len(self.data))
        except Exception as e:
            self.update_status("Load failed ❌")
            messagebox.showerror("❌ Error", f"Failed to load data:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVGUI(root)
    root.mainloop()