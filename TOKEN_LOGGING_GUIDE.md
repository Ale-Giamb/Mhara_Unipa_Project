# Token Logging System - Guida Completa

## 📋 Overview

Sistema **automatico** che traccia il consumo di token e i costi per tutti i modelli LLM utilizzati nel progetto MHARA.

---

## 🎯 Quick Start (1 minuto)

### Riepilogo Costi
```bash
cd src/my_robot_controller/my_robot_controller
python token_analysis.py
```

### Monitor Tempo Reale
```bash
python token_monitor.py
```

### Test Sistema
```bash
python test_token_logger.py
```

---

## 📁 Struttura File

```
MHARA_Unipa/
├── TOKEN_LOGGING_GUIDE.md              ← Questo file (guida unica)
├── src/my_robot_controller/my_robot_controller/
│   ├── token_logger.py                 ← Core del sistema
│   ├── token_analysis.py               ← Visualizzazione dati
│   ├── token_monitor.py                ← Monitor live
│   ├── token_report_generator.py       ← Generazione rapporti
│   ├── test_token_logger.py            ← Test suite
│   ├── Agent.py                        ← Integrato ✓
│   ├── LLMSummary.py                   ← Integrato ✓
│   ├── Cam_llm.py                      ← Integrato ✓
│   └── HealthCam.py                    ← Integrato ✓
└── data/token_logs/
    ├── token_usage.json                ← Log dettagliati (auto-creato)
    └── token_logger.log                ← Log Python (auto-creato)
```

---

## 💰 Modelli e Prezzi

| Modello | Input | Output | Fonte |
|---------|-------|--------|-------|
| gpt-4o-mini | $0.00015/1K | $0.0006/1K | OpenAI |
| gpt-4o | $0.005/1K | $0.015/1K | OpenAI |
| gpt-4-turbo | $0.01/1K | $0.03/1K | OpenAI |
| llama-3.3-70b | $0.00005/1K | $0.0001/1K | Groq |
| moondream | Gratuito | Gratuito | Ollama (locale) |

---

## 🔧 Comandi Principali

### 1. Visualizzare Riepilogo
```bash
python token_analysis.py
```
**Output:** Totali, per modello, per sorgente, statistiche

### 2. Log Dettagliati (Ultimi N)
```bash
python token_analysis.py --detailed --limit 10
```
**Output:** Tabella con timestamp, modello, tokens, costo

### 3. Filtro Temporale
```bash
python token_analysis.py --days 7
```
**Output:** Solo dati degli ultimi 7 giorni

### 4. Monitor Tempo Reale
```bash
python token_monitor.py
```
**Output:** Dashboard auto-aggiornato ogni 10 secondi

### 5. Esportare CSV
```bash
python token_analysis.py --export-csv costs.csv
```
**Output:** File CSV per Excel/Pandas

### 6. Generare Rapporti
```bash
# Testo
python token_report_generator.py --text

# HTML (formattato)
python token_report_generator.py --html report.html

# JSON (dati grezzi)
python token_report_generator.py --json report.json
```

---

## 🤖 Come Funziona

### Automatico - Niente da Configurare

Il logging è **completamente automatico** negli Agent principali:

```python
# Agent.py - Logging automatico ✓
result = agent.invoke("Ciao!")  # Token loggati automaticamente

# LLMSummary.py - Logging automatico ✓
chain = llm_sum.create_summary_chain()  # Token loggati automaticamente

# Cam_llm.py - Logging automatico ✓
camera = CamLLM()
result = camera.analyze_image(context)  # Token loggati automaticamente

# HealthCam.py - Logging automatico ✓
health = HealthCam(user_id="elderly_001")
result = health.analyze_health()  # Token loggati con user_id
```

### Accesso Programmativo

```python
from my_robot_controller.token_logger import get_token_logger

logger = get_token_logger()

# Riepilogo completo
summary = logger.get_summary()
print(f"Costo totale: ${summary['total_cost']:.8f}")
print(f"Token totali: {summary['total_tokens']:,}")
print(f"Richieste: {summary['total_entries']}")

# Per modello
for model, stats in summary['by_model'].items():
    print(f"{model}: {stats['count']} richieste, ${stats['total_cost']:.8f}")

# Per sorgente
for source, stats in summary['by_source'].items():
    print(f"{source}: {stats['count']} richieste, ${stats['total_cost']:.8f}")


logger.print_summary()
```

---

## 📊 Formato Dati

### Log JSON - `data/token_logs/token_usage.json`

