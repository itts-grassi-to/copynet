import gi
import os
import csv
import time
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
        self.__semaLettoriScrittori = Semaphore(1)
        self.__semaAntiRimbalzo = Semaphore(0)
        self.__caricaHosts()
    def __creaRigaHost(self, l, first):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add(hbox)
        if first:
            label = Gtk.Label(xalign=0, width_chars=10)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[0] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0, width_chars=30)
            label.set_markup("<span bgcolor='gray' color='white'>  " + l[1] + "  </span>")
            hbox.pack_start(label, True, True, 0)
            label = Gtk.Label(label="", xalign=0, width_chars=10)
            label.set_markup("<span bgcolor='gray' color='white'>  PERC  </span>")
            hbox.pack_start(label, True, True, 0)
            label = Gtk.Label(label="", xalign=0, width_chars=1)
            label.set_markup("<span bgcolor='gray' color='white'>  ACT  </span>")
            hbox.pack_start(label, True, True, 0)
        else:
            label = Gtk.Label(label=l[0], xalign=0, width_chars=10)
            hbox.pack_start(label, True, True, 0)
            label = Gtk.Label(label=l[1], xalign=0, width_chars=30)
            hbox.pack_start(label, True, True, 0)
            label = Gtk.Label(label="0%", xalign=0, width_chars=10)
            hbox.pack_start(label, True, True, 0)
            check = Gtk.CheckButton()
            check.set_active(True)
            hbox.pack_start(check, False, True, 0)
        return row
    def __caricaHosts(self):
        with open(FILE_CONF, "r") as f:
            lettore = csv.reader(f, delimiter=";")
            row = next(lettore)
            lstHosts.set_selection_mode(Gtk.SelectionMode.NONE)
            lstHosts.add(self.__creaRigaHost(row,True))
            for row in lettore:
                lstHosts.add(self.__creaRigaHost(row, False))
                # print(row)
    def __thPerc(self):
        self.__semaLettoriScrittori.acquire()
        print("thPerc avviato")
        self.__semaLettoriScrittori.release()
        while not self.__stopThread:
            lstHosts.show_all()
            time.sleep(2)
        print("thPerc fermato")
    def __thCopia(self, row, sema):
        self.__semaLettoriScrittori.acquire()
        print("thCopia avviato")
        self.__semaLettoriScrittori.release()
        # row.get_child().get_children()[0]     # nome PC
        # row.get_child().get_children()[1]     # indirizzo IP
        # row.get_child().get_children()[3]     attivato
        iperc = 0
        while not self.__stopThread:
            row.get_child().get_children()[2].set_label(str(iperc)+"%")       # percentuale
            iperc = iperc + 1
            time.sleep(1)
            if iperc >= 20:
                break
        sema.release()
        print("thCopia fermato")

    def __thFerma(self, sema):
        for s in sema:
            s.acquire()
        print("stop thread")
        self.__stopThread = True
        self.__semaAntiRimbalzo.acquire(False)
    def on_btHelp_clicked(self, win):
        dialog = Dlg(win, "Il software è costruito\nda Ortu prof. Daniele\nemail: daniele.ortu@itisgrassi.edu.it")
        dialog.run()
        dialog.destroy()
    def on_avvia(self):
        #print("avvia")
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
            sema.append( Semaphore(0) )
            # sema[len(sema) - 1].acquire()
            threading.Thread(target=self.__thCopia, args=(row, sema[len(sema)-1] )).start()
            i = i+1
            row = lstHosts.get_row_at_index(i)
            # print(i)
        threading.Thread(target=self.__thFerma, args=(sema, )).start()
    def on_stop(self):
        self.__stopThread = True


# *********** MAIN
builMain = Gtk.Builder()
builMain.add_from_file(GLADE)
lstHosts = builMain.get_object('listHosts')
winMain = builMain.get_object('mainCopynet')
winMain.set_icon_from_file(ICON)
winMain.connect("destroy", Gtk.main_quit)
builMain.connect_signals(EventiMain(winMain))
winMain.show_all()
Gtk.main()