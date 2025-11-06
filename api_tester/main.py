import tkinter as tk
from ui.main_window import ApiTesterApp
import threading
import sys, os,time
from PIL import Image, ImageTk

# -----------------------------
# SPLASH SCREEN FUNCTION (with Fade-Out)
# -----------------------------

def show_splash():
   
    def resource_path(relative_path):
        """Get absolute path to resource (for PyInstaller .exe and normal run)."""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.geometry("600x350+500+250")
    splash.configure(bg="#1E1E1E")

    try:
        splash_img_path = resource_path("assets/icons/splash.png")
        img = Image.open(splash_img_path)
        img = img.resize((600, 300), Image.LANCZOS)  # ✅ auto resize to fit window
        splash_img = ImageTk.PhotoImage(img)
        label_img = tk.Label(splash, image=splash_img, bg="#1E1E1E")
        label_img.image = splash_img
        label_img.pack(expand=True)
    except Exception:
        tk.Label(
            splash,
            text="Loading API Tester...",
            fg="white",
            bg="#1E1E1E",
            font=("Segoe UI", 18, "bold")
        ).pack(expand=True)

    # Subtext (keep your original style)
    tk.Label(
        splash,
        text="Initializing modules...",
        fg="#BBBBBB",
        bg="#1E1E1E",
        font=("Segoe UI", 10)
    ).pack(pady=10)

    splash.attributes("-alpha", 1.0)  # full opacity
    splash.update()

    # Show splash for 2.5 seconds before fading out
    time.sleep(2.5)

    # Fade out smoothly
    for i in range(20):
        splash.attributes("-alpha", 1.0 - (i / 20))
        time.sleep(0.05)
        splash.update()

    splash.destroy()

# -----------------------------
# MAIN ENTRY POINT
# -----------------------------
def main():
    # Run splash in separate thread
    splash_thread = threading.Thread(target=show_splash)
    splash_thread.start()
    splash_thread.join()

    # Launch main window
    app = ApiTesterApp()
    app.run()


if __name__ == "__main__":
    main()