```json
{
  "last_updated": "2025-01-26T15:30:45.123456",
  "usage_logs": [
    {
      "timestamp": "2025-01-26T15:30:40.123456",
      "model": "gpt-4o-mini",
      "source": "Agent",
      "input_tokens": 150,
      "output_tokens": 250,
      "total_tokens": 400,
      "input_cost": 0.0000225,
      "output_cost": 0.00015,
      "total_cost": 0.0001725,
      "metadata": {
        "thread_id": "user123",
        "input_preview": "Ciao, come stai?"
      }
    }
  ]
}
```

### Riepilogo - `summary['by_model']`

```python
{
    "gpt-4o-mini": {
        "count": 35,                    # Numero richieste
        "input_tokens": 8500,
        "output_tokens": 6200,
        "total_tokens": 14700,
        "total_cost": 0.00810275
    }
}
```

---

## 🐍 API - Utilizzo Programmativo

### Logging Manuale

```python
from my_robot_controller.token_logger import TokenLogger

logger = TokenLogger()

# Log una richiesta
logger.log_token_usage(
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
    source="MyCustomSource",
    metadata={"user_id": "alice", "task": "summarize"}
)
```

### Log da Risposta LLM

```python
from langchain_openai import ChatOpenAI
from my_robot_controller.token_logger import get_token_logger

llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("Hello")

logger = get_token_logger()
logger.log_from_response(response, model="gpt-4o-mini", source="CustomLLM")
```

### Recuperare Statistiche

```python
logger = get_token_logger()
summary = logger.get_summary()

# Totali
total_cost = summary['total_cost']
total_tokens = summary['total_tokens']
total_requests = summary['total_entries']

# Per modello
model_stats = summary['by_model']['gpt-4o-mini']
print(f"gpt-4o-mini: {model_stats['count']} requests, ${model_stats['total_cost']:.8f}")

# Per sorgente
source_stats = summary['by_source']['Agent']
print(f"Agent: {source_stats['count']} requests, ${source_stats['total_cost']:.8f}")
```

### Salvare Riepilogo

```python
logger.save_summary_to_file("monthly_report.json")
logger.print_summary()
```

---

## 📈 Esempi Pratici

### Scenario 1: Costo per Utente

```python
from my_robot_controller.token_logger import get_token_logger

logger = get_token_logger()

# Log con user_id nel metadata
logger.log_token_usage(
    model="gpt-4o-mini",
    input_tokens=100,
    output_tokens=50,
    source="Agent",
    metadata={"user_id": "alice"}
)

# Calcolare costo totale per Alice
alice_cost = sum(
    log['total_cost'] for log in logger.usage_data
    if log.get('metadata', {}).get('user_id') == 'alice'
)
print(f"Costo Alice: ${alice_cost:.8f}")
```

### Scenario 2: Analisi con Pandas

```python
import pandas as pd
import json

# Caricare dati
with open('data/token_logs/token_usage.json') as f:
    data = json.load(f)

df = pd.DataFrame(data['usage_logs'])

# Analisi
print(df.groupby('model')['total_cost'].sum())
print(df.groupby('source')['total_tokens'].sum())
print(df.groupby('source').size())  # Richieste per sorgente
```

### Scenario 3: Rapporto Mensile

```python
from my_robot_controller.token_report_generator import ReportGenerator
from pathlib import Path

gen = ReportGenerator(Path("data/token_logs/token_usage.json"))

# Generare rapporti
gen.generate_html_report(Path("report_january.html"))
gen.generate_json_report()
gen.print_dashboard(gen._calculate_stats())
```

---

## ⚙️ Configurazione

### Aggiornare Prezzi

**File:** `token_logger.py` (linee 20-40)

```python
class TokenCostConfig:
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.00015,   # ← Modifica qui
            "output": 0.0006,   # ← Modifica qui
        },
        # Aggiungi altri modelli
    }
```

Salva e i nuovi prezzi si applicheranno ai futuri log.

### Cambiar Directory Log

```python
from my_robot_controller.token_logger import TokenLogger

# Directory custom
logger = TokenLogger(log_dir="/custom/path/logs")
```

---

## 🧪 Test del Sistema

```bash
python test_token_logger.py
```

Output atteso:
```
================================================================================
TOKEN LOGGER TEST SUITE
================================================================================

✓ Token logger initialized
✓ Request logged successfully
✓ Logged 3 requests
✓ Summary retrieved successfully
✓ Model grouping verified
✓ Source grouping verified
✓ Pricing configuration verified
✓ Summary saved to test_summary.json

================================================================================
ALL TESTS COMPLETED SUCCESSFULLY!
================================================================================
```

