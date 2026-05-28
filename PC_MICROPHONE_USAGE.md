# Utilizzo del Microfono PC vs Pepper

## Modo Rapido: Variabile d'Ambiente

Scegli la sorgente audio impostando la variabile d'ambiente `AUDIO_SOURCE` prima di lanciare il sistema.

### Usare il Microfono del PC

```bash
export AUDIO_SOURCE=pc
ros2 launch my_robot_controller peppercontroller.launch.py
```

### Usare il Microfono di Pepper (Default)

```bash
export AUDIO_SOURCE=pepper
ros2 launch my_robot_controller peppercontroller.launch.py
```

O semplicemente (usa Pepper di default):

```bash
ros2 launch my_robot_controller peppercontroller.launch.py
```

## Configurazione Aggiuntiva per PC Microphone

Se usi il PC microphone, puoi configurare ulteriormente:

### 1. Durata della Registrazione

Controlla per quanti secondi registrare:

```bash
export AUDIO_SOURCE=pc
export PC_AUDIO_DURATION=10
ros2 launch my_robot_controller peppercontroller.launch.py
```

**Valori consigliati:**
- `5` secondi: veloce, per test
- `10` secondi: standard
- `15` secondi: per conversazioni più lunghe

### 2. Rilevamento Automatico del Silenzio

Per interrompere automaticamente la registrazione quando il silenzio è rilevato:

```bash
export AUDIO_SOURCE=pc
export PC_AUDIO_DETECTION=true
export PC_AUDIO_DURATION=30
ros2 launch my_robot_controller peppercontroller.launch.py
```

**Note:**
- Quando `PC_AUDIO_DETECTION=true`, il sistema attende il silenzio per interrompere
- Comunque non supera la durata massima specificata in `PC_AUDIO_DURATION`
- È più "intelligente" ma meno affidabile del tempo fisso

### 3. Combinare Tutte le Impostazioni

```bash
#!/bin/bash

# Configurazione completa
export AUDIO_SOURCE=pc              # Usa PC microphone
export PC_AUDIO_DURATION=8          # Registra max 8 secondi
export PC_AUDIO_DETECTION=false     # Usa tempo fisso (più affidabile)

# Avvia il sistema
ros2 launch my_robot_controller peppercontroller.launch.py
```

## Log e Diagnostica

Quando il sistema si avvia, vedrai un messaggio come:

```
[pepper_controller-1] 🎙 Sorgente audio: Microfono PC
```

o

```
[pepper_controller-1] 🎙 Sorgente audio: Microfono Pepper
```

Per verificare quale sorgente è stata selezionata, controlla i log ROS:

```bash
# In un altro terminale, durante l'esecuzione
ros2 topic echo /rosout | grep "Sorgente audio"
```

## Troubleshooting

### Problema: "Microfono PC non funziona"

1. Verifica che il microfono del PC sia abilitato:
   ```bash
   pactl list sources | grep -A 10 "Source"
   ```

2. Verifica che sounddevice sia installato:
   ```bash
   python -c "import sounddevice; print('OK')"
   ```

3. Prova a registrare direttamente:
   ```bash
   python -c "
   from src.speech.speech.pc_microphone import get_pc_recorder
   rec = get_pc_recorder()
   rec.record_audio(duration=5)
   "
   ```

### Problema: "Audio registrato ma vuoto"

1. Aumenta la durata della registrazione:
   ```bash
   export PC_AUDIO_DURATION=10
   ```

2. Verifica il livello di input del microfono del PC (sistema -> impostazioni audio)

3. Prova con `PC_AUDIO_DETECTION=false` (tempo fisso è più affidabile)

### Problema: "Voglio tornare a Pepper"

```bash
# Deseleziona la variabile
unset AUDIO_SOURCE

# O imposta esplicitamente
export AUDIO_SOURCE=pepper

# Poi riavvia
ros2 launch my_robot_controller peppercontroller.launch.py
```

## Variabili d'Ambiente Disponibili

| Variabile | Valori | Default | Descrizione |
|-----------|--------|---------|-------------|
| `AUDIO_SOURCE` | `pc`, `pepper` | `pepper` | Sorgente audio |
| `PC_AUDIO_DURATION` | numero (secondi) | `5` | Durata max registrazione PC |
| `PC_AUDIO_DETECTION` | `true`, `false` | `false` | Rilevamento silenzio |

## Script di Lancio Rapido

Crea un file `launch_with_pc.sh`:

```bash
#!/bin/bash

export AUDIO_SOURCE=pc
export PC_AUDIO_DURATION=8
export PC_AUDIO_DETECTION=false

echo "🎙 Lancio con microfono PC..."
ros2 launch my_robot_controller peppercontroller.launch.py
```

Poi usa:

```bash
chmod +x launch_with_pc.sh
./launch_with_pc.sh
```

## Best Practice

### Per Sviluppo/Testing

```bash
export AUDIO_SOURCE=pc
export PC_AUDIO_DURATION=5
export PC_AUDIO_DETECTION=false
```

### Per Deployment con Pepper

```bash
export AUDIO_SOURCE=pepper
# o semplicemente non impostare nulla
```

### Per Test di Entrambi

```bash
# Test 1: Pepper
ros2 launch my_robot_controller peppercontroller.launch.py

# Ctrl+C e poi...

# Test 2: PC
export AUDIO_SOURCE=pc
ros2 launch my_robot_controller peppercontroller.launch.py
```

---

**Nota:** Le modifiche sono completamente configurabili via variabili d'ambiente. Non è necessario modificare il codice.
