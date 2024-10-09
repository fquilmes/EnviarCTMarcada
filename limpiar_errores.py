import os
import ftplib
import tkinter as tk
from tkinter import messagebox

# Parámetros de FTP y directorios
FTP_PINNACLE_TOMO = '10.130.0.249'
FTP_USERNAME_TOMO = 'p3rtp'
FTP_PASSWORD_TOMO = 'p3rtp'
DIR_TOMOS_MARCADAS = '//files/network/DICOM/'
LOCAL_DIR = './'

# Función para eliminar todos los archivos en DIR_TOMOS_MARCADAS en el servidor FTP
def eliminar_archivos_ftp():
    """
    Elimina todos los archivos en el directorio DIR_TOMOS_MARCADAS del servidor FTP.

    Conecta al servidor FTP, se loguea y se cambia al directorio remoto.
    Luego lista todos los archivos en ese directorio y los elimina uno a uno.
    Si ocurre un error, se muestra un mensaje de error con la descripción del error.
    Si se eliminan todos los archivos con éxito, se muestra un mensaje de éxito.
    """
    try:
        with ftplib.FTP() as ftp:
            ftp.connect(FTP_PINNACLE_TOMO)
            ftp.login(FTP_USERNAME_TOMO, FTP_PASSWORD_TOMO)
            ftp.cwd(DIR_TOMOS_MARCADAS)
            filenames = ftp.nlst()  # Listar archivos en el directorio
            for filename in filenames:
                ftp.delete(filename)  # Eliminar cada archivo
            # Mostrar mensaje de éxito
            messagebox.showinfo("FTP", "Errores eliminados de PINNACLE.")
    except ftplib.all_errors as e:
        # Mostrar mensaje de error
        messagebox.showerror("Error FTP", f"Error al eliminar archivos en FTP: {e}")

# Función para eliminar todos los archivos .img en LOCAL_DIR
def eliminar_archivos_locales():
    """
    Elimina todos los archivos .img en LOCAL_DIR.

    Busca todos los archivos con extensión .img en el directorio LOCAL_DIR y los elimina uno a uno.
    Si ocurre un error, se muestra un mensaje de error con la descripción del error.
    Si se eliminan todos los archivos con éxito, se muestra un mensaje de éxito.
    """
    try:
        img_files = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.img')]
        for img_file in img_files:
            file_path = os.path.join(LOCAL_DIR, img_file)
            os.remove(file_path)  # Eliminar archivo local
        # Mostrar mensaje de éxito
        messagebox.showinfo("Local", "Errores eliminados de windows.")
    except Exception as e:
        # Mostrar mensaje de error
        messagebox.showerror("Error Local", f"Error al eliminar archivos locales: {e}")

# Llamada a las funciones con interfaz gráfica
def main():
    # Crear la ventana principal de tkinter
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal (no necesitamos una ventana completa)

    eliminar_archivos_ftp()      # Eliminar archivos en el servidor FTP
    eliminar_archivos_locales()  # Eliminar archivos .img en el directorio local

if __name__ == '__main__':
    main()
