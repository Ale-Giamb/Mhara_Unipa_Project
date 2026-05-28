# MHARA Robot System - Guida Completa

Questa guida è stata realizzata per il RoboticsLab dell'Università di Palermo.
In tutta la guida si farà riferimento a file e percorsi presenti all'interno del laboratorio, ciononostante non è difficile riadattarlo al proprio contesto.
Essa contiene tutti i comandi necessari per avviare e gestire il sistema robotico MHARA 
In questo progetto sono utilizzati i robot Pepper e GO2.
Lo scopo di pepper è quello di suggerire ricette o attività sulla base delle informazioni ottenute in fase di registrazione.
Lo scopo di GO2 è quello di monitorare l'ambiente e suggerire dei consigli relativi a postura, sedentarietà ...

**Nota**: 
Per una migliore comprensione del parlato si è scelto di utlizzare il microfono del pc, rispetto a quello di Pepper.  
Per attivare o disattivare l'ascolto si deve premere ctrl dentro una qualsiasi pagina web.
	  Resta comunque possibile utilizzare il microfono di Pepper mediantela la funzione record di UnipaQi speech.
	  Per avviare uno dei test bdi levare il commento  di riferimento all'interno a src/bdi_agents/bdi_agents.mas2j prima dell'uso.
	  IMPORTANTE: Qualora si effettuano modifiche al codice che riguardino la parte di architettura ros2, dopo aver salvato i file
	  è necessario effettuare il comando "colcon build" da terminale nel percorso opportuno
	  questo permette di rendere le modifiche effettive.
	
---

## 📋 Indice

1. [Prerequisiti](#prerequisiti)
2. [Avvio Database Neo4j](#avvio-database-neo4j)
3. [Avvio BDI (Belief-Desire-Intention)](#avvio-bdi-belief-desire-intention)
4. [Avvio Agenti Jason](#avvio-agenti-jason)
5. [Avvio UniPA QI](#avvio-unipa-qi)
6. [Avvio Altri Nodi ROS2](#avvio-altri-nodi-ros2)
7. [Avvio Completo con Terminator](#avvio-completo-con-terminator)
8. [Connessione al Robot](#connessione-al-robot)
9. [Risoluzione Problemi](#risoluzione-problemi)

---

## Prerequisiti
Assicurarsi si aver letto il file Codice Documentazione per avere chiarezza dell'intera composizione del codice e solo successivamente passare alla guida sottostante.
Prima di iniziare, assicurarsi di:

- Avere il percorso corretto configurato nel file `~/.bashrc`
- Verificare che tutte le dipendenze siano installate
- Avere i permessi di esecuzione sui file necessari

---

## Avvio Database Neo4j

Il database a grafo Neo4j deve essere avviato.

Esempio:
```bash
./neo4j-desktop-1.6.1-x86_64.AppImage
```
Importare il database mhara e
successivamente avviare grafo mhara 

**Nota**: Attendere il completo avvio dell'interfaccia grafica prima di procedere con i passi successivi.

---

## Connessione al Robot GO2

Seguire questa procedura nell'ordine indicato per stabilire la connessione con il robot.

### Passo 1: Avvio del Robot

Accendere il robot e attendere il completamento della fase di boot.

### Passo 2: Configurazione AP Mode

1. Aprire l'app mobile di controllo del robot
2. Selezionare dalle impostazioni, robot setting ed in fondo cliccare **AP Mode**
3. Inserire la password WiFi: `12345678`

**Percorso nell'app**: Device → Robot Dog Setting → (scorrere in fondo) → AP Mode

### Passo 3: Connessione Scheda WiFi Esterna

1. Collegare la scheda WiFi esterna via USB al computer
2. Eseguire il comando di connessione:

```bash
go2wifi
```

Questo comando configura automaticamente la scheda per comunicare con il robot.
Qualora non funzionasse perchè non è recettiva la scheda wifi, andare sulle impostazioni wifi del dispositivo,
selzionare la scheda wifi realtek e effettuare una scansione dellle reti wifi per verificare che la rete del go2 sia accessibile

### Passo 4: Attivazione VPN

Attivare la VPN per garantire la connessione sicura:

```bash
vpn
```

### Configurazione Rete Finale

Dopo l'attivazione della VPN, il sistema avrà due connessioni WiFi attive:

1. **Prima connessione**: Collegata al TP-Link (con VPN attiva)
   - Utilizzata per la comunicazione con i vari robot della rete
   
2. **Seconda connessione**: Collegata direttamente al robot
   - Utilizzata per il controllo diretto del robot

**Importante**: Entrambe le connessioni devono rimanere attive per il corretto funzionamento del sistema.

---
## Avvio BDI (Belief-Desire-Intention)



### MHARA Environment 

```bash
cd ~/Scrivania/mhara_env/MHARA_Unipa/src
ros2 launch bdi_launch.py
```

**Nota**: Utilizzare il percorso corretto in base alla propria configurazione del sistema.

---

## Avvio Agenti Jason

Gli agenti Jason gestiscono il comportamento intelligente del sistema.


### MHARA Environment 

```bash
cd ~/Scrivania/mhara_env/MHARA_Unipa/src/bdi_agents
jason bdi_agents.mas2j
```

---

## Avvio UniPA QI

Avvio del nodo QI UniPA con configurazione di rete specifica.

```bash
ros2 launch qi_unipa qi_unipa2.launch.py ip:=192.168.0.105 port:=9559
```

**Parametri di configurazione**:
- `ip`: Indirizzo IP del robot (default: 192.168.0.105)
- `port`: Porta di comunicazione (default: 9559)

---

## Avvio Altri Nodi ROS2

Lancio del controller principale per il robot Pepper.

```bash
ros2 launch my_robot_controller peppercontroller.launch.py
```




## Risoluzione Problemi

### Il database Neo4j non si avvia

- Verificare i permessi di esecuzione: `chmod +x neo4j-desktop-1.6.1-x86_64.AppImage`
- Controllare che non ci siano istanze già in esecuzione

### ROS2 non trova i pacchetti

- Verificare che il workspace sia stato compilato: `colcon build`
- Source del workspace: `source install/setup.bash`
- Controllare la variabile `ROS_DOMAIN_ID`

### Impossibile connettersi al robot

- Verificare che il robot sia completamente avviato
- Controllare che la password WiFi sia corretta (12345678)
- Assicurarsi che la scheda WiFi esterna sia riconosciuta dal sistema
- Verificare lo stato della VPN con `vpn status` (se disponibile)

### Problemi con gli agenti Jason

- Verificare che JDK sia installato e configurato correttamente
- Controllare il file di configurazione `bdi_agents.mas2j`
- Verificare i log per eventuali errori di sintassi

---

## Note Aggiuntive

- Tutti i percorsi partono dalla directory home (`~/`)
- I comandi devono essere eseguiti nell'ordine specificato per garantire il corretto funzionamento
- Si consiglia di creare uno script di avvio automatico per semplificare la procedura
- Mantenere aggiornata la documentazione in caso di modifiche alla configurazione

---


**Versione documento**: 1.0  
**Ultimo aggiornamento**: Gennaio 2026
