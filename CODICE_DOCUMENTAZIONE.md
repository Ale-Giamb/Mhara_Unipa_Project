# 📚 MHARA Robot System - Documentazione Completa del Codice

Questa guida descrive l'architettura, i componenti principali e le modifiche consigliate per ogni parte del sistema MHARA.

---

## 📑 Indice

1. [Panoramica Generale](#panoramica-generale)
2. [Struttura del Progetto](#struttura-del-progetto)
3. [Componenti Principali](#componenti-principali)
4. [Descrizione dei Moduli](#descrizione-dei-moduli)
5. [Flusso di Comunicazione](#flusso-di-comunicazione)
6. [Punti di Modifica Comuni](#punti-di-modifica-comuni)

---

## Panoramica Generale

### Scopo del Sistema
Il sistema MHARA è un'architettura robotica multi-agente sviluppata dall'Università di Palermo che integra:
- **Robot Pepper**: Gestisce l'interazione con l'utente, offre ricette e suggerimenti in base ai dati raccolti
- **Robot GO2**: Monitora l'ambiente domestico, fornisce consigli sulla postura e sulla sedentarietà
- **Agenti BDI (Belief-Desire-Intention)**: Sistema di agenti intelligenti basato su Jason per il ragionamento logico
- **Database Neo4j**: Grafo della conoscenza per memorizzare informazioni su utenti, ricette e stato di salute

### Tecnologie Principali
- **ROS2 (Robot Operating System 2)**: Framework di comunicazione inter-processi
- **Jason**: Framework per agenti BDI
- **Neo4j**: Database a grafo per Knowledge Graph
- **WebRTC**: Comunicazione con GO2
- **LLMs (Large Language Models)**: Per elaborazione del linguaggio naturale
- **OpenCV**: Per elaborazione video

---

## Struttura del Progetto

```
MHARA_Unipa/
├── src/                          # Codice sorgente principale
│   ├── my_robot_controller/      # Controller principale di Pepper
│   ├── go2_robot_node/           # Controller per robot GO2
│   ├── movement/                 # Gestione movimenti robot
│   ├── bdi_agents/               # Agenti BDI in Jason
│   ├── speech/                   # Elaborazione discorso (speech-to-text)
│   ├── vision/                   # Elaborazione visione (computer vision)
│   ├── vital_sensors/            # Raccolta dati vitali
│   ├── audio/                    # Gestione audio
│   ├── qi_unipa/                 # Bridge QI-ROS2
│   ├── qi_unipa_msgs/            # Definizioni messaggi ROS2
│   ├── camera/                   # Gestione telecamera
│   ├── all_launch.py             # Script di avvio di tutti i nodi
│   ├── bdi_launch.py             # Script di avvio agenti BDI
│   └── nao_controller_launch.py  # Script di avvio controller NAO
├── build/                        # Artefatti di compilazione (generato da colcon)
├── install/                      # File installati (generato da colcon)
├── log/                          # Log di compilazione
├── data/                         # Dati generati a runtime
└── README.md                     # Guida di avvio veloce
```

---

## Componenti Principali

### 1. **Pepper Controller** (`src/my_robot_controller/`)
**Ruolo**: Orchestratore principale dell'interazione con Pepper

**File Principale**: `my_robot_controller/pepper_controller.py`

**Responsabilità**:
- Gestione della registrazione utente
- Coordinamento tra Speech Recognition e Speech Synthesis
- Integrazione con LLMs per generazione di risposte
- Comunicazione con agenti BDI
- Gestione della telecamera per riconoscimento volti
- Query al database Neo4j

**Punti di Modifica Comuni**:
- **Modificare risposte robot**: File `pepper_controller.py` → metodo `transcription_callback()`
- **Aggiungere nuovi topic publisher**: Linea ~45-60 (section "# Publisher")
- **Aggiungere nuovi topic subscriber**: Linea ~61-80 (section "# Subscriber")
- **Cambiare fonte audio**: File `audio_config.py` → metodo `AudioConfig.to_pc()` o `AudioConfig.to_pepper()`
- **Modificare interazione conversazionale**: Classe `Pepper_Controller` → metodi di callback

**Configurazione Audio**:
```python
# In pepper_controller.py linea ~24-32
audio_source = os.getenv("AUDIO_SOURCE", "pepper").lower()
if audio_source == "pc":
    AudioConfig.to_pc()      # Usa microfono PC
else:
    AudioConfig.to_pepper()  # Usa microfono Pepper
```

**Variabili d'Ambiente Importanti**:
- `AUDIO_SOURCE`: "pc" o "pepper" (predefinito: "pepper")
- `NEO4J_URI`: Indirizzo database (predefinito: "bolt://localhost:7690")
- `NEO4J_USERNAME`: Nome utente (predefinito: "neo4j")
- `NEO4J_PASSWORD`: Password (predefinito: "12345678")

---

### 2. **GO2 Robot Controller** (`src/go2_robot_node/`)
**Ruolo**: Gestisce la connessione e il controllo del robot GO2

**File Principale**: `go2_robot_node/Go2RobotNode.py`

**Responsabilità**:
- Connessione WebRTC con GO2
- Controllo movimenti del robot
- Acquisizione video dalla telecamera
- Acquisizione audio
- Controllo modalità operazionali

**Classi Principali**:

#### `Go2Controller`
```python
# Linea ~49-100
class Go2Controller:
    def __init__(self, conn):
        """Inizializza il controller con la connessione WebRTC"""
    
    async def init_robot(self):
        """Inizializzazione post-connessione"""
    
    async def move(self, x=0.0, y=0.0, z=0.0, duration=0.5):
        """Muove il robot (x avanti/dietro, y sinistra/destra, z rotazione)"""
    
    async def take_picture(self):
        """Cattura un'immagine dalla telecamera"""
```

**Punti di Modifica Comuni**:
- **Aggiungere nuovi comandi di movimento**: Metodo `move()` linea ~85-95
- **Aggiungere nuova funzionalità audio**: Classe `WebRTCAudioHub` (file `webrtc_audiohub.py`)
- **Modificare parametri di connessione**: Costanti in `constants.py`
- **Cambiare velocità movimenti**: Parametri nella funzione `move()`

**Comandi di Movimento**:
```python
# Parametri del metodo move():
x: float    # Movimento lineare avanti (>0) o indietro (<0). Range: -1.0 a 1.0
y: float    # Movimento laterale sinistra (<0) o destra (>0). Range: -1.0 a 1.0
z: float    # Rotazione antioraria (<0) o oraria (>0). Range: -1.0 a 1.0
duration: float  # Durata del movimento in secondi
```

---

### 3. **Agent Controller** (`src/my_robot_controller/my_robot_controller/Agent.py`)
**Ruolo**: Wrapper per l'esecuzione di agenti BDI tramite Jason

**Responsabilità**:
- Esecuzione di agenti BDI
- Comunicazione tra ROS2 e agenti Jason
- Gestione del ciclo di vita degli agenti

**Punti di Modifica Comuni**:
- **Aggiungere nuovi agenti**: Linea ~20-40
- **Modificare parametri di esecuzione**: Metodi di inizializzazione agenti

---

### 4. **Neo4j Driver** (`src/my_robot_controller/my_robot_controller/neo4j_driver.py`)
**Ruolo**: Gestione della connessione e query al database Neo4j

**Classe**: `Neo4jGraphConnection`

**Responsabilità**:
- Connessione al database
- Esecuzione di query Cypher
- Gestione degli errori di connessione


**Variabili di Connessione** (linea ~5-9):
```python
self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7690")
self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
self.password = password or os.environ.get("NEO4J_PASSWORD", "12345678")
```

---

### 5. **LLM Integration** (`src/my_robot_controller/my_robot_controller/LLMSummary.py`)
**Ruolo**: Integrazione con Large Language Models per generazione di testo

**Responsabilità**:
- Generazione di risposte conversazionali
- Riassunto di informazioni
- Elaborazione del linguaggio naturale

**Punti di Modifica Comuni**:
- **Cambiare modello LLM**: Linea ~10-20 (modello configurato)
- **Modificare prompt di sistema**: Linea ~30-40 (system prompt)
- **Regolare temperatura/top_p**: Parametri di generazione

---

### 6. **Camera & Vision** 
**File**: `src/my_robot_controller/my_robot_controller/HealthCam.py`

**Responsabilità**:
- Acquisizione da telecamera
- Riconoscimento volti
- Analisi video
- Estrazione informazioni visive

**Punti di Modifica Comuni**:
- **Modificare parametri telecamera**: Linea ~20-40
- **Aggiungere nuovi filtri video**: Funzioni di elaborazione
- **Cambiare modello di riconoscimento**: Linea ~50-60

---

### 7. **Movement Controller** (`src/movement/movement/movement_controller.py`)
**Ruolo**: Gestione del movimento base del robot Pepper

**Punti di Modifica Comuni**:
- **Aggiungere nuovi tipi di movimento**: Metodo `movement_callback()` linea ~20-25
- **Modificare parametri di velocità**: Funzione `walkTo()` linea ~60-70

---

### 8. **BDI Agents** (`src/bdi_agents/`)
**Linguaggio**: AgentSpeak (Jason)

**File Principale**: `bdi_agents/bdi_agents.mas2j`

**Responsabilità**:
- Ragionamento logico tramite agenti BDI
- Decisioni su nutrizione e stato cognitivo
- Interazione con ROS2

**Punti di Modifica Comuni**:
- **Aggiungere nuove credenze**: File `.asl` dei singoli agenti
- **Modificare piani**: Sezione "plans" nei file AgentSpeak
- **Cambiare regole di decisione**: Logica nel file `bdi_agents.mas2j`

**Attivazione Agenti**:
```java
// Nel file bdi_agents.mas2j, decommentare uno tra:
agents: nutrition_agent;        // Per monitoraggio nutrizione
// agents: cognitive_state;       // Per stato cognitivo
```

---

### 9. **Speech Recognition** (`src/speech/`)
**Responsabilità**:
- Conversione audio in testo
- Configurazione del microfono
- Gestione dei topic ROS2

**Topic ROS2**:
- **Subscriber**: `/record` (Bool) - Avvia registrazione
- **Publisher**: `/transcription` (String) - Testo trascritto

**Punti di Modifica Comuni**:
- **Cambiare provider TTS/STT**: Linea ~30-50
- **Modificare lingua**: Parametro lingua nei modelli
- **Aggiungere lingue aggiuntive**: File di configurazione

---

### 10. **Tools & Utility** (`src/my_robot_controller/my_robot_controller/tools.py`)
**Responsabilità**:
- Funzioni di utilità generiche
- Helper per query al database
- Utility di formattazione dati

**Punti di Modifica Comuni**:
- **Aggiungere nuove funzioni helper**: Aggiungi funzioni al file
- **Modificare funzioni di formattazione**: Metodi di utility

---

## Flusso di Comunicazione

### 1. Flusso Conversazionale Standard

```
┌─────────────────────────────────────────────────────────────┐
│ 1. AVVIO: Utente tocca Pepper o invia /start_conv           │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 2. REGISTRAZIONE: Raccolta dati utente (nome, età, etc.)    │
│    - pepper_controller.py: start_conversation()             │
│    - Dati salvati in Neo4j                                  │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 3. ACQUISIZIONE AUDIO: Attiva microfono (PC o Pepper)       │
│    - Speech module: /record (Bool)                          │
│    - Audio registrato                                       │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 4. SPEECH-TO-TEXT: Conversione audio in testo               │
│    - Topic: /transcription (String)                         │
│    - Testo inviato a pepper_controller                      │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 5. ELABORAZIONE: pepper_controller.transcription_callback() │
│    - Estrae intent dall'input utente                        │
│    - Query a Neo4j per recuperare informazioni              │
│    - Invio a LLM per generazione risposta                   │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 6. BDI (Opzionale): Invio richiesta a agenti Jason          │
│    - Topic: /to_bdi (String)                                │
│    - Agent.py coordina esecuzione                           │
│    - Ritorno risultato via /to_ros                          │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 7. GENERAZIONE RISPOSTA: LLM produce testo naturale         │
│    - LLMSummary.py                                          │
│    - Risposta formattata                                    │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 8. TEXT-TO-SPEECH: Conversione testo in audio               │
│    - Topic: /speak (String)                                 │
│    - Pepper pronuncia la risposta                           │
└───────────────┬─────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────┐
│ 9. VISUALIZZAZIONE: Mostra informazioni nel display         │
│    - Topic: /show (String)                                  │
│    - Optional /hide (Bool) per pulire schermo               │
└─────────────────────────────────────────────────────────────┘
```

### 2. Flusso Monitoraggio GO2

```
┌──────────────────────────────────┐
│ GO2 Acceso e Connesso            │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│ WebRTC Connection Stabilita       │
│ (go2_robot_node/Go2RobotNode.py) │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│ Acquisizione Video/Audio Continua │
│ - frame_queue globale            │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│ Analisi Video (Vision Module)     │
│ - Rilevamento postura             │
│ - Rilevamento movimento           │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│ Generazione Consigli              │
│ - Postura corretta                │
│ - Esercizi suggeriti              │
└───────────┬──────────────────────┘
            │
┌───────────▼──────────────────────┐
│ Invio a Pepper per Visualizzazione│
└──────────────────────────────────┘
```

### 3. Topic ROS2 Principali

| Topic | Tipo | Direzione | Descrizione |
|-------|------|-----------|-------------|
| `/transcription` | String | OUT (Speech) | Testo trascritto da audio |
| `/speak` | String | IN (Pepper Controller) | Testo da pronunciare |
| `/show` | String | IN (Pepper Controller) | Testo da mostrare sul display |
| `/hide` | Bool | IN (Pepper Controller) | Nasconde il display |
| `/record` | Bool | IN (Speech) | Attiva/disattiva registrazione |
| `/to_bdi` | String | OUT (Pepper Controller) | Messaggio agli agenti BDI |
| `/to_ros` | String | IN (Pepper Controller) | Risposta dagli agenti BDI |
| `/start_conv` | Bool | IN (Pepper Controller) | Avvia conversazione |
| `/get_camera` | Bool | IN (Pepper Controller) | Attiva telecamera |
| `/transcription_bdi` | String | IN (Pepper Controller) | Trascrizione dai BDI |
| `/query_al_db` | String | IN (Pepper Controller) | Query al database |
| `/consiglia_esercizio` | String | IN (Pepper Controller) | Suggerimenti esercizi |
| `go2/action` | String | OUT (Pepper Controller) | Azioni per GO2 |
| `go2/camera` | Bool | OUT (Pepper Controller) | Telecamera GO2 |

---

## Punti di Modifica Comuni

### 🎙️ 1. Cambiare Fonte Audio

**Posizione**: `src/my_robot_controller/my_robot_controller/audio_config.py`

**Opzione 1: Via variabile d'ambiente**:
```bash
export AUDIO_SOURCE=pc      # Usa microfono PC
export AUDIO_SOURCE=pepper  # Usa microfono Pepper
```

**Opzione 2: Nel codice**:
```python
# In pepper_controller.py linea ~24-32
if audio_source == "pc":
    AudioConfig.to_pc()      # ← Modifica qui
```

-

### 🔄 2. Modificare il Flusso di Compilazione

**Quando modificare il codice ROS2**, è necessario ricompilare:

```bash
# 1. Naviga nella directory principale
cd ~/Scrivania/mhara_env/MHARA_Unipa

# 2. Pulisci build precedenti (opzionale)
rm -rf build install log

# 3. Ricompila
colcon build

# 4. Source setup
source install/setup.bash

# 5. Avvia i nodi
ros2 launch my_robot_controller peppercontroller.launch.py
```

**Nota**: La compilazione potrebbe impiegare qualche minuto. Verifica che non ci siano errori.

---

### 🐛 10. Debug e Logging

**Abilitare Logging Dettagliato** (in qualunque file Python):

```python
import logging

# Imposta livello di logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MY_MODULE")
logger.setLevel(logging.DEBUG)

# Usa in diversi contesti
logger.debug("Messaggio di debug")      # Dettagli di esecuzione
logger.info("Informazione")              # Info generiche
logger.warning("Attenzione")             # Avvertimenti
logger.error("Errore")                   # Errori
logger.critical("Errore critico")        # Errori critici
```

**Monitorare Topic ROS2**:

```bash
# Elencare tutti i topic
ros2 topic list

# Monitorare un topic specifico
ros2 topic echo /transcription

# Mostrare info su un topic
ros2 topic info /transcription

# Vedere frequenza di pubblicazione
ros2 topic hz /transcription
```

---

## Checklist per Modifiche

Quando modifichi il codice, segui questa checklist:

- [ ] Ho identificato il file corretto da modificare
- [ ] Ho compreso il flusso di dati attraverso il modulo
- [ ] Ho fatto le modifiche nel file appropriato
- [ ] Ho testato la sintassi del codice
- [ ] Se è codice ROS2: ho eseguito `colcon build`
- [ ] Ho sourceto il nuovo setup: `source install/setup.bash`
- [ ] Ho testato la funzionalità
- [ ] Ho controllato i log per errori
- [ ] Ho documentato la modifica (commento nel codice)
- [ ] Ho fatto commit delle modifiche (se usi git)

---

## Contatti e Riferimenti

- **Responsabile Progetto**: Università di Palermo
- **Repository**: https://github.com/ale-gia/MHARA_Unipa
- **Branch Principale**: `main`

---

## Cronologia Modifiche

| Data | Autore | Modifica |
|------|--------|----------|
| 2026-01-29 | Alessandro Giambanco | Creazione documentazione iniziale |

---

**Ultima Aggiornamento**: 2026-01-29
**Versione Documentazione**: 1.0

