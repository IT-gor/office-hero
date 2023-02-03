Kurzanleitung:

1. Starten Sie die Webseite als Liveserver (z.B. mit VSCode oder PYCharm) [ansonsten funktioniert die Tonausgabe nicht]

2. Starten der Python Anwendung (und der virtuellen Umgebung)
Win: Führen Sie die start_windows.bat Batchdatei aus
Linux (Debian / Ubuntu): Führen Sie die start_debian.sh Shelldatei aus
Mac: Erstellen Sie bitte zuerst eine virtuelle Umgebung (siehe Link zur Anleitung) und aktivieren Sie diese. Installieren Sie im Anschluss die Pakete aus requirements.txt. 

Anleitung (Mac): https://sourabhbajaj.com/mac-setup/Python/virtualenv.html
Um die Pakete zu installieren nutzen Sie bitte folgenden Befehl:
pip install -r requirements.txt

Alternativ können Sie auch die Pakete in der requirements.txt auch systemweit mit demselben Befehl installieren.

3. Passen Sie ggf. den Midi-Port an, damit die Anwendung richtig funktioniert. Sehen Sie hierfür in die Ausgabe der Python-Konsole (starten Sie die batch/shell hierfür aus dem Terminal heraus) und in die Ausgabe der JavaScript-Konsole (Entwicklertools im Browser). Passen Sie einfach die Nummer des gewünschten Midiports an.

office-hero.py
outport = mido.open_output(mido.get_output_names()[-1])
inport = mido.open_input(mido.get_input_names()[-1])

Hier wird der letzte Midi-Port verwendet. 
Sollte der aktuell eingestellte Port nicht funktionieren, kann man diese auch manuell angeben.

Beispiel:
outport=mido.open_output('LoopBe Internal MIDI 2')
inport=mido.open_input('LoopBe Internal MIDI 1')

js/midi.js
output = midiAccess.outputs.get('output-1');

Der Output wird aber auch in der Konsole des Browser ausgegeben und kann angepasst werden.
Sollte der aktuell eingestellte Port nicht funktionieren, kann man die id aus der Konsole mit der aktuellen id ('output-1') austauschen.

ACHTUNG: Die Ports müssen in beiden Dateien das selbe MIDI-Device verwenden.