"""
@author Igor Romanica
@version 1.0

Dies ist der Python-Code für unser Office Hero Spiel - ein Guitar Hero Ableger.
Wir nutzen OpenCV um Bilder der Webcam einzulesen und tracken den vom Spieler benutzen Textmarker,
mit dem er die Noten treffen soll, die eingeblendet werden.
Außerdem wird den Webcam-Bildern die Benutzeroberfläche und die Hinweise des Spiels eingeblendet.
Der Song wird aus einer Midi-Datei eingelesen. Es können Midi-Nachrichten empfangen werden, die Auskunft
über die Markerfarbe, den ausgwählten Songtitel und das Instrument geben. Außerdem ob die automatische Farb-
erkennung gestartet wurde oder der Song gestartet bzw. gestoppt wurde.
Da mehrere Operationen parallel und ohne Zeitverzörzgerung ablaufen, werden sie in Threads gestartet.
Zu den Threads gehören
-listenOnChange (lauscht nach Midi Nachrichten)
-playScreen (stellt die Noten und das Interface auf dem Screen dar)
-readMidiFile (liest die ausgwählte Midi Datei unter Beachtung der Abspielpausen ein)
-playMidiNote (spielt einee einzelne Midi-Note)

Programm-Ablauf in dieser Python-Datei:
1. setzen der Standardwerte (Markerfarbe, Fenstergröße, Midi-Ports (erste Midi-Output/Input-Port der Liste)
2. starten der vier Threads (listenOnChange, playScreen, readMidiFile, playMidiNote)
3. die Threads laufen endlos weiter im Loop (while 1) und ändern das Verhalten je nach den vom Benutzer ausgewählten
    Parametern (Start / Stop des Songs, starten der Farberkennung), welche in dem listenOnChange-Thread gesetzt werden,
    bzw. abhängig davon, ob der Song noch abspielt oder bereits beendet wurde (play_bool, song_ended).

Detailierte Beschreibung der Threads:
listenOnChange: Lauscht auf eingehende Midi-Nachrichten, setzt die Werte für Markerfarbe (jeweils die Unter- und
    Obergrenze der Farbwerte im HSV-Farbraum (l_h, u_h, l_s, u_s, l_v, u_v) / starten der Farberkennung (detect_color),
    Songtitel bzw. Midi-Datei (midi_song), Start / Stop des Songs (play_bool)
readMidiFile: Falls der Benutzer auf start klickt (play_bool=True) wird der ausgewählte Midi-Song (midi_song) eingelesen
    und in der Notenliste (note_list) für den PlayScreen-Thread zur Verfügung gestellt.
playScreen: Fügt die UI zu dem Webcam-Video hinzu, wie die Target Area (Bereich in dem Noten getroffen werden können),
    Rechteck um den erkannten Input-Marker, Text zum Punktestand und Highscore, Noten-Symbole (falls play_bool = True).
    Ruft Funktionen auf, um die Notentreffer zu erkennen (detectNoteHit(note)) und kennzeichnet die Noten ggf. als
    getroffen. Prüft ob die nächste Note abgespielt werden soll und setzt die Note ggf. als play_note Variable.
playMidiNote: Prüft ob eine Note gesetzt wurde für play_note. Falls play_note vorhanden ist (!= False) wird die Note
    abgespielt und wieder auf False gesetzt.

Lesen Sie bitte die Kommentare der jeweiligen Funktionen für weitere Details zu den Thread Methoden.
Schauen Sie sich für eine Übersicht des Zusammenspiels der Threads bitte das entsprechende Diagramm in der Doku an.

Verwendete Bibliotheken:
cv2 (OpenCV): Einlesen der Webcam-Bilder, UI-Gestaltung, Zeichnen der Noten-Symbole, Erkennung vom Input-Marker
mido (MIDI Objects for Python): Kommunikation zwischen Python- und JavaScript-/HTML-Welt, Einlesen der Midi-Datei.
threading: Ermöglicht die parallel laufenden Threads
NumPy: Wird für die Erstellung der Masken verwendet und die Kombination mit
    dem ursprünglichen Bild (detectMarker)
pygame: Verzögerung des Durchlaufs der Thread-Loops mittels clock.tick(ms) - ms = Zeit in Millisekunden

Der Python Code baut auf der "Piano tile app" von Wilson Chao auf, welcher in einem Youtube-Video vorgestellt wurde.
Hierzu zählt der Code aus den Funktionen "readMidiFile", "playScreen", und "playMidiNote". Der Code wurde also
in drei Threads aufgeteilt, um unserer Ablauflogik gerecht zu werden (z.B. spiele nur getroffene Noten ab.)
Der Quell-Code kann aus der Videobeschreibung entnommen werden.
Quelle: youtube.com/watch?v=w732EXqmfZU

"""

