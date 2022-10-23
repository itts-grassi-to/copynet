import globale
import socket
import threading

class Server:
    def __init__(self):
        self.HOST = "localhost"
        self.__alt = False
        # self.d = destinatario

    def __th_srv(self, conn, addr):
        with conn:
            print('Connected by', addr)
            conn.sendall(globale.PAR)
            # attendo dove memorizzare il file
            path_dest = conn.recv(globale.MTU)
            conn.sendall(globale.ACK)

            with open(path_dest, 'wb') as fwb:
                print("inizio")
                while True:
                    conn.sendall(globale.PAR)
                    data = conn.recv(globale.MTU)
                    if data == globale.END:
                        break
                    fwb.write(data)
                    print(".", end=" ")
            print("fine")

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, globale.PORTA))
            s.listen(10)
            while not self.__alt:
                print("attendo comessione")
                conn, addr = s.accept()
                threading.Thread(target=self.__th_srv(), args=(conn, addr,)).start()
s = Server()
s.run()