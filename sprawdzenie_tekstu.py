import Projekt.lewica_prawica_crawler as crawler
from collections import Counter

slownik_lematyzacji = crawler.wczytaj_lematyzacje(crawler.nazwa_pliku_z_lematyzacja)
liczba_slow = 1000
nazwa_wczytywanego_artykulu = "Tekst.txt"

def wczytaj_model_jezyka(nazwa_pliku):
    wiersze= crawler.otworz_plik(nazwa_pliku)
    set_slow = set() #pusty set
    for i, linia in enumerate(wiersze):
        if i < liczba_slow: #pierwsze 1000 slow zeby dlugosc setu ogolnie nie miala znaczenia
            linia = linia.strip().split(",") #Usuwamy dziwne spacje ktore sie stworzyly
            set_slow.add(linia[0])
    return set_slow

linie_z_tekstu = crawler.otworz_plik(nazwa_wczytywanego_artykulu)
nowy_slownik = Counter()
for linia in linie_z_tekstu:
    lista_slow = crawler.przygotuj_linie(linia)
    nowy_slownik += crawler.zlicz_slowa(lista_slow)

set_slow = set(nowy_slownik.keys())
set_lewicowy = wczytaj_model_jezyka("slownik_lewica.csv")
set_prawicowy = wczytaj_model_jezyka("slownik_prawica.csv")

print (set_slow)
print ("z lewica ma wspolnego", len(set_slow.intersection(set_lewicowy)), "slow z top", liczba_slow)
print ("z prawica ma wspolnego", len(set_slow.intersection(set_prawicowy)), "slow z top", liczba_slow)