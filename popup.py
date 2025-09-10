import tkinter as tk
from tkinter import messagebox
import sys

if len(sys.argv) > 1:
    tarea = sys.argv[1]
else:
    tarea = "Tarea sin nombre"

root = tk.Tk()
root.withdraw()
messagebox.showinfo("Orbis - Confirmación",
                    f"Tarea pendiente:\n\n{tarea}\n\nPresiona Aceptar para confirmar.")
root.destroy()
