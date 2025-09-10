import json
import time
import winsound
import schedule
import threading
import subprocess, sys
from pystray import Icon, Menu, MenuItem
from PIL import Image
from win10toast import ToastNotifier
import tkinter as tk
from tkinter import messagebox

toaster = ToastNotifier()

def lanzar_alarma(tarea):
    print(f"⏰ Recordatorio: {tarea}")
    toaster.show_toast("Orbis - Recordatorio", tarea, duration=10, threaded=True)
    winsound.Beep(1000, 800)
    subprocess.Popen([sys.executable, "popup.py", tarea])

def cargar_agenda():
    with open("agenda.json", "r", encoding="utf-8") as f:
        return json.load(f)

def programar_agenda(agenda):
    schedule.clear()
    for hora, tarea in agenda.items():
        schedule.every().day.at(hora).do(lanzar_alarma, tarea=tarea)
        print(f"✅ Programado {tarea} a las {hora}")

def ciclo_principal():
    while True:
        schedule.run_pending()
        time.sleep(30)



def ver_agenda(icon, item):
    agenda = cargar_agenda()
    tareas = "\n".join([f"{h} → {t}" for h, t in agenda.items()])

    def mostrar():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Agenda de hoy", tareas)
        root.destroy()

    threading.Thread(target=mostrar).start()

def actualizar_agenda(icon, item):
    agenda = cargar_agenda()
    programar_agenda(agenda)

    def mostrar():
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Orbis", "Agenda actualizada correctamente")
        root.destroy()

    threading.Thread(target=mostrar).start()


def salir(icon, item):
    icon.stop()

def editar_agenda(icon, item):
    agenda = cargar_agenda()

    def mostrar_editor():
        root = tk.Tk()
        root.title("Editar agenda")

        # Campos editables: hora + tarea
        entradas_hora = {}
        entradas_tarea = {}

        fila = 0
        for hora, tarea in agenda.items():
            # Hora
            entrada_hora = tk.Entry(root, width=10)
            entrada_hora.insert(0, hora)
            entrada_hora.grid(row=fila, column=0, padx=5, pady=5)
            entradas_hora[fila] = entrada_hora

            # Tarea
            entrada_tarea = tk.Entry(root, width=50)
            entrada_tarea.insert(0, tarea)
            entrada_tarea.grid(row=fila, column=1, padx=5, pady=5)
            entradas_tarea[fila] = entrada_tarea

            fila += 1

        def guardar():
            nueva_agenda = {}
            for i in entradas_hora:
                nueva_hora = entradas_hora[i].get().strip()
                nueva_tarea = entradas_tarea[i].get().strip()
                if nueva_hora and nueva_tarea:
                    nueva_agenda[nueva_hora] = nueva_tarea

            with open("agenda.json", "w", encoding="utf-8") as f:
                json.dump(nueva_agenda, f, ensure_ascii=False, indent=4)

            programar_agenda(nueva_agenda)
            messagebox.showinfo("Orbis", "Agenda actualizada correctamente")
            root.destroy()

        tk.Button(root, text="Guardar", command=guardar).grid(row=fila, column=0, columnspan=2, pady=10)

        root.mainloop()

    threading.Thread(target=mostrar_editor).start()

def main():
    agenda = cargar_agenda()
    programar_agenda(agenda)

    hilo = threading.Thread(target=ciclo_principal, daemon=True)
    hilo.start()

    image = Image.open("orbis.png")
    menu = Menu(
        MenuItem("Ver agenda", ver_agenda),
        MenuItem("Actualizar agenda", actualizar_agenda),
        MenuItem("Editar agenda", editar_agenda),   # 👈 nuevo
        MenuItem("Salir", salir)
    )
    icon = Icon("Orbis", image, menu=menu)
    icon.run()

if __name__ == "__main__":
    main()
