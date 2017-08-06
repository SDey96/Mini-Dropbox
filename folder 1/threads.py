import socket
import os
import subprocess
import threading
import hashlib
import time
import struct
from stat import *

class serverThread(threading.Thread):
    def __init__(self, threadId, threadName) :
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = threadName
        self.running = True

    def exit(self) :
        self.running = False

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def downl(self, args, conn) :
        if len(args) <= 2 :
            conn.send("woco")
            return
        if args[1] == "TCP" :
            if os.path.exists(args[2]) == False:
                conn.send("nofi")
                return

            c = os.stat(args[2])
            fileinfo = args[2] + " " + str(c.st_size) + " " + str(c.st_mtime) + " " + self.md5(args[2])
            fileinfo = bytes(fileinfo)    # Or other appropriate encoding
            data = struct.pack("I%ds" % (len(fileinfo),), len(fileinfo), fileinfo)
            conn.send(data)

            perm = oct(os.stat(args[2])[ST_MODE])[-4:]
            conn.send((str)(perm))
            time.sleep(0.1)

            f = open(''+args[2],'rb')
            l = f.read(1024)
            while (l):
                conn.send(l)
                l = f.read(1024)
            f.close()
        return

    def index(self, args, conn) :

        if len(args) > 1 and args[1] == "longlist":
            l = os.listdir('.')

            conn.send(str(len(l)))

            for fil in l :
                comm = "ls -lh " + fil
                pr = subprocess.Popen("ls -lh" + comm, stdout=subprocess.PIPE, shell=True)
                (ans, err) = pr.communicate()
                inf = ans.split()
                ty = ""
                if inf[0][0] == 'd' :
                    ty = "directory"
                else :
                    ty = "file"
                ret = inf[9] + "  " + inf[5] + "  " +inf[6] + " " + inf[7] + "  " + ty
                conn.send(ret)
            return


        elif len(args) > 1 and args[1] == "shortlist" :
            if len(args) < 4 :
                conn.send(str(1))
                for i in xrange(100000):
                    i += 1
                conn.send("Format of shortlist is index shortlist <starttimestamp> <endtimestamp>")
                return
            l = os.listdir('.')

            fileList = []
            for fil in l :
                d = os.stat(fil)
                if d.st_mtime >= float(args[2]) and d.st_mtime <= float(args[3]) :
                    fileList.append(fil)

            conn.send(str(len(fileList)))

            for i in xrange(100000):
                i += 1

            for fil in fileList :
                comm = "ls -lh " + fil
                pr = subprocess.Popen( comm, stdout=subprocess.PIPE, shell=True)
                (ans, err) = pr.communicate()
                inf = ans.split()
                ty = ""
                if inf[0][0] == 'd' :
                    ty = "directory"
                else :
                    ty = "file"
                ret = inf[8] + "  " + inf[4] + "  " +inf[5] + " " + inf[6] + "  " + ty
                # print ret
                conn.send(ret)
            return

        elif len(args) > 1 and args[1] == "regex" :
            if len(args) < 3 :
                conn.send(str(1))
                for i in xrange(100000):
                    i += 1
                conn.send("Format of regex is index regex \.txt$")
                return
            l = os.listdir('.')
            selFil = []
            for fil in l :
                pr = subprocess.Popen("ls -lh " + fil + " | grep " + '"' + args[2] + '"', stdout=subprocess.PIPE, shell=True)
                (ans, err) = pr.communicate()
                inf = ans.split()
                if len(inf) > 2:
                    selFil.append(fil)

            conn.send(str(len(selFil)))
            for i in xrange(100000) :
                i+=1

            for fil in selFil :
                pr = subprocess.Popen("ls -lh " + fil, stdout=subprocess.PIPE, shell=True)
                (ans, err) = pr.communicate()
                inf = ans.split()
                ty = ""
                if inf[0][0] == 'd' :
                    ty = "directory"
                else :
                    ty = "file"
                ret = inf[8] + "  " + inf[4] + "  " +inf[5] + " " + inf[6] + "  " + ty
                conn.send(ret)
            return
        conn.send("1")
        for i in xrange(100000):
            i+=1
        conn.send("use longlist/shortlist/regex with index")
        return

    def hashing(self, args, conn):
        if len(args) < 2 :
            conn.send("1")
            for i in xrange(100000):
                i+=1
            conn.send("Use verify/checkall with hash")
            return
        if args[1] == "verify" :
            conn.send("1")
            for i in xrange(100000):
                i+=1
            if len(args) < 3 :
                conn.send("Specify a file")
                return
            elif os.path.exists(args[2]) == False :
                conn.send("File not found")
                return
            else :
                conn.send( str(self.md5(args[2]) ) + " " + str( time.ctime(os.path.getmtime(args[2]) ) ) )
                return

        elif args[1] == "checkall" :
            li = os.listdir('.')
            conn.send( str(len(li) ) )
            for fil in li :
                conn.send( str(fil) + " " + str(self.md5(fil) ) + " " + str( time.ctime(os.path.getmtime(fil) ) ) )
            return

        else :
            conn.send ("Use verify/checkall with hash")
            return

    def run(self) :
        port = 60000
        s = socket.socket()
        host = ""
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(2)
        while self.running:
            conn, addr = s.accept()
            data = conn.recv(1000)
            args = data.split()

            if args[0] == "index":
                self.index(args, conn)
            elif args[0] == "hash":
                self.hashing(args, conn)
            elif args[0] == "download":
                self.downl(args, conn)
            elif args[0] == "exit" or args[0] == "quit" :
                self.exit()

            conn.close()

        s.close()

