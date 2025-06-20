import subprocess
import time


def main():
    server_process = subprocess.Popen(['python', 'server/servidor.py'])
    print("Servidor iniciado...")
    time.sleep(1)
    client_process = subprocess.Popen(['py', '-2.7', 'client/cliente.py'])

    try:
        server_process.wait()
        client_process.wait()
    except KeyboardInterrupt:
        print("Interrumpido. Deteniendo procesos...")
        server_process.terminate()
        client_process.terminate()

if __name__ == "__main__":
    main()