import socket # pripojí knižnicu sieťovej komunikácie na úrovni socket

host = socket.gethostbyname(socket.gethostname()) # oznámi aplikácii IP adresu

print("Server bude bežať na adrese:", host)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # vytvorí komunikačný kanál UDP
port = 5678
s.bind((host, port)) # priradí kanál k adrese a portu
print("Server beží na porte:", port)
clients = set() # množina na uloženie adries klientov

while True:
    data, addr = s.recvfrom(1024) # čaká na príchod dát (maximálne 1024 bajtov)
    clients.add(addr)
    data = data.decode('utf-8') # dekóduje prijaté dáta z bajtov na reťazec
    print(str(addr) + data) # vypíše prijaté dáta spolu s adresou odosielateľa
    for c in clients:
        if c != addr: # neodosiela späť odosielateľovi
            s.sendto(data.encode('utf-8'), c) # odošle prijaté dáta všetkým ostatným klientom