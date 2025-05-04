import tkinter as tk
from tkinter import ttk, messagebox

class TestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Test GUI")
        
        # Notebook oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Test sekmesi
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text="Test")
        
        # Test butonu
        ttk.Button(self.test_frame, text="Test Butonu").pack(pady=20)

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Test Login")
        self.geometry("300x200")
        
        ttk.Button(self, text="Giriş Yap", command=self.show_main).pack(pady=20)
        
    def show_main(self):
        self.withdraw()
        try:
            root = tk.Tk()
            app = TestGUI(root)
            root.protocol("WM_DELETE_WINDOW", lambda: self.on_close(root))
            root.mainloop()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            self.destroy()
            
    def on_close(self, root):
        root.destroy()
        self.destroy()

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop() 