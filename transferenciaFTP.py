import os
import ftplib
import pydicom
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import re
from tqdm import tqdm
import signal

# Configuración
FTP_PINNACLE_TOMO = '10.130.0.249'
FTP_USERNAME_TOMO = 'p3rtp'
FTP_PASSWORD_TOMO = 'p3rtp'
DIR_TOMOS_MARCADAS = '//files/network/DICOM/'

FTP_PINNACLE_1 = '10.130.0.251'
FTP_USERNAME_1 = 'p3rtp'
FTP_PASSWORD_1 = 'p3rtp'
DIR_PACIENTES_1 = '/PrimaryPatientData/NewPatients/Institution_224/Mount_0/' #no se usa

FTP_PINNACLE_2 = '10.130.0.252'
FTP_USERNAME_2 = 'p3rtp'
FTP_PASSWORD_2 = 'p3rtp'
DIR_PACIENTES_2 = '/PrimaryPatientData/NewPatients/Institution_224/Mount_0/' #no se usa

LOCAL_DIR = './'
LOG_PASADOS = rf'\\10.130.1.253\FisicaQuilmes\00_Tomografo\98_Logs\_aRegistroGeneral\log_pacientes_enviados.txt'
ARCHIVO_CONTADOR = rf'\\10.130.1.253\FisicaQuilmes\00_Tomografo\98_Logs\_aRegistroGeneral\contador_NOBORRAR.txt'

TIMEOUT = 60  # Tiempo límite de 1 minutos por archivo
# Función para manejar el timeout
def handler(signum, frame):    
    raise TimeoutError

# Función para eliminar archivos en el servidor FTP
def eliminar_archivos_ftp(ftp, dir_path):
    ftp.cwd(dir_path)
    filenames = ftp.nlst()
    for filename in filenames:
        ftp.delete(filename)

# Función para eliminar archivos locales
def eliminar_archivos_locales():
    img_files = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.img')]
    for img in img_files:
        os.remove(os.path.join(LOCAL_DIR, img))
        