import time
import mido
from threading import Thread
import cv2
import numpy as np
import pygame

# Liste mit Midi-Noten
note_list = []  # Struktur von note_list: [[x-Wert, y-Wert], Midi-Nachricht, False (Note getroffen), False (Note abgespielt)

# Midi Ports
outport = mido.open_output(mido.get_output_names()[-1])
inport = mido.open_input(mido.get_input_names()[-1])
# outport=mido.open_output('LoopBe Internal MIDI 2')
# inport=mido.open_input('LoopBe Internal MIDI 1')

print("mido.get_output_names(): ", mido.get_output_names())
print("mido.get_input_names(): ", mido.get_input_names())

WIDTH = 640
HEIGHT = 480

play_bool = False  # True wenn der Song abgespielt wird
song_ended = False  # True wenn das Einlesen des Songs beendet wurde
play_note = False  # Wert der Note die aktuell gespielt wird

points = 0
highscore = 0

# Y-Werte für Target Area (Bereich der Treffererkennung)
target_area_bottom = int(HEIGHT/3 +20)
target_area_top = int(HEIGHT/3 -20)

# Positionsdaten vom erkannten Marker-Bereich (rectangle)
marker_area_left_top = -1  # (x,y)
marker_area_right_bottom = -1  # (x,y)

# vorausgewählte Midi-Song
midi_song = mido.MidiFile('midis/Ente.mid')
# midi_song_tmp = False
midi_song_tmp = mido.MidiFile('midis/Ente.mid')

# init (HSV) Farbwerte für Gelb
l_h, u_h = 25, 42
l_s, u_s = 150, 245
l_v, u_v = 50, 200

# für die noteToScreenRatio() Funktion
min_note = -1
span_note = -1
noten_anzahl = 0

# Wird für die clock.tick(ms) Methode verwendet. ms = Zeit in Millisekunden, die ein Thread-Loop mindest braucht.
clock = pygame.time.Clock()

# um die Markerfarbe zu erkennen
detect_color = False
detect_timer = False
color_red = False  # hilft dabei die Farbwinkel-Maske von rot zu erstellen
loop_timer = time.time()  # hilft bei der automatischen Farberkennung (detectColor)
loop_timer_delta = 0


def get_play_bool():
    global play_bool
    return play_bool


def readMidiFile():
    """ liest die ausgewählte Mididatei ein (midi_song) und speichert die Midi-Nachrichten mit den xy-Screen-Werten in die note_list.
    Mit mid.play() werden korrekte Pausen zwischen den Noten erzeugt.
    Sobald der Song endet wird song_ended auf True gesetzt.
    Struktur von note_list: [[x-Wert, y-Wert], Midi-Nachricht, False (Note getroffen), False (Note abgespielt)
    Input: / Output: keine - alle Werte werden für globale Variablen gesetzt
    Läuft andauernd im Thread thread_readMidiFile.
    """
    global note_list, song_ended, midi_song  #, mid, note_list_hitted
    while 1:
        if not song_ended:
            note_list = []
            noteToScreenRatio(midi_song)
            for msg in midi_song.play():  # hier werden Pausen gemacht beim Lesen
                if msg.type == 'note_on':
                    n = msg.note
                    x = noteToScreenPosition(n)
                    if msg.type == 'note_on' and msg.velocity != 0:
                        # Struktur von note_list: [[x-Wert, y-Wert], Midi-Nachricht, False (Note getroffen), False (Note abgespielt)
                        note_list.append([[x, HEIGHT], msg, False, False])
                    # Checke ob noch gespielt wird (innerhalb der loop - frischer Zugriff auf global variable) ...
                    if not get_play_bool():
                        break  # ... und breake die Loop ggf.
                clock.tick(50)
            song_ended = True
        clock.tick(50)


