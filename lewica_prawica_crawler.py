from urllib import request
from bs4 import BeautifulSoup
from random import choice
import re
import operator
from collections import Counter
import urllib.error

# Rzeczy z zajec
# 1. Crawler (urllib + BeautifulSoap) i przeszukiwanie linkow
# 2. Regexp (wyszukiwanie URL)
# 3. Lematyzacja
# 4. Sposob sprawdzenia czy tekst jest lewicowy czy prawicowy - porownanie TOP N slow z setu najczesciej wystepujacych dla lewicy/prawicy

lista_adresow_prawica = ["http://niezalezna.pl", "http://www.rp.pl", "http://wpolityce.pl", "http://naszdziennik.pl"] # podstawowa lista stron PRAWICA

lista_adresow_lewica = ["http://www.newsweek.pl", "https://www.wprost.pl", "http://www.tvn24.pl", "http://natemat.pl"] # podstawowa lista stron LEWICA

mapowanie_stron_na_tresc = {"http://niezalezna.pl" : ("div", "class", "node-content"), # strona : miejsce gdzie ma tresc artykulu
                            "http://www.rp.pl": ("div", "class", "article-content-text"),
                            "http://wpolityce.pl":("div", "class", "intext-links"),
                            "http://naszdziennik.pl":("div", "id", "article-content"),
                            # --------------linia podziału politycznego ;) ---------------------------------
                            "http://www.newsweek.pl": ("div", "class", "article-detail"),
                            "https://www.wprost.pl": ("div", "class", "art-text"),
                            "http://www.tvn24.pl":("article", "class", "mb20"),
                            "http://natemat.pl" : ("div", "class", "article-body art__body") }
slowa_do_usuniecia = {"w", "na", "się", "z", "do", "na", "bez", "za", "pod", "u", "w", "nad", "o", "od", "po", "a", "r", "już",
                          "1", "2", "3", "4", "5", "6", "7", "8","9","0",
                              "jest", "oraz", "przez", "który", "także", "jednak"} #SET http://stackoverflow.com/questions/19985145/how-do-i-create-a-python-set-with-only-one-element

nazwa_pliku_z_lematyzacja = "lemmatization-pl.txt"
slownik_lematyzacji = dict()

def otworz_plik(nazwa_pliku):
    '''
    Otwiera plik i zwraca listę linii
    '''
    f = open(nazwa_pliku, 'r', encoding="utf8")
    lista_wierszy = f.readlines()
    f.close()
    return lista_wierszy

def wczytaj_lematyzacje(nazwa_pliku_z_lematyzacja):
    '''
    http://www.lexiconista.com/datasets/lemmatization/
    '''
    slownik_lematyzacji = dict()
    lista_wierszy = otworz_plik(nazwa_pliku_z_lematyzacja)
    for wiersz in lista_wierszy:
        #Forma odmieniona na podstawowa
        wiersz = wiersz.split() #Splituje poprawnie, zeby nie chcial literek przetwarzac
        slownik_lematyzacji[wiersz[1]] = wiersz[0]
    return slownik_lematyzacji