def ftp_transfer():
    # Crear la ventana principal de tkinter
    """
    Descarga los archivos de la carpeta DIR_TOMOS_MARCADAS y los almacena en la carpeta LOCAL_DIR.
    Muestra una ventana con una barra de progreso que indica el avance de la descarga.
    """
    
    root = tk.Tk()
    root.title("Descargando tomo")

    # Etiqueta de progreso
    progress_label = tk.Label(root, text="Descargando archivos...")
    progress_label.pack(pady=10)

    # Barra de progreso
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=10)

    # Configurar la barra de progreso
    with ftplib.FTP() as ftp:
        ftp.connect(FTP_PINNACLE_TOMO)
        ftp.login(FTP_USERNAME_TOMO, FTP_PASSWORD_TOMO)
        ftp.cwd(DIR_TOMOS_MARCADAS)
        filenames = ftp.nlst()
        img_files = [filename for filename in filenames if filename.endswith('.img')]
        progress['maximum'] = len(img_files)

        # Función para actualizar la barra de progreso
        def update_progress_tomo():
            for i, filename in enumerate(img_files):
                local_file = os.path.join(LOCAL_DIR, filename)
                with open(local_file, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                progress['value'] = i + 1
                root.update_idletasks()
            root.destroy()

        # Iniciar la descarga de archivos en un hilo separado para no bloquear la interfaz
        root.after(100, update_progress_tomo)
        root.mainloop()

def ftp_upload(server_ip, username, password, remote_dir):
    # Crear la ventana principal de tkinter
    """
    Crea una interfaz gráfica que muestra una barra de progreso para subir archivos
    .img desde LOCAL_DIR al servidor FTP en el directorio remoto especificado.

    La barra de progreso se actualizará con el progreso de la subida de archivos.
    Una vez que se termina de subir todos los archivos, se cierra la ventana de la
    interfaz.

    Parameters
    ----------
    server_ip : str
        La dirección IP del servidor FTP al que se quiere subir los archivos.
    username : str
        El nombre de usuario para loguearse en el servidor FTP.
    password : str
        La contraseña para loguearse en el servidor FTP.
    remote_dir : str
        El directorio remoto en el que se van a subir los archivos.
    """
    root = tk.Tk()
    root.title("Enviando archivos")

    # Etiqueta de progreso
    progress_label = tk.Label(root, text="Enviando archivos a Física...")
    progress_label.pack(pady=10)

    # Barra de progreso
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=10)

    # Contar archivos .img en LOCAL_DIR
    img_files = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.img')]

    # Configurar la barra de progreso
    progress['maximum'] = len(img_files)

    # Función para actualizar la barra de progreso
    def update_progress():
        """
        Actualiza la barra de progreso al subir archivos al servidor FTP.

        Se conecta al servidor FTP, se loguea, se cambia al directorio remoto
        especificado y luego se suben los archivos .img encontrados en LOCAL_DIR.
        La barra de progreso se actualiza con el progreso de la subida de archivos.
        Una vez que se termina de subir todos los archivos, se cierra la ventana de la
        interfaz.
        """
        with ftplib.FTP() as ftp:
            ftp.connect(server_ip)
            ftp.login(username, password)
            ftp.cwd(remote_dir)

            for i, filename in enumerate(img_files):
                local_file = os.path.join(LOCAL_DIR, filename)
                with open(local_file, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                progress['value'] = i + 1
                root.update_idletasks()

        root.destroy()

    # Iniciar la carga de archivos en un hilo separado para no bloquear la interfaz
    root.after(100, update_progress)
    root.mainloop()


def dcmdump(filepath, tag):
    """
    Reads a DICOM file at `filepath` and returns the value of the given `tag`.

    If the tag is not found in the file, returns an empty string.

    If an exception is raised while reading the file, prints the exception message
    and returns an empty string.

    Parameters
    ----------
    filepath : str
        path to the DICOM file to read
    tag : str
        the tag to read from the file

    Returns
    -------
    str
        the value of the given tag, or an empty string if not found
    """
    try:
        ds = pydicom.dcmread(filepath,force=True)
        return ds.data_element(tag).value if tag in ds else ''
    except Exception as e:
        print(f'Error reading DICOM file {filepath}: {e}')
        return ''

# Leer y procesar todos los archivos DICOM
def process_dicom_files():
    files_processed = []
    with open('transferred_files.txt', 'r') as f:
        for line in f:
            files_processed.append(line.strip())

    nombres_pacientes = set()
    hcs_pacientes = set()

    for file in files_processed:
        nombre_paciente = dcmdump(file, 'PatientName')
        hc_paciente = dcmdump(file, 'PatientID')
        nombres_pacientes.add(nombre_paciente)
        hcs_pacientes.add(hc_paciente)
    
    # Verificar si todos los nombres y HCs son consistentes
    if len(hcs_pacientes) > 1:
        # Crear una ventana emergente con el mensaje de error
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "No coincide el número de HC con Sitramed.\n\nDICOMs eliminados.")
        # Eliminar todos los archivos descargados
        for file in files_processed:
            os.remove(file)
        return False, None, None
    
    return True, nombres_pacientes.pop(), hcs_pacientes.pop()