---

## 📊 Output Esempio

### token_analysis.py
```
================================================================================
TOKEN USAGE AND COST SUMMARY
================================================================================

Report Period: 2025-01-26 to 2025-01-26
Total Entries: 42
Total Tokens: 15,240
Total Cost: $0.00845230

--------------------------------------------------------------------------------
BY MODEL:
--------------------------------------------------------------------------------

gpt-4o-mini:
  Requests: 35
  Input Tokens: 8,500
  Output Tokens: 6,200
  Total Tokens: 14,700
  Total Cost: $0.00810275
```

### token_monitor.py
```
================================================================================
TOKEN USAGE MONITOR - 2025-01-26 14:30:00
================================================================================

Total Requests: 42                 Total Tokens: 15,240
Total Cost:     $0.00845230

MODEL                          REQ      TOKENS          COST
------------------------------------------------------------------------
gpt-4o-mini                    35       14,700          $0.00810275
llama-3.3-70b-versatile        7        540             $0.00034955
```

---

## 🆘 Troubleshooting

### File Log Non Creato
```bash
# Creare directory
mkdir -p data/token_logs
chmod 755 data/token_logs
```

### Costi Zero
Verificare che il modello sia in `TokenCostConfig.PRICING` in `token_logger.py`

### Resettare Log
```bash
rm data/token_logs/token_usage.json
# Ricrea il file da zero al prossimo log
```

### Debug
```python
from my_robot_controller.token_logger import get_token_logger
logger = get_token_logger()
print(f"Log file: {logger.log_file}")
print(f"Log dir: {logger.log_dir}")
print(f"Entries: {len(logger.usage_data)}")
```

---

## 📚 File Moduli

### token_logger.py (12 KB)
**Core del sistema**
- `TokenCostConfig`: Configurazione prezzi
- `TokenLogger`: Logger principale
- `get_token_logger()`: Istanza globale

### token_analysis.py (8 KB)
**Visualizzazione e analisi**
- Riepilogo statistico
- Log dettagliati
- Export CSV
- Filtri temporali

### token_monitor.py (5.7 KB)
**Monitor in tempo reale**
- Dashboard auto-aggiornato
- Filtri customizzabili
- Visualizzazione per modello/sorgente

### token_report_generator.py (13 KB)
**Generazione rapporti**
- Rapporto testo
- Rapporto HTML formattato
- Rapporto JSON
- Statistiche dettagliate

### test_token_logger.py
**Test suite completa**
- Verifica logging
- Test statistiche
- Test configurazione prezzi
- Salvataggio summary

---

## ✨ Features

- ✅ Logging automatico (zero config)
- ✅ Calcolo costi in tempo reale
- ✅ Tracking per modello e sorgente
- ✅ Export CSV/JSON/HTML
- ✅ Monitor tempo reale
- ✅ Per-user tracking (metadata)
- ✅ Thread-safe
- ✅ Non-bloccante
- ✅ 5 modelli preconfigurati
- ✅ Facilmente estensibile

---

## 🚀 Quickstart Checklist

- [ ] Eseguire test: `python test_token_logger.py`
- [ ] Verificare riepilogo: `python token_analysis.py`
- [ ] Monitor tempo reale: `python token_monitor.py`
- [ ] Generare HTML: `python token_report_generator.py --html report.html`
- [ ] Esportare CSV: `python token_analysis.py --export-csv costs.csv`

---

## 📞 Info

- **Repo:** MHARA_Unipa (ale-gia)
- **Branch:** main
- **Creato:** Gennaio 2026
- **Python:** 3.8+
- **Status:** ✅ Pronto per l'uso

---

## 🎓 Approfondimenti

### Come Funziona Internamente?

1. **Ogni LLM** produce `response_metadata` con usage info
2. **TokenLogger** cattura input/output tokens
3. **Prezzi** vengono calcolati automaticamente
4. **JSON file** è aggiornato in tempo reale
5. **Tools** leggono il JSON per statistiche

### Perché è Utile?

- **Monitoraggio Costi:** Traccia spese per ogni modello
- **Ottimizzazione:** Identifica modelli più costosi
- **Billing:** Dati per fatturazione utenti/cliente
- **Debugging:** Analizza token usage per richiesta
- **Reporting:** Rapporti automatici periodici

### Non Impatta Performance?

- ✅ Logging è **asincrono**
- ✅ Non blocca l'esecuzione
- ✅ Scrittura file ottimizzata
- ✅ Overhead minimo (<1%)

---

**Ultimo aggiornamento:** Gennaio 2026 | **Versione:** 1.0