def playMidiNote():
    """ spielt die aktuell angeschlagene Midi-Note (=play_note). Setzt den Wert danach auf False.
    Es ist nur eine einzelne Midi-Nachricht oder False.
    Input / Output: keine - play_note wird global gelesen / gesetzt
    Läuft andauernd im Thread thread_playMidiNote. """
    global play_note
    while 1:
        if play_note:
            outport.send(play_note)
            play_note = False
        clock.tick(50)


def playScreen():
    """ Erzeugt den Video-Output und prüft an entsprechenden stellen den Video-Input (detectMarker/detectNoteHit).
     Fügt die UI-Elemente zu den Kamera-Videobildern hinzu (Noten-Symbole, Bereich der Target-Area, Text: Punkte, etc.).
     Blendet je nach Zustand den Schlusstext ein nach Songende (song_ended) oder den Bereich zur Farberkennung ein (detect_color).
     Ansonsten werden die Noten des Songs eingeblendet, falls der Song abgespielt wird (play_bool).
     Die Notenliste (note_list), die ggf. (play_bool) bereits von readMidiFile() erstellt wurde, wird von hinten geloopt,
     um erstmal Noten zu löschen die bereits außerhalb des Screens sind.
     Es wird geprüft, ob die Note aktuell getroffen wurde (detectNoteHit(note)) im entsprechenden bereich (Target Area).
     Falls die Note getroffen wurde, wird ein Punkt hinzugefügt und die Note als getroffen gekennzeichnet.
     Falls die Note zwar bereits getroffen, aber noch nicht abgespielt wurde und die Target Area gerade verlassen hat,
     wird die Note abgespielt und als abgespielt gesetzt.
     Die Noten werden in zwei verschiedenen Farben eingefärbt, je nachdem ob sie bereits getroffen wurden.
     Nachdem der Song geendet hat (song_ended) und keine Noten mehr in der Noteliste (note_list) vorhanden sind,
     was bedeutet, dass alle Noten bereits außerhalb des Screens waren, wird der Schlusstext eingeblendet (addFinalText).
     Struktur von note_list: [[x-Wert, y-Wert], Midi-Nachricht, Boolean (Note getroffen), Boolean (Note abgespielt)
     Läuft andauernd im Thread thread_playScreen.
     Input: / Output: keine - alle Werte werden für globale Variablen gesetzt
    """
    global note_list, note_list_hitted, points, song_ended, prev, frame_rate, play_note, song_loaded, detect_color

    vid = cv2.VideoCapture(0)
    while 1:
        ret, frame = vid.read()
        prev = time.time()
        frame = cv2.flip(frame, 1)
        frame = detectMarker(frame)
        frame = addScoreText(frame)

        if detect_color:
            frame = detectColor(frame)
        else:
            frame = drawTargetArea(frame)

        if song_ended and len(note_list) == 0:  # Song ist nun zu Ende
            frame = addFinalText(frame)

        # checke ob Song abspielt
        if play_bool and len(note_list) > 0:
            for i in range(len(note_list)-1, -1, -1):
                # delete notes that are off screen
                if note_list[i][0][1] < -15:
                    note_list.remove(note_list[i])
                else:
                    x, y = note_list[i][0][0], note_list[i][0][1]

                    # Note wurde nicht gespielt, befindet sich im Target Area und wurde (gerade) getroffen
                    if not note_list[i][-2] and target_area_top < note_list[i][0][1] < target_area_bottom and detectNoteHit(note_list[i][0]):
                        points += 1
                        note_list[i][-2] = True  # Note wurde getroffen, setze Wert auf True

                    if note_list[i][-2]:  # male erstmal alle Noten die bereits getroffen wurden
                        cv2.rectangle(frame, [x-3, y-3], [x+20+3, y+10+3],  (0, 0, 0), -1)  # Farbe für getroffene Noten (innen)
                        cv2.rectangle(frame, [x, y], [x+20, y+10],  (255, 255, 255), -1)  # Farbe für getroffene Noten (außen)
                        if not note_list[i][-1] and y < target_area_bottom-25:  # spiele Note falls Sie den Target Area Bereich verlässt
                            play_note = note_list[i][1]
                            note_list[i][-1] = True  # note wurde gespielt, also True
                    else:
                        cv2.rectangle(frame, [x-3, y-3], [x+20+3, y+10+3],  (255, 255, 255), -1)  # Farbe für nicht getroffene Noten (innen)
                        cv2.rectangle(frame, [x, y], [x+20, y+10],  (0, 0, 0), -1)  # Farbe für nicht getroffene Noten (außen)
                    note_list[i][0][1] -= 4  # y-Wert wird erhöht
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.imshow('Office Hero', frame)
        cv2.setWindowProperty('Office Hero', cv2.WND_PROP_TOPMOST, 1)
        clock.tick(50)