class clientThread(threading.Thread):
    def __init__(self, threadId, threadName) :
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = threadName
        self.running = True

    def exit(self) :
        self.running = False

    def index(self, s) :
        num = s.recv(1000)
        for i in xrange(int(num)) :
            data = s.recv(10000)
            print data
        return

    def downl(self, args, s):
        if len(args) <= 2 :
            s.recv(4)
            print "usage of download :  download <flag> [args]..."
            return
        if args[1]=="TCP":
            length = s.recv(4)
            length, = struct.unpack('I', length)
            if length == "nofil" :
                print "File does not exist"
                return
            if length == "woco" :
                print "usage of download :  download <flag> [args]..."
                return
            fileinfo = s.recv(length).decode()
            if fileinfo != "" :
                print fileinfo
            temp=fileinfo.split()
            if len(temp) == 0 :
                print "File does not exist"
                return
            if len(temp) <= 1 or temp[2] != "not":
                perm = s.recv(1024)
                with open('' + args[2], 'wb') as f:
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                    f.close()
                subprocess.call( ['chmod', (str)(perm), args[2]] )
            return
            if temp[2] == "not" :
                print "File does not exist"
        return

    def hashing(self, s) :
        num = s.recv(1000)
        for i in xrange(int(num)) :
            data = s.recv(10000)
            print data
        return

    def run(self) :
        while self.running :
            comm = raw_input("prompt> ")
            args = comm.split()
            if comm == "" or len(args) == 0:
                continue
            f = open("log.txt","a+")
            f.write(comm + "\n")
            f.close()
            s = socket.socket()
            host = ""
            port = 60001
            s.connect((host, port))
            s.send(comm)

            if args[0] == "index" :
                self.index(s)
            elif args[0] == "hash" :
                self.hashing(s)
            elif args[0] == "download" :
                self.downl(args, s)
            elif args[0] == "exit" or args[0] == "quit" :
                self.exit()
            else :
                print "command not found"
            s.close()



