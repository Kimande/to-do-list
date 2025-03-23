import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

class ModernTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern To-Do List")
        self.root.geometry("800x600")
        self.root.configure(bg="#F5F5F5")
        
        # Database connection setup
        self.db_connection = None
        try:
            self.db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="modern_to_do_list",
                port=3307
            )
            self.cursor = self.db_connection.cursor()
            self.create_table()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
            self.root.destroy()
            return

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.create_widgets()
        self.load_tasks()

    def configure_styles(self):
        """Configure custom styles for widgets"""
        self.style.configure("TButton", padding=6, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", 
                            font=("Segoe UI", 18, "bold"), 
                            background="#6C5CE7", 
                            foreground="white")
        self.style.configure("Progress.TLabel", 
                            font=("Segoe UI", 12), 
                            background="#F5F5F5")
        self.style.configure("Treeview", 
                            font=("Segoe UI", 11), 
                            rowheight=25)
        self.style.configure("Treeview.Heading", 
                            font=("Segoe UI", 11, "bold"))
        self.style.map("Treeview", 
                      background=[("selected", "#A8A5E6")])

    def create_table(self):
        """Create tasks table if not exists"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                priority VARCHAR(50),
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_connection.commit()

    def create_widgets(self):
        """Create and arrange UI components"""
        # Header
        header_frame = ttk.Frame(self.root, style="Header.TLabel")
        header_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(header_frame, 
                 text="Task Manager", 
                 style="Header.TLabel").pack(side=tk.LEFT, padx=20)

        # Input Section
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10, padx=20, fill=tk.X)

        self.task_entry = ttk.Entry(input_frame, font=("Segoe UI", 12), width=40)
        self.task_entry.pack(side=tk.LEFT, padx=5)

        self.category_combobox = ttk.Combobox(input_frame, 
                                             values=["Work", "Personal", "Shopping", "Other"], 
                                             width=15)
        self.category_combobox.pack(side=tk.LEFT, padx=5)
        self.category_combobox.set("Category")

        self.priority_combobox = ttk.Combobox(input_frame, 
                                             values=["Low", "Medium", "High"], 
                                             width=12)
        self.priority_combobox.pack(side=tk.LEFT, padx=5)
        self.priority_combobox.set("Priority")

        ttk.Button(input_frame, 
                  text="➕ Add", 
                  command=self.add_task, 
                  style="TButton").pack(side=tk.LEFT, padx=5)

        # Task List Treeview
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.task_tree = ttk.Treeview(tree_frame, 
                                     columns=("id", "task", "category", "priority", "completed"), 
                                     show="headings")
        self.task_tree.heading("task", text="Task")
        self.task_tree.heading("category", text="Category")
        self.task_tree.heading("priority", text="Priority")
        self.task_tree.heading("completed", text="Status")
        self.task_tree.column("id", width=0, stretch=tk.NO)  # Hide ID column
        self.task_tree.column("task", width=300)
        self.task_tree.column("category", width=120)
        self.task_tree.column("priority", width=100)
        self.task_tree.column("completed", width=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.pack(fill=tk.BOTH, expand=True)

        # Action Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, 
                  text="✔ Mark Complete", 
                  command=self.mark_completed,
                  style="TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, 
                  text="🗑️ Delete Task", 
                  command=self.delete_task,
                  style="TButton").pack(side=tk.LEFT, padx=5)

        # Progress Section
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(pady=10)

        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           orient=tk.HORIZONTAL, 
                                           length=200, 
                                           mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=5)

        self.progress_label = ttk.Label(progress_frame, 
                                      text="Progress: 0%", 
                                      style="Progress.TLabel")
        self.progress_label.pack(side=tk.LEFT)

    def load_tasks(self):
        """Load tasks from database into Treeview"""
        self.task_tree.delete(*self.task_tree.get_children())
        try:
            self.cursor.execute("SELECT id, task, category, priority, completed FROM tasks")
            tasks = self.cursor.fetchall()

            for task in tasks:
                task_id, text, category, priority, completed = task
                status = "✔ Done" if completed else "❌ Pending"
                self.task_tree.insert("", tk.END, 
                                    values=(task_id, text, category, priority, status), 
                                    tags=("completed" if completed else "pending"))
            
            self.task_tree.tag_configure("completed", foreground="#808080")
            self.update_progress()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to load tasks: {str(e)}")

    def add_task(self):
        """Add new task to database"""
        task = self.task_entry.get().strip()
        category = self.category_combobox.get()
        priority = self.priority_combobox.get()

        if not task:
            messagebox.showwarning("Input Error", "Please enter a task description")
            return
        if category == "Category":
            category = None
        if priority == "Priority":
            priority = None

        try:
            self.cursor.execute(
                "INSERT INTO tasks (task, category, priority) VALUES (%s, %s, %s)",
                (task, category, priority)
            )
            self.db_connection.commit()
            self.task_entry.delete(0, tk.END)
            self.load_tasks()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to add task: {str(e)}")

    def delete_task(self):
        """Delete selected task from database"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a task to delete")
            return

        task_id = self.task_tree.item(selected[0], "values")[0]
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            self.db_connection.commit()
            self.load_tasks()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to delete task: {str(e)}")

    def mark_completed(self):
        """Toggle task completion status"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a task")
            return

        task_id = self.task_tree.item(selected[0], "values")[0]
        current_status = self.task_tree.item(selected[0], "values")[4]
        new_status = not ("✔" in current_status)

        try:
            self.cursor.execute(
                "UPDATE tasks SET completed = %s WHERE id = %s",
                (new_status, task_id)
            )
            self.db_connection.commit()
            self.load_tasks()
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to update task: {str(e)}")

    def update_progress(self):
        """Update progress bar and label"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM tasks")
            total = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = TRUE")
            completed = self.cursor.fetchone()[0]

            progress = (completed / total) * 100 if total > 0 else 0
            self.progress_bar["value"] = progress
            self.progress_label.config(text=f"Progress: {progress:.1f}%")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to update progress: {str(e)}")

    def __del__(self):
        """Clean up database connection"""
        if self.db_connection and self.db_connection.is_connected():
            self.cursor.close()
            self.db_connection.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernTodoApp(root)
    root.mainloop()