def noteToScreenRatio(midi_song):
    """
    Berechnet die optimale Verteilung der Noten auf dem Screen. Trifft die Vorbereitung für noteToScreenPosition(note).
    Input: komplette Midi Datei (midi_song)
    Output: kein Returnwert, setzt die Werte global für die kleinste Note (min_note) und die Notenspanne (span_note)
    Wird aufgerufen von readMidiFile.
    """
    global min_note, span_note, noten_anzahl
    noten_anzahl = 0
    note_list = []
    for m in midi_song:
        if m.type == 'note_on':
            note_list += [m.note]
            noten_anzahl += 1
    min_note = min(note_list)
    max_note = max(note_list)
    span_note = max_note - min_note  # so viele Noten (Abstufungen)


def noteToScreenPosition(note):
    """
     Berechnet den X-Pixelwert an dem die Note dargestellt werden soll.
     Input: Integer das der Midi-Note entspricht.
     Output: X-Wert der Notendarstellung
     Wird aufgerufen von readMidiFile.
     """
    global min_note, span_note
    return int((((note-min_note) / span_note) * (WIDTH * 0.5)) + (WIDTH * 0.25))


def drawTargetArea(img):
    """ Zeichnet die Target Area ein, also den Bereich in dem der Marker und der Notenanschlag erkannt wird.
     Das Rechteck geht über den Bildrand hinaus. Es werden de facto nur zwei Linien eingezeichnet.
     Input: img
     Output img (zusätzlich mit Target Area)
     Wird aufgerufen von playScreen.
    """
    return cv2.rectangle(img, (-2, target_area_bottom), (WIDTH+2, target_area_top), (10, 200, 0), 2)  # green