class serverThreadAuto(threading.Thread):
    def __init__(self, threadId, threadName) :
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = threadName
        self.running = True

    def exit(self) :
        self.running = False

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def downl(self, args, conn) :
        c = os.stat(args[1])
        fileinfo = args[1] + " " + str(c.st_size) + " " + str(c.st_mtime) + " " + self.md5(args[1])
        fileinfo = bytes(fileinfo)
        data = struct.pack("I%ds" % (len(fileinfo),), len(fileinfo), fileinfo)
        conn.send(data)
        time.sleep(0.1)

        perm = oct(os.stat(args[1])[ST_MODE])[-4 : ]
        conn.send((str)(perm))
        time.sleep(0.1)

        f = open(''+args[1],'rb')
        l = f.read(1024)
        while (l):
            conn.send(l)
            l = f.read(1024)
        f.close()
        return

    def index(self, conn) :
        l = os.listdir('.')
        conn.send(str(len(l)))
        time.sleep(0.1)
        for fil in l :
            for i in xrange(100000) :
                i+=1
            conn.send(fil)

    def hashing(self, args, conn):
        conn.send( str(self.md5(args[1]) ) + " " + str( os.stat(args[1]).st_mtime ) )
        time.sleep(0.1)
        return


    def run(self) :
        port = 60000
        s = socket.socket()
        host = ""
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(2)
        while True:
            conn, addr = s.accept()
            data = conn.recv(1000)
            args = data.split()

            if args[0] == "index":
                self.index(conn)
            elif args[0] == "hash":
                self.hashing(args, conn)
            elif args[0] == "download":
                self.downl(args, conn)

            conn.close()

        s.close()

class clientThreadAuto(threading.Thread):
    def __init__(self, threadId, threadName) :
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = threadName
        self.running = True

    def exit(self) :
        self.running = False

    def index(self, s) :
        num = s.recv(1000)
        l = os.listdir('.')
        retList = []
        for i in xrange(int(num)) :
            data = s.recv(10000)
            if data not in l :
                retList.append(data)
        return retList

    def downl(self, args, s):
        length = s.recv(4)
        length, = struct.unpack('I', length)
        fileinfo = s.recv(length).decode()
        print fileinfo
        temp = fileinfo.split()
        perm = s.recv(1024)
        with open('' + args[1], 'wb') as f:
            while True:
                data = s.recv(1024)
                if not data:
                    break
                f.write(data)
            f.close()
        subprocess.call(['chmod', (str)(perm), args[1]])
        return

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def hashing(self, args, s, port, host) :
        data = s.recv(10000)
        info = data.split()
        ha = self.md5(args[1])
        if str(ha) != info[0] :
            if int(os.stat(args[1]).st_mtime) < int(float(info[1])) :
                return True
        return False

    def run(self) :
        while self.running :
            time.sleep(10)
            host = ""
            port = 60001
            s = socket.socket()
            s.connect((host, port))

            comm = "index"
            print "running command " + comm
            s.send(comm)
            newFiles = self.index(s)
            s.close()
            for fil in newFiles :
                s = socket.socket()
                s.connect((host, port))
                comm = "download " + str(fil)
                args = comm.split()
                print "running command " + comm
                s.send(comm)
                self.downl(args, s)
                s.close()

            l = os.listdir('.')
            lis = []
            for fil in l :
                comm = "hash " + str(fil)
                args = comm.split()
                print "running command " + comm
                s = socket.socket()
                s.connect((host, port))
                s.send(comm)
                if self.hashing(args, s, port, host): 
                    lis.append(args[1])
                s.close()

            for fil in lis :
                s = socket.socket()
                s.connect((host, port))
                comm = "download " + str(fil)
                args = comm.split()
                print "running command " + comm
                s.send(comm)
                self.downl(args, s)
                s.close()


comm = raw_input("Manual(1)/Automated(2)")
if comm == "1" :
    thread1 = serverThread(1, "reciever")
    thread2 = clientThread(2, "sender")
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
elif comm == "2" :
    thread1 = serverThreadAuto(1, "reciever")
    thread2 = clientThreadAuto(2, "sender")
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()    