def wczytaj_strone(adres_html):
    '''
    Metoda odczytuje strone za pomoca urllib i zwraca jej kod HTML, wykorzystuje User-Agent zeby sie podszyc pod przegladarke
    '''
    lista_headerów = [{'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'},
                      {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'},
                      {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"},
                      {"User-Agent": 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'},
                      {"User-Agent": 'Opera/9.25 (Windows NT 5.1; U; en)'},
                      {"User-Agent": 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)'}]

    header = choice(lista_headerów) #wylosuj header tak zeby strona sie nie burzyla ze przeszukuje ja crawler
    try:
        req = request.Request(adres_html, None,headers=header)
        wczytana_stona = BeautifulSoup(request.urlopen(req).read(), "html.parser")
    except urllib.error.HTTPError:
        return
    return wczytana_stona

def wyszukaj_linki_do_podstron_artykulow_w_html(adres, slownik):
    '''
    Metoda przyjmuje podana strone - adres. Na tej podstawie szuka w niej linków prowadzących do artykułów z tej strony
    np. adres http://niezalezna.pl i szukamy w nim linków np http://niezalezna.pl/93752-wrzeszczeli-podczas-miesiecznicy-zadalismy-im-kilka-pytan-reakcja-rynsztok-wideo
    '''
    slownik_strona_linki = slownik
    podana_strona = wczytaj_strone(adres)
    linki = podana_strona.findAll('a') # ZNAJDUJE WSZYSTKIE LINKI
    if adres != "https://www.wprost.pl":
        linki = re.findall('(?:href=)[\"|\'](?=http|https)(.*?)[\"\']', str(linki)) # Za pomoca regexp znajdz tylko to co ma link
                                                                                #  http://stackoverflow.com/questions/23325404/regular-expression-to-match-certain-src-and-href-in-html-file
    else: #wprost ma bardzo dziwna strukture i trzyma lniki np /kraj ktore powinny odnosic sie do www.wprost.pl/kraj
        linki = re.findall('(?:href=)(?:(?:[\"\'])((?:[/][\w-]+){3,}.html)(?:[\"\']))', str(linki)) #<- https://regex101.com/
        poprawione_linki = []
        for link in linki:
            link = adres+link
            poprawione_linki.append(link)
        linki=poprawione_linki

    for znaleziony_link in linki: # Dla kazdego linka ze strony ktora widze, zapisz ja
        if (str(znaleziony_link)[0:len(str(adres))] == str(adres) ): # sprawdz czy to jest artykul ze strony glownej + czy nie jest to zdjecie
            slownik_strona_linki[adres].add(znaleziony_link)

def obetnij_znaki_w_linii(linia):
    '''
    Czyta wybrana linie tekstu, usuwa znaki niedozwolone
    '''
    lista_usuwanych_znaków = set([',', '.', '\r', '\n', '-', '"', "'", "/", "/", ":", "”", "„", "(", ")", "@", "_", "–", "*", "?", "…", "+", "“" , "#"])
    for ch in lista_usuwanych_znaków:
        if ch in linia:
            linia = linia.replace(ch, "")
    return linia

def przygotuj_linie(linia):
    """
    Zamienia linie na slowa, usuwa znaki
    wejscie: Pan Jan lubi jezdzic samochodem, ale lubi tez pomarancze, wczoraj zjadl obiad!
    wyjscie: [pan, jan, lubi,...]
    dodatkowo wykorzystuje sie lematyzacje
    """
    linia = obetnij_znaki_w_linii(linia)
    linia= linia.lower()
    linia = linia.split()
    linia = [lematyzuj(slowo) for slowo in linia]
    return linia

def lematyzuj(slowo):
    try:
        #Sprawdz czy slowo znajduje sie w lematyzacji
        return slownik_lematyzacji[slowo]
    except KeyError:
        return slowo

def zlicz_slowa(lista_slow):
    '''
    Sprawdza ile razy wystapilo kazde slowo w liscie.
    Rozwiazane jest "z internetu", ciezko sie je tlumaczy.
    wejscie: [pan, jan, je, placki, jadl, je, wczoraj, je, tez, jablka]
    wyjscie: slownik z tuplami {("pan":1) , ("je":2), ...}
    '''
    #http://stackoverflow.com/questions/20510768/python-count-frequency-of-words-in-a-list
    lista_slow = [slowo for slowo in lista_slow if len(slowo) > 3 and slowo not in slowa_do_usuniecia]
    counts = Counter(lista_slow)
    return counts

def zapisz_slownik_do_csv(slownik, nazwa):
    import csv
    with open("slownik_"+nazwa+".csv", "w", encoding="utf-8") as zapis:
        writer=csv.writer(zapis)
        slownik = slownik.most_common()
        for klucz,wartosc in slownik:
            writer.writerow([klucz,wartosc])

def stworz_jezyk_z_listy_portali(lista_adresow, nazwa):
    global slownik_lematyzacji
    slownik_lematyzacji = wczytaj_lematyzacje(nazwa_pliku_z_lematyzacja)
    slownik_strona_linki = dict.fromkeys(lista_adresow, set()) #pod kazda strona trzymamy set odwiedzonych juz linkow
                                            # np { "http://niezalezna.pl": ("http://niezalezna.pl/1", "http://niezalezna.pl/2")}

    for adres in lista_adresow: # uzupełnienie stron linkami artykulow
        wyszukaj_linki_do_podstron_artykulow_w_html(adres, slownik_strona_linki) # wyszukanie linkow z podstawowej strony

    slownik_wystapien_slow = Counter() # {slowo, wystapienia}, taki lepszy slownik bo da sie go dodawac
    for odwiedzona_strona in slownik_strona_linki.items(): #.items() iteruje po kluczach slownika [0] i wartosciach [1]
        strona_glowna = odwiedzona_strona[0] # strona glowna - "http://niezalezna.pl"
        set_linkow_z_danej_strony = odwiedzona_strona[1] # jeden z linkow zapisanych ze slownika - "http://niezalezna.pl/1"
        print ("Przetwarzam strone", strona_glowna)

        for i, link_do_artykulu in enumerate(set_linkow_z_danej_strony): # pod tym setem mamy sporo roznych linkow do artykulow z tej strony:
            print ("Przetwarzam link", (i+1) , "/", len(set_linkow_z_danej_strony))
            strona = wczytaj_strone(link_do_artykulu) # tresc strony

            szukany_element = mapowanie_stron_na_tresc[strona_glowna][0]
            szukany_parametr = mapowanie_stron_na_tresc[strona_glowna][1]
            szukana_wartosc = mapowanie_stron_na_tresc[strona_glowna][2]
            try:
                # Przyklad, szukamy DIV'a (element) z klasa (parametr) ktora ma wartosc "node-content"
                tresc_artykulu = strona.findAll(szukany_element, {szukany_parametr : szukana_wartosc}) # wyszukana tresc artykulu
            except AttributeError:
                continue

            for element in tresc_artykulu:
                lista_slow = przygotuj_linie(element.text)
                nowy_slownik = zlicz_slowa(lista_slow) #Lacze Countery (slowniki) i ich wartosci i klucze
                slownik_wystapien_slow = slownik_wystapien_slow + nowy_slownik #Pelne mapowanie uzupelnione o nowa linie

            #Wyniki lista top 20 slow aktualizowana po kazdym linku
            #sorted_word_values = sorted(slownik_wystapien_slow.items(), key=operator.itemgetter(1), reverse=True)
            #all_words = sum(i[1] for i in sorted_word_values)
            # print (link_do_artykulu, [(value[0], round((value[1]/all_words),4)) for value in sorted_word_values[:20]])

    zapisz_slownik_do_csv(slownik_wystapien_slow, nazwa)

if __name__ == "__main__":
    stworz_jezyk_z_listy_portali(lista_adresow_lewica, "lewica")