def main():
    # Transferir archivos desde TOMO
    ftp_transfer()

    # Contar archivos .img
    img_files = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.img')]
    img_count = len(img_files)
    
    if img_count == 0:
        # Crear una ventana emergente con el mensaje de error
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", "No se encontraron archivos .img para enviar.")
        return

    # Crear archivo de registro de archivos .img
    with open('transferred_files.txt', 'w') as f:
        for img in img_files:
            f.write(f"{img}\n")
    
    # Procesar todos los archivos DICOM y verificar consistencia
    all_files_ok, nombre_paciente, hc_paciente = process_dicom_files()
    
    if not all_files_ok:
        # Eliminar archivos en el servidor TOMO
        with ftplib.FTP() as ftp:
            ftp.connect(FTP_PINNACLE_TOMO)
            ftp.login(FTP_USERNAME_TOMO, FTP_PASSWORD_TOMO)
            ftp.cwd(DIR_TOMOS_MARCADAS)
            for img in img_files:
                ftp.delete(img)
        # Crear una ventana emergente con el mensaje de error
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Información", "Exportar un único pte con el número de HC que corresponda.")
        return

    nombre_HC_pinnacle1 = f"{hc_paciente}___PINNACLE_1"
    nombre_HC_pinnacle2 = f"{hc_paciente}___PINNACLE_2"

    # Verificar si el paciente ya fue enviado
    with open(LOG_PASADOS, 'r') as f:
        log_pasados_content = f.read()

    if nombre_HC_pinnacle1 in log_pasados_content:
        print("La tomo ya se envio a Pinnacle1 por lo que se envia de nuevo al mismo lugar.")
        DEST_SERVER = 'PINNACLE_1'
        nombre_paciente = f"RR_{nombre_paciente}"
    elif nombre_HC_pinnacle2 in log_pasados_content:
        print("La tomo ya se envio a Pinnacle2 por lo que se envia de nuevo al mismo lugar.")
        DEST_SERVER = 'PINNACLE_2'
        nombre_paciente = f"RR_{nombre_paciente}"
    else:
        # Leer el valor del contador desde el archivo (si existe)
        if os.path.exists(ARCHIVO_CONTADOR):
            with open(ARCHIVO_CONTADOR, 'r') as f:
                contador = int(f.read().strip())
        else:
            contador = 0

        # Incrementar el contador
        contador = (contador % 2) + 1

        # Determinar qué servidor usar en esta ejecución
        if contador == 1:
            DEST_SERVER = 'PINNACLE_1'
        else:
            DEST_SERVER = 'PINNACLE_2'
        
        # Guardar el valor actual del contador en el archivo
        with open(ARCHIVO_CONTADOR, 'w') as f:
            f.write(str(contador))

    datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        nombre_paciente_ajustado = nombre_paciente.ljust(32, '_')
    except:
        nombre_paciente_ajustado = nombre_paciente._components[0].ljust(32, '_')


    # Actualizar el log de pacientes pasados
    with open(LOG_PASADOS, 'a') as f:
        f.write(f"{nombre_paciente_ajustado}___{hc_paciente}___{DEST_SERVER}___{datetime_str}\n")

    # Transferir archivos al DEST_SERVER
    if DEST_SERVER == 'PINNACLE_1':
        ftp_upload(FTP_PINNACLE_1, FTP_USERNAME_1, FTP_PASSWORD_1, DIR_TOMOS_MARCADAS)
    else:
        ftp_upload(FTP_PINNACLE_2, FTP_USERNAME_2, FTP_PASSWORD_2, DIR_TOMOS_MARCADAS)

    # Crear y actualizar el log individual del paciente
    log_filename = rf"\\10.130.1.253\FisicaQuilmes\00_Tomografo\98_Logs\{nombre_paciente}___{hc_paciente}___{DEST_SERVER}___{datetime_str}.txt"
    with open(log_filename, 'w') as f:
        for img in img_files:
            nombre_paciente = dcmdump(img, 'PatientName')
            hc_paciente = dcmdump(img, 'PatientID')
            f.write(f"{nombre_paciente} - {hc_paciente} - {img} - Destino: {DEST_SERVER} - Fecha y hora: {datetime_str}\n")
    
    # Eliminar archivos en el servidor TOMO
    with ftplib.FTP() as ftp:
        ftp.connect(FTP_PINNACLE_TOMO)
        ftp.login(FTP_USERNAME_TOMO, FTP_PASSWORD_TOMO)
        ftp.cwd(DIR_TOMOS_MARCADAS)
        for img in img_files:
            ftp.delete(img)

    for img in img_files:
        os.remove(os.path.join(LOCAL_DIR, img))
        
    # Crear una ventana emergente avisando que ya ta
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Listo!", "Paciente enviado correctamente!")

if __name__ == '__main__':
    main()
