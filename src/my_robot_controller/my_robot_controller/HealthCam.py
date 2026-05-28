import base64
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from langchain_openai import ChatOpenAI
import ollama
from datetime import datetime,timedelta
import json
from pathlib import Path
from .token_logger import get_token_logger

class HealthCam:
    def __init__(self, provider="openai", model=None, user_id="default_user"):
        self.image_path = os.path.expanduser("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/src/camera/")
        self.provider = provider
        self.user_id = user_id
        self.token_logger = get_token_logger()
        
        # Setup directory per salvare i dati
        self.data_dir = Path("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/data/health_monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurazione del modello basata sul provider
        if provider == "groq":
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        elif provider == "openai":
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
 
        elif provider == "ollama":
            self.ollama_model = "moondream:1.8b"
            self.llm = None
        else:
            raise ValueError(f"Provider non supportato: {provider}")
        
        # Esempi di analisi positive e negative
        self.positive_example = """
        POSTURA: La persona è seduta con la schiena dritta e ben supportata, le spalle sono rilassate.
        MOBILITÀ: La persona mostra una buona capacità di movimento, è in piedi e attiva.
        AMBIENTE: L'ambiente è ben illuminato, ordinato e sicuro, senza ostacoli a terra.
        STATO EMOTIVO: La persona appare serena e di buon umore.
        SEGNI DI RISCHIO: Nessun segno di particolare rischio rilevato.
        """
        
        self.negative_example = """
        POSTURA: La persona è in posizione curva, con le spalle incurvate in avanti, potenziale tensione alla schiena.
        MOBILITÀ: Movimenti limitati, la persona appare poco attiva.
        AMBIENTE: Presenza di oggetti sul pavimento che potrebbero causare cadute, illuminazione scarsa.
        STATO EMOTIVO: La persona appare stanca o affaticata.
        SEGNI DI RISCHIO: Possibile affaticamento, rischio di caduta per ostacoli, necessità di incoraggiare il movimento.
        """
        
        # Prompt specializzato per monitoraggio salute anziani
        self.health_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            Sei un assistente specializzato nel monitoraggio della salute di persone  attraverso analisi visiva.
            Analizza l'immagine fornita concentrandoti sui seguenti aspetti critici per la salute:
            
            1. POSTURA: Valuta la postura della persona (schiena dritta/curva, spalle, collo, allineamento generale)
            2. MOBILITÀ: Osserva se la persona è attiva, seduta, sdraiata, usa ausili (bastone, deambulatore)
            3. AMBIENTE: Identifica rischi di caduta (oggetti sul pavimento, scarsa illuminazione, tappeti, scale)
            4. STATO EMOTIVO: Osserva espressioni facciali che indicano benessere, stress, dolore o disagio
            5. SEGNI DI RISCHIO: Rileva qualsiasi segnale di difficoltà, affaticamento, instabilità o pericolo
            
            Fornisci una risposta strutturata in italiano, chiara e concisa, con raccomandazioni pratiche se necessario.
            
            Esempi di risposta:
            Esempio positivo: {self.positive_example}
            Esempio negativo: {self.negative_example}
            """),
            ("user", [
                {
                    "type": "text",
                    "text": "Analizza questa immagine per monitorare la salute e il benessere della persona . Contesto: {{context}}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,{image_data}"
                    }
                }
            ])
        ])

    def _load_image_as_base64(self) -> str:
        self.image_path_ = os.path.join(self.image_path, "image.jpeg")
        with open(self.image_path_, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_with_ollama(self, context=""):
        """Metodo specifico per usare Ollama direttamente"""
        system_prompt = f"""
        Analizza l'immagine fornita concentrandoti sulla salute di persone :
        
        1. POSTURA: Valuta la postura della persona
        2. MOBILITÀ: Osserva il livello di attività
        3. SEDENTARIETÀ: Cerca segni di inattività prolungata
        4. AMBIENTE: Identifica rischi di caduta
        5. STATO EMOTIVO: Osserva benessere o disagio
        6. SEGNI DI RISCHIO: Rileva segnali di difficoltà
        
        Rispondi in italiano in modo strutturato.
        
        Esempi:
        Positivo: {self.positive_example}
        Negativo: {self.negative_example}
        
        Contesto: {context}
        """
        
        response = ollama.chat(
            model=self.ollama_model,
            messages=[{
                'role': 'user',
                'content': system_prompt + "\n\nAnalizza questa immagine per il monitoraggio della salute.",
                'images': [self.image_path_]
            }]
        )
        
        # Ollama è locale, non loghiamo costi
        return response['message']['content']

    def create_health_chain(self):
        """Metodo per provider LangChain"""
        if self.provider == "ollama":
            raise ValueError("Per Ollama usa il metodo analyze_with_ollama() direttamente")
            
        def prepare_inputs(context):
            return {
                "image_data": self._load_image_as_base64(),
                "context": context
            }
        
        chain = RunnableLambda(prepare_inputs) | self.health_prompt | self.llm
        
        # Wrap chain to log token usage
        def chain_with_logging(context):
            result = chain.invoke(context)
            
            # Log token usage
            if hasattr(result, 'response_metadata'):
                metadata = result.response_metadata
                if 'usage' in metadata:
                    usage = metadata['usage']
                    self.token_logger.log_token_usage(
                        model="gpt-4o-mini" if self.provider == "openai" else "llama-3.3-70b-versatile",
                        input_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('completion_tokens', 0),
                        source="HealthCam",
                        metadata={"user_id": self.user_id, "context": context[:50] if context else ""}
                    )
            
            return result
        
        return chain_with_logging

    def _parse_analysis(self, analysis_text):
        """Estrae informazioni strutturate dall'analisi testuale"""
        data = {
            "postura": "",
            "mobilita": "",
            "sedentarieta": "",
            "ambiente": "",
            "stato_emotivo": "",
            "segni_rischio": "",
            "analisi_completa": analysis_text
        }
        
        # Parsing semplice per estrarre le sezioni
        sections = ["POSTURA:", "MOBILITÀ:", "SEDENTARIETÀ:", "AMBIENTE:", "STATO EMOTIVO:", "SEGNI DI RISCHIO:"]
        for i, section in enumerate(sections):
            if section in analysis_text:
                start = analysis_text.find(section) + len(section)
                if i < len(sections) - 1:
                    end = analysis_text.find(sections[i+1])
                    if end == -1:
                        end = len(analysis_text)
                else:
                    end = len(analysis_text)
                
                key = section.replace(":", "").replace("À", "A").lower()
                if key == "mobilita":
                    data["mobilita"] = analysis_text[start:end].strip()
                elif key == "sedentarieta":
                    data["sedentarieta"] = analysis_text[start:end].strip()
                else:
                    data[key.replace(" ", "_")] = analysis_text[start:end].strip()
        
        return data

    def save_analysis(self, analysis_text, context=""):
        """Salva l'analisi in formato JSON con timestamp"""
        timestamp = datetime.now()
        
        # Parsing dei dati strutturati
        parsed_data = self._parse_analysis(analysis_text)
        
        # Crea il record completo
        record = {
            "timestamp": timestamp.isoformat(),
            "user_id": self.user_id,
            "context": context,
            "provider": self.provider,
            **parsed_data
        }
        
        # Salva in file JSON giornaliero
        daily_file = self.data_dir / f"{self.user_id}_{timestamp.strftime('%Y-%m-%d')}.json"
        
        # Carica i dati esistenti o crea una nuova lista
        if daily_file.exists():
            with open(daily_file, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
        else:
            daily_data = []
        
        daily_data.append(record)
        
        # Salva i dati aggiornati
        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)
        
        # Salva anche in un file di log continuo
        log_file = self.data_dir / f"{self.user_id}_continuous.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"Analisi salvata in: {daily_file}", flush=True)
        return daily_file

    def analyze_image(self, context="", save=True):
        """Metodo unificato per analizzare l'immagine e salvare i risultati"""
        if self.provider == "ollama":
            print("Analizzando immagine per monitoraggio salute...", flush=True)
            analysis = self.analyze_with_ollama(context)
        else:
            chain = self.create_health_chain()
            response = chain.invoke(context)
            analysis = response.content if hasattr(response, 'content') else str(response)
        
        # Salva l'analisi se richiesto
        if save:
            self.save_analysis(analysis, context)
        
        return analysis

    def get_daily_summary(self, date=None):
        """Recupera il riepilogo delle analisi di una giornata specifica"""
        if date is None:
            date = datetime.now()
        
        daily_file = self.data_dir / f"{self.user_id}_{date.strftime('%Y-%m-%d')}.json"
        
        if not daily_file.exists():
            return None
        
        with open(daily_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_health_trends(self, days=7):
        """Analizza i trend di salute negli ultimi N giorni"""
        trends = []
        current_date = datetime.now()
        
        for i in range(days):
            date = current_date- timedelta(days=days)
            daily_data = self.get_daily_summary(date)
            if daily_data:
                trends.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "num_analyses": len(daily_data),
                    "data": daily_data
                })
        
        return trends

    def generate_health_advice(self, recent_analyses, llm_chain=None):
            """
            Genera consigli personalizzati basati sulle analisi recenti
            
            Args:
                recent_analyses: Lista delle analisi recenti (ultime ore/giorni)
                llm_chain: Chain LLM per generare il consiglio (opzionale)
            
            Returns:
                str: Consiglio personalizzato per l'anziano
            """
            if not recent_analyses:
                return "Non ci sono analisi recenti disponibili per generare consigli."
            
            # Prepara il contesto dalle analisi recenti
            context = self._prepare_context_from_analyses(recent_analyses)
            
            if llm_chain:
                
                response = llm_chain.invoke({"input": context})
                #return response.content if hasattr(response, 'content') else str(response)
                #return response.output if hasattr(response, 'output') else str(response)
                return response.get('output', '')
            else:
                # Generazione consiglio basato su regole
                return self._generate_rule_based_advice(recent_analyses)
        
    def _prepare_context_from_analyses(self, analyses):
        """Prepara un riassunto delle analisi per il prompt"""
        if not analyses:
            return "Nessuna analisi disponibile"
        
        context_parts = []
        for i, analysis in enumerate(analyses[-5:], 1):  # Ultime 5 analisi  print(f"recent analysis : {analysis}",flush=True)
            timestamp = analysis.get('timestamp', 'N/A')
            context_parts.append(f"\nAnalisi {i} ({timestamp}):")
            context_parts.append(f"- Postura: {analysis.get('postura', 'N/A')[:100]}")
            context_parts.append(f"- Mobilità: {analysis.get('mobilita', 'N/A')[:100]}")
            context_parts.append(f"- Sedentarietà: {analysis.get('sedentarieta', 'N/A')[:100]}")
            context_parts.append(f"- Ambiente: {analysis.get('ambiente', 'N/A')[:100]}")
            context_parts.append(f"- Stato emotivo: {analysis.get('stato_emotivo', 'N/A')[:100]}")
            context_parts.append(f"- Rischi: {analysis.get('segni_rischio', 'N/A')[:100]}")
        
        return "\n".join(context_parts)
    
    def _generate_rule_based_advice(self, analyses):
        """Genera consigli basati su regole semplici"""
        latest = analyses[-1] if analyses else {}
        
        postura = latest.get('postura', '').lower()
        mobilita = latest.get('mobilita', '').lower()
        sedentarieta = latest.get('sedentarieta', '').lower()
        rischi = latest.get('segni_rischio', '').lower()
        
        advice = []
        
        # Valutazione postura
        if 'curva' in postura or 'incurvat' in postura:
            advice.append("Ho notato che la tua postura potrebbe essere migliorata. Prova a raddrizzare delicatamente la schiena e rilassare le spalle.")
        
        # Valutazione sedentarietà
        if 'sedat' in sedentarieta or 'inattiv' in sedentarieta or 'prolungat' in sedentarieta:
            advice.append("Sei rimasto seduto per un po'. Che ne dici di fare una piccola passeggiata o alcuni semplici esercizi di stretching?")
        
        # Valutazione mobilità
        if 'limitat' in mobilita or 'poco attiv' in mobilita:
            advice.append("Ti vedo poco attivo. Anche piccoli movimenti possono fare la differenza per il tuo benessere.")
        
        # Valutazione rischi
        if 'caduta' in rischi or 'ostacol' in rischi:
            advice.append("Attenzione! Ho notato alcuni potenziali rischi nell'ambiente. Assicurati che il percorso sia libero da ostacoli.")
        
        if 'affaticat' in rischi or 'stanc' in rischi:
            advice.append("Sembri affaticato. È importante riposare quando il corpo lo richiede.")
        
        # Consiglio predefinito
        if not advice:
            advice.append("Tutto sembra andare bene! Continua così e ricorda di mantenerti attivo durante la giornata.")
        
        return " ".join(advice)
    
    def get_recent_analyses(self, hours=2):
        """Recupera le analisi delle ultime N ore"""
       
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Carica file del giorno corrente
        daily_data = self.get_daily_summary()
        if not daily_data:
            return []
        
        # Filtra per timestamp recente
        recent = []
        for analysis in daily_data:
            timestamp_str = analysis.get('timestamp', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp >= cutoff_time:
                  
                    recent.append(analysis)
            except ValueError:
                continue
        
        return recent