import globale
import gi
import os
import csv
import time
import socket
import threading
from threading import *


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CURRDIR = os.path.dirname(os.path.abspath(__file__))
GLADE = os.path.join(CURRDIR, 'mainCopynet.glade')
FILE_CONF = os.path.join(CURRDIR, 'copynet.csv')
ICON = os.path.join(CURRDIR, 'img/icoCopynet.png')


class EventiMain:
    def __init__(self, win):
        self.__cpn = CPN()
        self.__win = win
    def on_btHelp_clicked(self, button):
        self.__cpn.on_btHelp_clicked(self.__win)
    def on_btAvvia_clicked(self, bt):
        self.__cpn.on_avvia()
    def on_btStop_clicked(self, bt):
        self.__cpn.on_stop()
    def on_btExit_clicked(self,bt):
        self.__cpn.on_exit()
class Dlg(Gtk.Dialog):
    def __init__(self, parent, testo) :
        super().__init__(title="Informazioni", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 100)
        label = Gtk.Label(label=testo)
        box = self.get_content_area()
        box.add(label)
        self.show_all()


class CPN():
    def __init__(self):
        self.__nomeCampi = self.__enum(NOME=0, UTENTE=1, INDIRIZZO=2, PATH=3, PERC=4, ACT=5)
        self.__semaLettoriScrittori = Semaphore(1)
        self.__semaAntiRimbalzo = Semaphore(0)
        self.__caricaHosts()
        self.__cancellaLog()
    def __enum(self, **enums):
        return type('Enum', (), enums)
    def __stampaLog(self,s):
        self.__semaLettoriScrittori.acquire()
        lblLog.set_label(s + "\n" + lblLog.get_label())
        self.__semaLettoriScrittori.release()
    def __cancellaLog(self):
        # print("cancellaLista",)
        lblLog.set_label("")
    def __creaRigaHost(self, l, first):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add(hbox)
        if first:
            # NOME
            label = Gtk.Label(xalign=0, width_chars=10)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[self.__nomeCampi.NOME] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            # UTENTE
            label = Gtk.Label(xalign=0, width_chars=20)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[self.__nomeCampi.UTENTE] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            # INDIRIZZO
            label = Gtk.Label(xalign=0, width_chars=20)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[self.__nomeCampi.INDIRIZZO] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            # PATH
            label = Gtk.Label(xalign=0, width_chars=50)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[self.__nomeCampi.PATH] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            # PERCENUALE
            label = Gtk.Label(label="", xalign=0, width_chars=10)
            label.set_markup("<span bgcolor='gray' color='white'>  PERC  </span>")
            hbox.pack_start(label, True, True, 0)
            # ATTIVO
            label = Gtk.Label(label="", xalign=0, width_chars=1)
            label.set_markup("<span bgcolor='gray' color='white'>  ACT  </span>")
            hbox.pack_start(label, False, True, 0)
        else:
            # nome
            label = Gtk.Label(label=l[self.__nomeCampi.NOME], xalign=0, width_chars=10)
            hbox.pack_start(label, True, True, 0)
            # UTENTE
            label = Gtk.Label(label=l[self.__nomeCampi.UTENTE], xalign=0, width_chars=20)
            hbox.pack_start(label, True, True, 0)
            # INDIRIZZO
            label = Gtk.Label(label=l[self.__nomeCampi.INDIRIZZO], xalign=0, width_chars=20)
            hbox.pack_start(label, True, True, 0)
            # PATH
            label = Gtk.Label(label=l[self.__nomeCampi.PATH], xalign=0, width_chars=50)
            hbox.pack_start(label, True, True, 0)
            # PERCENUALE
            label = Gtk.Label(label="0%" , xalign=0, width_chars=10)
            hbox.pack_start(label, True, True, 0)
            # ATTIVO
            check = Gtk.CheckButton()
            check.set_active(True)
            hbox.pack_start(check, False, True, 0)
        return row
    def __caricaHosts(self):
        with open(FILE_CONF, "r") as f:
            lettore = csv.reader(f, delimiter=";")
            row = next(lettore)
            lstHosts.set_selection_mode(Gtk.SelectionMode.NONE)
            lstHosts.add(self.__creaRigaHost(row, True))
            for row in lettore:
                lstHosts.add(self.__creaRigaHost(row, False))
                # print(row)
        #lst.show_all()
    def __thPerc(self):
        self.__stampaLog("thPerc avviato")
        while not self.__stopThread:
            lstHosts.show_all()
            time.sleep(2)
        self.__stampaLog("thPerc fermato")
    def __thCopia(self, row, sema, nomeFileOrigine):
        nomePC =   row.get_child().get_children()[self.__nomeCampi.NOME].get_label()
        ipRemoto = row.get_child().get_children()[self.__nomeCampi.INDIRIZZO].get_label()
        nomeFileRemoto = nomeFileOrigine.split("/")
        nomeFileRemoto = nomeFileRemoto[len(nomeFileRemoto) - 1]
        nomeFileRemoto = row.get_child().get_children()[self.__nomeCampi.PATH].get_label() + \
                   "/" + nomeFileRemoto
        self.__stampaLog("thCopia avviato su " + nomePC + " " + ipRemoto)
        # row.get_child().get_children()[3]     attivato
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fwb:
            try:
                fwb.connect((ipRemoto, globale.PORTA))
            except socket.error as exc:
                self.__stampaLog("Errore di connessione a " + nomePC + ": " + str(exc))
                sema.release()
                return
            data = fwb.recv(globale.MTU)
            if data != globale.PAR:
                self.__stampaLog("client non pronto")
                return
            fwb.sendall(str.encode(nomeFileRemoto))
            data = fwb.recv(globale.MTU)
            if data != globale.ACK:
                self.__stampaLog(nomePC+": errore nell'invio nome file")
                return
            self.__stampaLog(nomePC + ": inviato nome file")
            with open(nomeFileOrigine, "rb") as f:
                car = f.read()
                start = 0
                dimensioneFile = residuo = len(car)
                iperc = 0
                while not self.__stopThread:
                    #data = fwb.recv(globale.MTU)
                    #if data != globale.PAR:
                    #    self.__stampaLog("client non pronto invio byte")
                    #    break
                    if residuo >= globale.MTU:
                        fine = start+ (globale.MTU)
                        print("INVIO: ", start, " ",  fine )
                        fwb.sendall(car[start:fine])
                        start = fine
                        data = fwb.recv(globale.MTU)
                        if data != globale.ACK:
                            self.__stampaLog(nomePC + ": errore nella ricezione ack dati")
                            break
                        residuo = residuo - globale.MTU
                    else:
                        fine = start + residuo -1
                        fwb.sendall(car[start:fine]+str.encode('\n'))
                        print("INVIO: ", start, " ",  fine )
                        #start = fine
                        data = fwb.recv(globale.MTU)
                        if data != globale.ACK:
                            self.__stampaLog(nomePC + ": errore nella ricezione ack dati")
                            break
                        residuo=0
                    if residuo == 0:
                        fwb.sendall(globale.END)
                        row.get_child().get_children()[self.__nomeCampi.PERC].set_label("100%")
                        self.__stopThread = True
                    iperc = int(((dimensioneFile - residuo)/dimensioneFile)*100)
                    row.get_child().get_children()[self.__nomeCampi.PERC].set_label(str(iperc)+"%")       # percentuale
                    time.sleep(1)
        sema.release()
        self.__stampaLog("file copiato con successo su " + nomePC)

    def __thFerma(self, sema):
        self.__stampaLog("thFerma avviato")
        for s in sema:
            s.acquire()
        self.__stampaLog("stop thread")
        self.__stopThread = True
        self.__semaAntiRimbalzo.acquire(False)
        self.__stampaLog("thFerma finito")
    def on_btHelp_clicked(self, win):
        dialog = Dlg(win, "Il software è costruito\nda Ortu prof. Daniele\nemail: daniele.ortu@itisgrassi.edu.it")
        dialog.run()
        dialog.destroy()
    def on_avvia(self):
        #print("avvia")
        nomeFile = btScegliFile.get_filename()
        if nomeFile == None:
            dialog = Gtk.MessageDialog(
                transient_for=None,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.CLOSE,
                text="Seleziona il file da copiare",
            )
            dialog.run()
            dialog.destroy()
            return
        self.__cancellaLog()
        if self.__semaAntiRimbalzo.acquire(False):
            self.__semaAntiRimbalzo.release()
            return
        print("***********")
        self.__semaAntiRimbalzo.release()
        self.__stopThread = False
        i = 1
        row = lstHosts.get_row_at_index(i)
        if row != None:
            threading.Thread(target=self.__thPerc, args=()).start()
        sema = []
        while row != None:
            if row.get_child().get_children()[5].get_active():
                sema.append(Semaphore(0))
                s = sema[len(sema) - 1]
                threading.Thread(target=self.__thCopia, args=(row, s, nomeFile)).start()
            i = i+1
            row = lstHosts.get_row_at_index(i)
            # print(i)
        threading.Thread(target=self.__thFerma, args=(sema, )).start()
    def on_stop(self):
        self.__stopThread = True
    def on_exit(self):
        print("cliccato uscita")
        #row = lstLog.get_row_at_index(0)
        #lbl = row.get_child().get_children()[0]
        #lblLog.set_label(lblLog.get_label()+"\nciao")

# *********** MAIN
builMain = Gtk.Builder()
builMain.add_from_file(GLADE)
lstHosts = builMain.get_object('listHosts')
btScegliFile = builMain.get_object('btScegliFile')
#lstLog = builMain.get_object('lstLog')
#lblLog = builMain.get_object('hRow').get_children()[0]
lblLog = builMain.get_object("lblLog")
winMain = builMain.get_object('mainCopynet')
winMain.set_icon_from_file(ICON)
winMain.connect("destroy", Gtk.main_quit)
builMain.connect_signals(EventiMain(winMain))
winMain.show_all()
Gtk.main()