def addScoreText(img):
    """
    Fügt den Text bezüglich der Punkte und des Highscores hinzu der oben links und rechts eingeblendet wird
    Input: img
    Output img (zusätzlich mit Punkten / Highscore)
    Wird aufgerufen von playScreen.
    """
    cv2.rectangle(img, (WIDTH - 100, 10), (WIDTH - 5, 30), (0, 0, 0), -1)
    cv2.putText(img, "Points: " + str(points), (WIDTH - 100, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    cv2.rectangle(img, (5, 10), (130, 30), (0, 0, 0), -1)
    return cv2.putText(img, "Highscore: " + str(highscore), (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)


def addFinalText(img):
    """
    Fügt den Text bezüglich der Punkte und des Highscores hinzu der nach Songende eingeblendet wird
    Input: img
    Output img (zusätzlich mit Punkten / Highscore)
    Wird aufgerufen von playScreen.
    """
    cv2.rectangle(img, (WIDTH//2 - 245, HEIGHT//2-15), (WIDTH//2 + 245, HEIGHT//2+15), (0, 0, 0), -1)
    cv2.putText(img, "You have " + str(points) + " out of " + str(noten_anzahl) + " total points",
                (WIDTH // 2 - 240, HEIGHT // 2 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
    if points > highscore:
        cv2.rectangle(img, (WIDTH//2 - 245, HEIGHT//2+50), (WIDTH//2 + 245, HEIGHT//2+20), (0, 0, 0), -1)
        cv2.putText(img, "You have a new highscore! Superb!!",
                    (WIDTH // 2 - 240, HEIGHT // 2 + 42), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
    return img


def detectMarker(frame):
    """
     Zeichnet Rechteck um den Marker herum auf dem "frame"-Bild ein, falls er erkannt wurde und setzt die Positionsdaten.
     Gibt das Bild wieder zurück.

     Input: frame (Webcam-Bild mit eingezeichneter UI)
     Output: frame (Webcam-Bild mit eingezeichneter UI, mit Rechteck um Marker herum, falls er erkannt wurde),
        Marker-Positon wird global gesetzt (marker_area_left_top, marker_area_right_bottom)

     Funktion wird von playScreen aufgerufen.

     Details:
     Aktualisiert die Positionsdaten des Marker-Rechtecks (marker_area_left_top, marker_area_right_bottom).
     Nur der Bereich in der Target Area und herum ( Höhe: target_area_top-20:target_area_bottom+20, gesamte Breite) wird
     nach dem Marker gescannt.
     Der Marker wird anhand der Range der HSV-Farbwerte ermittelt. Dafür werden drei Masken erstellt jeweils für den
     Wertebereich (inRange()) von dem Farbwinkel (Hue), der Sättigung (Saturation) und der Helligkeit (Value).
     Falls eine rote Markerfarbe gewählt wurde, werden zwei Farbwinkel-Masken addiert. Grund hierfür ist, dass Rot im
     HSV-Farbraum einem Winkel von 0 Grad entspricht und Werte sowohl größer Null, als auch kleiner 360 Grad, umfasst.
     Die lower Boundary entspricht also einem Wert von unter 360 Grad (und > 340°) und die obere Grenzwert einem Wert
     über 0 Grad (und < 20°). Die drei Masken werden zu einer Maske multipliziert. Im Anschluss wird der untersuchte
     Bildausschnitt (roi_rectangle) mit der Maske kombiniert (bitwise_and()).
     Nun wird der Bildausschnitt nach Konturen untersucht und von den Konturen wird die größt erkannte Kontur ermittelt.
     Die Marker-Positionsdaten werden um die Höhe korrigiert (target_area_top-20) die auf Grund des Bildausschnittes im
     Vergleich zum Gesamtbild fehlt und sie werden global gesetzt (marker_area_left_top, marker_area_right_bottom).
     Es wird ein Rechteck um den erkannten Markerbereich gezeichnet auf das Bild (frame).
     """
    global marker_area_left_top, marker_area_right_bottom, l_h, u_h, l_s, u_s, l_v, u_v, target_area_bottom, target_area_top, WIDTH

    # nehme nur den Ausschnitt vom rectangle als ROI
    roi_rectangle = frame[target_area_top-20:target_area_bottom+20:, 0:WIDTH]   # leicht über Target Area hinaus, um Marker sauber zu erkennen
    frame_hsv = cv2.cvtColor(roi_rectangle, cv2.COLOR_BGR2HSV)
    frame_gray = cv2.cvtColor(roi_rectangle, cv2.COLOR_BGR2GRAY)
    h, s, v = cv2.split(frame_hsv)

    # Rot entspricht einem Winkel von 0 Grad im HSV-Farbraum und umfasst Werte sowohl größer Null, als auch kleiner 360 Grad.
    # Die lower Boundary entspricht also einem Wert von unter 360 Grad (und > 340°) und die obere Grenzwert einem Wert über 0 Grad (und < 20°)
    # Im Falle einer roten Farbe werden einfach zwei Farbwinkel-Masken addiert.
    if not color_red:
        lower_h = np.array([l_h])
        upper_h = np.array([u_h])
        mask_h = cv2.inRange(h, lower_h, upper_h)
    else:
        lower_h = np.array([l_h])
        upper_h = np.array([u_h])
        lower_mask = cv2.inRange(h, np.array([0]), upper_h)
        upper_mask = cv2.inRange(h, lower_h, np.array([180]))
        mask_h = lower_mask + upper_mask

    lower_s = np.array([l_s])
    upper_s = np.array([u_s])
    mask_s = cv2.inRange(s, lower_s, upper_s)

    lower_v = np.array([l_v])
    upper_v = np.array([u_v])
    mask_v = cv2.inRange(v, lower_v, upper_v)

    # kombinieren der drei Binärmasken
    mask = mask_h * mask_s * mask_v
    mask_result = cv2.bitwise_and(frame_gray, frame_gray, mask=mask)

    contours, hierarchy = cv2.findContours(mask_result, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    area_detected = []

    # Loope über die erkannten Konturen, füge Bereiche in die area_detected Liste hinzu, die groß genug sind.
    for c in contours:
       # Fläche für das Rechteck ermitteln --> min x,y und max x,y Werte = Rechteckfläche
       vals_x = []
       vals_y = []
       for dot in c:
           vals_x += [dot[0,0]]
           vals_y += [dot[0,1]]
       if(len(vals_x) > 0 and len(vals_y) > 0):
           min_x, max_x = min(vals_x), max(vals_x)
           min_y, max_y = min(vals_y), max(vals_y)

           # füge nur Bereiche hinzu, die die Mindestgröße erfüllen
           if min_x != max_x and min_y != max_y and abs(min_x - max_x) > 15 and abs(min_y - max_y) > 15:
               area_detected += [[[min_x, min_y], [max_x, max_y]]]

    # loope auf der Suche nach dem größten Bereich. Wir wollen den Index ermitteln.
    index = -1
    span_x = 0
    span_y = 0
    for i in range(len(area_detected)):
        [min_x, min_y], [max_x, max_y] = area_detected[i]
        if max_x - min_x > span_x and max_y - min_y > span_y:
            index = i
            span_x = min_x - max_x
            span_y = min_y - max_y

    # aktualisiere die Marker Area Positionsdaten, falls ein Bereich erkannt wurde. Male ein Rechteck um den Marker herum.
    if index != -1:
        [min_x, min_y], [max_x, max_y] = area_detected[index]
        marker_area_left_top = (min_x, min_y + target_area_top-20)
        marker_area_right_bottom = (max_x, max_y + target_area_top-20)
        cv2.rectangle(frame, marker_area_left_top, marker_area_right_bottom, (10, 200, 0), 1)
    else:
        marker_area_left_top = -1
        marker_area_right_bottom = -1
    return frame


def detectNoteHit(note):
    """ Gibt Auskunft ob die Note von dem Marker getroffen wurde.
    Input: Liste mit x und y Wert [x,y]
    Output: return True, falls Note getroffen wurde und False falls nicht
    Funktion wird von playScreen aufgerufen. """
    global marker_area_left_top, marker_area_right_bottom
    if marker_area_left_top != -1:
        if marker_area_left_top and marker_area_right_bottom and ((marker_area_left_top[0]-20 < note[0] < marker_area_right_bottom[0]+20) and (marker_area_left_top[1]-20 < note[1] < marker_area_right_bottom[1]+20)):
            return True
        else:
            return False
    else:
        return False


def detectColor(img):
    """ Farbeerkennung wurde gestartet (detect_color = True).
     Blendet 5 Sekunden lang das Rechteck ein, das den Bereich markiert in dem die Farbe erkannt wird
     und eine entsprechende Nachricht.
     Liest nach dieser Zeit den Farbbereich aus und setzt die untere und obere Farbwert-Grenzen mit einer zusätzlichen Toleranz.
     Wird aufgerufen von playScreen() falls die Farberkennung aktiviert wurde (detect_color = True).
     Farberkennung wird per Midi-Message aktiviert (listenOnChange() -> if msg.value==11 -> detect_color = True).
     Input: img (Webcam-Bild mit GUI)
     Output: img (Webcam-Bild mit GUI und neuen Elementen)
     Gibt das Bild (img) wieder zurück.
     """
    global detect_color, detect_timer, l_h, u_h, l_s, u_s, l_v, u_v, color_red
    time_delta = time.time() - detect_timer  # Berechne wie lange die Farbekennung läuft (max. 5 sek)

    # Füge die UI Elemente hinzu
    cv2.rectangle(img, (WIDTH//2 - 155, HEIGHT//2 +50), (WIDTH//2 + 155, HEIGHT//2 +30), (0, 0, 0), -1)
    cv2.putText(img, "Place marker into rectangle in 5 sec.", (WIDTH//2 - 150, HEIGHT//2 +45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    cv2.rectangle(img, (WIDTH//2 - 10, HEIGHT//2 -30), (WIDTH//2 + 10, HEIGHT//2 -10), (0, 0, 0), -1)
    cv2.putText(img, str(int(6-time_delta)), (WIDTH//2 - 6, HEIGHT//2 -15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    # Bereich in dem die Farbe erkannt wird
    y1, y2 = HEIGHT//2 -145, HEIGHT//2 -135
    x1, x2 = WIDTH//2 - 5, WIDTH//2 + 5
    color_red = False

    if time_delta > 5:
        detect_timer = False
        detect_color = False

        # Teilbereich des Bildes erhalten (roi)
        roi = img[y1:y2, x1:x2]
        liH, liS, liV = [], [], []
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        for i in range(len(roi)):
            for h,s,v in roi_hsv[i]:
                liH += [h]
                liS += [s]
                liV += [v]
        minH = min(liH); maxH = max(liH)
        minS = min(liS); maxS = max(liS)
        minV = min(liV); maxV = max(liV)

        # checke ob rote Farbe den 0° Winkel umspannt...
        if maxH > 160 and minH < 22:
            color_red = True
            maxH = max([x for x in liH if x < 22])
            minH = min([x for x in liH if x > 160])

        # setze Farbe
        l_h, u_h = minH-8 if minH-8 > 0 else 0, maxH+8 if maxH+8 < 180 else 180
        l_s, u_s = minS-25 if minS-25 > 0 else 0, maxS+25 if maxS+25 < 255 else 255
        l_v, u_v = minV-25 if minV-25 > 0 else 0, maxV+25 if maxV+25 < 255 else 255

    return cv2.rectangle(img, (x1, y1), (x2, y2), (10, 200, 0), 2)


def listenOnChange():
    """ Prüft ob neue Midi Nachrichten (msg) eingetroffen sind sind und setzt die Variablenwerte entsprechend.
     Nachrichtenwerte:
     Markerfarbe (gelb, rot, blau, magenta), Farberkennung, Songauswahl und Start / Stop
     Läuft andauernd im Thread thread_listenOnChange.
     """
    global l_h, u_h, l_s, u_s, l_v, u_v, midi_song, midi_song_tmp, play_bool, points, highscore, song_ended, detect_color, detect_timer, note_list, color_red
    while 1:
        for msg in inport:
            if msg.type == 'control_change':
                ##### Textmarker Color #####
                if(msg.control==10 and msg.value in [1,2,3,4]):  # setze color_red auf False, falls eine Farbe gewählt wurde
                    color_red = False
                if(msg.control==10 and msg.value==1): #Gelb
                    l_h, u_h = 25, 42
                    l_s, u_s = 120, 255
                    l_v, u_v = 50, 248
                elif(msg.control==10 and msg.value==2): #Rot (magenta)
                    l_h, u_h = 180, 255
                    l_s, u_s = 120, 255
                    l_v, u_v = 50, 248
                elif(msg.control==10 and msg.value==3): #Blau
                    l_h, u_h = 100, 115
                    l_s, u_s = 120, 255
                    l_v, u_v = 50, 248
                elif(msg.control==10 and msg.value==4): #Grün
                    l_h, u_h = 55, 75
                    l_s, u_s = 120, 255
                    l_v, u_v = 50, 248
                elif(msg.control==10 and msg.value==11):  # Detect color
                    detect_color = True
                    detect_timer = time.time()
                    play_bool = False
                    song_ended = False

                    ##### Midi Songs #####
                elif(msg.control==10 and msg.value==5):
                    midi_song = mido.MidiFile('midis/Ente.mid')
                    midi_song_tmp = mido.MidiFile('midis/Ente.mid')
                elif(msg.control==10 and msg.value==6):
                    midi_song = mido.MidiFile('midis/addams.mid')
                    midi_song_tmp = mido.MidiFile('midis/addams.mid')
                elif(msg.control==10 and msg.value==7):
                    midi_song = mido.MidiFile('midis/Axel.mid')
                    midi_song_tmp = mido.MidiFile('midis/Axel.mid')
                elif(msg.control==10 and msg.value==8):
                    midi_song = mido.MidiFile('midis/mario2.mid')
                    midi_song_tmp = mido.MidiFile('midis/mario2.mid')

                ##### PLAY #####
                elif(msg.control==10 and msg.value==9):
                    note_list = []
                    midi_song = midi_song_tmp
                    play_bool = True
                    song_ended = False

                elif(msg.control==10 and msg.value==10):
                    play_bool = False
                    # song_ended = False
                    note_list = []
                    if points > highscore:
                        highscore = points
                    points = 0
        clock.tick(50)

##### Starte alle Threads #####
thread_listenOnChange = Thread(target=listenOnChange)
thread_playScreen = Thread(target=playScreen)
thread_readMidiFile = Thread(target=readMidiFile)
thread_playMidiNote = Thread(target=playMidiNote)

thread_listenOnChange.start()
thread_playScreen.start()
thread_readMidiFile.start()
thread_playMidiNote.start()
