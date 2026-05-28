import rclpy
import time
from rclpy.node import Node
from std_msgs.msg import Bool,String
from .shared import memory
from .Agent import Agent
from .LLMSummary import LLMSummary
from .Cam_llm import CamLLM
from .HealthCam import HealthCam  
from .tools import graph

import logging
logging.getLogger("langchain").setLevel(logging.WARNING)
from .update_kg import Update_Kg
import json

import os
from datetime import datetime
import random
import threading
from datetime import datetime,timedelta

# Configurazione audio da variabile d'ambiente
try:
    from .audio_config import AudioConfig, AudioSource
    HAS_AUDIO_CONFIG = True
    
    # Leggi la sorgente audio dalla variabile d'ambiente
    audio_source = os.getenv("AUDIO_SOURCE", "pepper").lower()
    if audio_source == "pc":
        AudioConfig.to_pc()
    else:
        AudioConfig.to_pepper()
except ImportError:
    HAS_AUDIO_CONFIG = False

class Pepper_Controller(Node):
    def __init__(self):
        super().__init__("pepper_controller")
        
        # Log della sorgente audio configurata
        if HAS_AUDIO_CONFIG:
            config = AudioConfig()
            self.get_logger().info(f"🎙 Sorgente audio: {config.get_source_name()}")
        
        # Publisher
        self.record_pub =self.create_publisher(Bool,"/record",10)
        self.record_no_mic_pub = self.create_publisher(Bool,"/record_no_mic",10)
        self.speak_pub=self.create_publisher(String,"/speak",10)
        self.show_pub=self.create_publisher(String,"/show",10)
        self.hide_pub=self.create_publisher(Bool,"/hide",10)
        self.bridge_pub = self.create_publisher(String, '/to_bdi', 10)
        self.invia_a_test = self.create_publisher(String, '/test', 10)
        self.camera_pub = self.create_publisher(Bool, '/get_camera', 10)
        self.ending_pub = self.create_publisher(Bool, '/end', 10)
        self.start_bdi_pub=self.create_publisher(Bool,'/start_bdi',10)

        # Subscriber
        self.transcription_sub = self.create_subscription(String, "/transcription", self.transcription_callback, 10)
        self.isSpeaking_bdi_sub = self.create_subscription(Bool, "/is_speaking_bdi",self.is_speaking_callback,10)
        self.isSpeaking_sub = self.create_subscription(Bool, "/is_speaking",self.check_speaking,10)
        self.start_conv_sub=self.create_subscription(Bool,"/start_conv",self.start_conversation,10)
        self.user_sub=self.create_subscription(String,"/user_update",self.update_user,10)
        self.bridge_sub = self.create_subscription(String, '/to_ros', self.spedisci_a_nodo, 10)
        self.transcription_bdi_sub = self.create_subscription(String, "/transcription_bdi", self.transcription_bdi_callback, 10)
        self.db_sub = self.create_subscription(String, "/query_al_db", self.query_al_db, 10)
        self.consiglia_esercizio_sub = self.create_subscription(String, "/consiglia_esercizio", self.consiglia_esercizio, 10)
        self.touched=self.create_subscription(Bool, "/touched", self.set_start, 10)
        

        # Publisher Go2 (opzionali - il sistema funziona senza Go2)
        try:
            self.go2_action_pub = self.create_publisher(String, 'go2/action', 10)
            self.go2_audio_play_pub = self.create_publisher(String, 'go2/audio/play', 10)
            self.go2_audio_speak_pub = self.create_publisher(String, 'go2/audio/speak', 10)
            self.go2_camera_pub = self.create_publisher(Bool, 'go2/camera', 10)
            self.has_go2 = True
        except Exception as e:
            self.get_logger().warn(f"Go2 publisher non disponibili: {e}. Sistema continuerà senza Go2.")
            self.has_go2 = False
            self.go2_action_pub = None
            self.go2_audio_play_pub = None
            self.go2_audio_speak_pub = None
            self.go2_camera_pub = None


        # Configurazione modelli e tools
        self.agent=Agent()
        self.health_agent=Agent(1)
        llm_sum=LLMSummary()
        self.Up_Kg=Update_Kg()
        self.Cam=CamLLM(provider="openai")
        
        # Inizializzazione HealthCam per monitoraggio periodico
        self.health_cam = HealthCam(provider="openai", user_id="elderly_patient_001")
        
        self.agent_executor=self.agent.create_agent_executor()
        self.healt_agent_executor=self.health_agent.create_agent_executor()
        
        # Sincronizza il thread_id tra Agent e memoria condivisa
        # Questo assicura che la memoria sia sempre accessibile all'agente
        memory.set_thread_id(self.agent.thread_id)
        
        self.summary_chain=llm_sum.create_summary_chain()
        
        # Inizializzazione variabili
        self.latest_response = ""
        self.is_speaking_bool = False
        self.deve_rispondere = False
        self.user_input=""
        self.start=True
        
        # Variabili per monitoraggio periodico
        self.monitoring_active = False
        self.monitoring_interval = 360 # 6 minuti 
        self.monitoring_thread = None
        self.last_advice_time = None
        
        # Lista circolare 
        self.len_pos=60 # circa 5 minuti di monitoraggio
        self.pos_dict={'In piedi':0, 'Seduto':1, 'Sdraiato':2}
        
        self.insert_pos=0
        self.history_position=[None]*self.len_pos
      
        # Avvia il monitoraggio periodico automaticamente
        self.start_periodic_monitoring()


   
                                   
    def get_go2_intro_phrases(self):
        """Genera frasi introduttive per le analisi del Go2"""
        intro_phrases = [
            "Il Go2 ha terminato l'analisi dell'ambiente e ha qualcosa da condividere con te. ",
            "Ho ricevuto un'analisi interessante dal Go2, ascolta cosa mi comunica. ",
            "Il robot Go2 ha osservato l'ambiente e vorrebbe darti questi suggerimenti. ",
            "Il Go2 ha completato la scansione e ha scoperto qualcosa di importante. ",
            "Ho ricevuto un rapporto dal Go2 sulla situazione ambientale. ",
            "Il robot Go2 ha terminato le sue osservazioni e ti comunica quanto segue. ",
            "Interessante! Il Go2 ha analizzato tutto e vorrei condividere i risultati con te. ",
            "Il Go2 ha notato alcuni dettagli che penso ti interesseranno. ",
            "Ho appena ricevuto il resoconto dal Go2 riguardo l'ambiente. ",
            "Il robot Go2 ha completato la sua analisi e ha dei dati interessanti da comunicarti. "
        ]
        return random.choice(intro_phrases)
    
    def go2_analysis(self):
        """Riceve analisi/osservazioni dal robot Go2 e le comunica tramite Pepper"""
        self.get_logger().info(f"[GO2] Analisi ")
        
        # Genera una frase introduttiva
        intro_phrase = self.get_go2_intro_phrases()
        
        # Combina introduzione + analisi del Go2
        full_message = intro_phrase 
        
        # Pubblica il messaggio tramite Pepper
        response_msg = String()
        response_msg.data = full_message
        self.speak_pub.publish(response_msg)
        
        self.get_logger().info(f"[PEPPER] Comunicazione analisi Go2: {full_message}")
    
    
    
    def go2_action(self, action: str):
        """Invia comando azione al Go2 (stand_up, stand_down, stop, sit)"""
        if not self.has_go2:
            self.get_logger().warn("Go2 non disponibile. Comando azione ignorato.")
            return
        msg = String()
        msg.data = action.lower()
        self.go2_action_pub.publish(msg)
        self.get_logger().info(f"[GO2] Azione: {action}")
    
    def go2_play_audio(self, filename: str):
        """Riproduce un file audio sul Go2"""
        if not self.has_go2:
            self.get_logger().warn("Go2 non disponibile. Audio ignorato.")
            return
        msg = String()
        msg.data = filename
        self.go2_audio_play_pub.publish(msg)
        self.get_logger().info(f"[GO2] Riproduzione audio: {filename}")
    
    def go2_speak(self, text: str):
        """Sintetizza e riproduce testo con TTS sul Go2"""
        if not self.has_go2:
            self.get_logger().warn("Go2 non disponibile. Testo non sintetizzato.")
            return
        msg = String()
        msg.data = text
        self.go2_audio_speak_pub.publish(msg)
        self.get_logger().info(f"[GO2] Sintesi vocale: {text}")
    
    def go2_request_camera(self):
        """Richiede un frame dalla camera del Go2"""
        if not self.has_go2:
            self.get_logger().warn("Go2 non disponibile. Richiesta camera ignorata.")
            return
        msg = Bool()
        msg.data = True
        self.go2_camera_pub.publish(msg)
        self.get_logger().info("[GO2] Richiesta frame camera")
    
    def go2_stand_up(self):
        """Alza il robot Go2"""
        self.go2_action("stand_up")
    
    def go2_stand_down(self):
        """Siede il robot Go2"""
        self.go2_action("stand_down")
    
    def go2_stop(self):
        """Ferma il movimento del Go2"""
        self.go2_action("stop")
    
    def go2_sit(self):
        """Siede il robot Go2"""
        self.go2_action("sit")
    
    def start_periodic_monitoring(self):
        """Avvia il monitoraggio periodico della salute"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.get_logger().info(f"✓ Monitoraggio periodico della salute avviato (ogni {self.monitoring_interval}s)")

    def stop_periodic_monitoring(self):
        """Ferma il monitoraggio periodico"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.get_logger().info("✗ Monitoraggio periodico della salute fermato")

    def random_advice_sentence(self):
        sentences = [
            "Fai una breve camminata di 5-10 minuti ",
            "Fai una passeggiata dopo i pasti per favorire la digestione e rompere la sedentarietà.",
            "Fai qualche passo vicino alla finestra o al balcone.",
            "Solleva le Ginocchia Alternativamente per 2 minuti come se facessi marcia sul posto."
            "Stendi e Rilassa le Gambe (5 volte per gamba)."
        ]
        return random.choice(sentences)
    
    def _monitoring_loop(self):
        """Loop principale per il monitoraggio periodico"""
        while self.monitoring_active:
            try:
                # Attendi l'intervallo specificato
                time.sleep(self.monitoring_interval)
                
                if not self.monitoring_active:
                    break
                
                # Esegui l'analisi periodica
                self._perform_periodic_health_check()
                
            except Exception as e:
                self.get_logger().error(f"Errore nel monitoraggio periodico: {e}")

    def _perform_periodic_health_check(self):
        """Esegue un controllo periodico della salute e fornisce consigli"""
        self.get_logger().info("=" * 60)
        self.get_logger().info("🏥 INIZIO CONTROLLO PERIODICO DELLA SALUTE")
        self.get_logger().info("=" * 60)
        
        try:
            # 1. Scatta foto
            self.get_logger().info("📸 Acquisizione immagine dalla camera...")
            msg_cam = Bool()
            msg_cam.data = True
            #self.camera_pub.publish(msg_cam)
            self.go2_request_camera()
            time.sleep(4)  # Attendi acquisizione immagine
            
            # 2. Analizza immagine con HealthCam
            self.get_logger().info("🔍 Analisi dell'immagine per parametri di salute...")
            context = f"Controllo periodico automatico - {datetime.now().strftime('%H:%M')}"
            health_analysis = self.health_cam.analyze_image(context=context, save=True)
            
            self.get_logger().info("📊 Analisi completata:")
            self.get_logger().info(f"{health_analysis[:200]}...")  # Log primi 200 caratteri
            
            # 3. Recupera analisi recenti (ultima ora)
            recent_analyses = self.health_cam.get_recent_analyses(hours=1)
            self.get_logger().info(f"📁 Recuperate {len(recent_analyses)} analisi recenti")
            
            # 4. Genera consiglio personalizzato
            self.get_logger().info("💡 Generazione consiglio personalizzato...")
         

            advice_result = self.health_cam.generate_health_advice(
                recent_analyses=recent_analyses,
                llm_chain=self.healt_agent_executor 
            )
     
  

            self.get_logger().info(f"####################\nADVICE:{advice_result}") 
        
            self.get_logger().info(f"ADVICE-IN-OUT:{recent_analyses,advice_result}")
            # Log del consiglio
            self._log_health_advice(recent_analyses,advice_result)
            # 5. Comunica il consiglio solo se significativo
            if self._should_communicate_advice(advice_result, recent_analyses):
           
                self.go2_analysis()
                self._communicate_health_advice(advice_result)
                self.last_advice_time = datetime.now()
            
            self.get_logger().info("=" * 60)
            self.get_logger().info("✓ CONTROLLO PERIODICO COMPLETATO")
            self.get_logger().info("=" * 60)
            
        except Exception as e:
            self.get_logger().error(f"❌ Errore durante il controllo periodico: {e}")

    def _should_communicate_advice(self, advice, recent_analyses):
        """Determina se il consiglio deve essere comunicato all'utente"""
   
        """
        if self.last_advice_time:
           
            time_since_last = datetime.now() - self.last_advice_time
            if time_since_last < timedelta(minutes=5):
                return False
        """
        # Comunica se ci sono parole chiave critiche
        critical_keywords = ['rischio', 'caduta', 'attenzione', 'urgente', 'pericolo', 'affaticato', 'sedentario']
        advice_lower = advice.lower()
        
        for keyword in critical_keywords:
            if keyword in advice_lower:
                return True
        
        # Comunica se ci sono più di 3 analisi nelle ultime 2 ore (attività frequente)
        #if len(recent_analyses) >= 3:
           # return True
        
        # Comunica comunque ogni 3 controlli periodici (30 minuti) 
        if len(recent_analyses) % 5 == 0:
            return True
        
        return False

    def _communicate_health_advice(self, advice):
        """Comunica il consiglio all'utente tramite speech"""
        self.get_logger().info("🗣️  Comunicazione consiglio all'utente")
        
        # Prepara il messaggio con un'introduzione gentile
        intro_phrases = [
            "Ho notato qualcosa che vorrei condividere con te.",
            "Permettimi di darti un piccolo suggerimento.",
            "Ho fatto alcune osservazioni e vorrei condividere un consiglio. ",
            "Basandomi su ciò che ho osservato, vorrei suggerirti qualcosa. "
        ]
        
        full_message = random.choice(intro_phrases) + advice
        
        # Pubblica il messaggio
        msg = String()
        msg.data = full_message
        #self.speak_pub.publish(msg)
        self.go2_speak(full_message)
   

    def _log_health_advice(self, advice_in,advice_out):
        """Salva il consiglio in un file di log dedicato"""
        log_dir = os.path.expanduser("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/src/health_advice_log/")
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = os.path.join(log_dir, f"health_advice_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        log_entry = f"""
                    {'='*80}
                    CONSIGLIO SULLA SALUTE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    {'='*80}

                    Analisi:{advice_in}\n
                    Risposta:{advice_out}

                    {'='*80}

                    """
        
        try:
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            self.get_logger().info(f"📝 Consiglio salvato in: {log_filename}")
        except Exception as e:
            self.get_logger().error(f"❌ Errore nel salvare il log del consiglio: {e}")

    def transcription_callback(self, msg):
        self.user_input=msg.data.lower()
        res=String()
        if ('termina'  in self.user_input):
            res.data='È stato un piacere aiutarti. A presto!'
            self.speak_pub.publish(res)
            self.start=False
            
            # Ferma il monitoraggio quando termina la conversazione
            self.stop_periodic_monitoring()
            
            msg=Bool()
            msg.data=True
            self.ending_pub.publish(msg)
        else:
            self.conversation(res)

    def set_start(self,msg):
        self.start=msg.data
        # Riavvia il monitoraggio quando l'utente riattiva il robot
        if self.start and not self.monitoring_active:
            self.start_periodic_monitoring()
    
    def _log_conversation_to_file(self, timestamp, user_input, agent_response, 
                                intermediate_steps, summary):
        """Salva le informazioni della conversazione in un file di log formattato"""
        log_dir = os.path.expanduser("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/src/conv_log/")
        log_filename = os.path.join(log_dir, f"conversation_{datetime.now().strftime('%Y-%m-%d')}.log")
        """
                    ANALISI CAMERA:
                    {camera_analysis}"""
        
        log_entry = f"""
                    {'='*80}
                    CONVERSAZIONE DEL: {timestamp}
                    {'='*80}

                    DOMANDA UTENTE:
                    {user_input}

                    RISPOSTA AGENTE:
                    {agent_response}

                    PASSI INTERMEDI:
                    {self._format_intermediate_steps(intermediate_steps)}


                    RIASSUNTO INTERAZIONE:
                    {summary}

                    {'='*80}

                    """
        
        try:
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write(log_entry)
            self.get_logger().info(f"Conversazione salvata in: {log_filename}")
        except Exception as e:
            self.get_logger().error(f"Errore nel salvare il log: {e}")

    def _format_intermediate_steps(self, intermediate_steps):
        """Formatta i passi intermedi in modo leggibile"""
        if not intermediate_steps:
            return "Nessun passo intermedio registrato"
        
        formatted_steps = []
        for i, step in enumerate(intermediate_steps, 1):
            if isinstance(step, tuple) and len(step) >= 2:
                action, observation = step[0], step[1]
                formatted_steps.append(f"Passo {i}:")
                formatted_steps.append(f"  Azione: {action}")
                formatted_steps.append(f"  Risultato: {observation}")
                formatted_steps.append("")
            else:
                formatted_steps.append(f"Passo {i}: {step}")
                formatted_steps.append("")
        
        return "\n".join(formatted_steps)

    def conversation(self,res):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.get_logger().info(f"#############################################\nUtente: {self.user_input}")
        msg=String()
        msg.data="thinking.html"
        self.show_pub.publish(msg)
        memory_vars = memory.load_memory_variables({})
        chat_history = memory_vars.get('chat_history', [])
        
        response = self.agent_executor.invoke({
            "input": self.user_input,
            "chat_history": chat_history
        })
        
        #self.get_logger().info("\n#################\nAnalizzo camera")
        msg_cam=Bool()
        msg_cam.data=True
        #self.camera_pub.publish(msg_cam)
        #time.sleep(4)
        
        self.get_logger().info(f"Response: {response['output']}\n")
        res.data = response.get('output', '')
        intermediate_steps = response.get('intermediate_steps', [])
        self.speak_pub.publish(res)

        #cam_result=self.Cam.analyze_image(res.data)
        #self.get_logger().info("\n#################\nImmagine interpretata: "+cam_result.content+"\n#############")
        
        summary_input = {
            "response": f"""
                Risposta completa: {res.data}
                
                Passi intermedi:
                {intermediate_steps}

                
            """
        }#Analisi della risposta:{cam_result.content}
        
        summary_output = self.summary_chain.invoke(summary_input)
        summary= summary_output.content

        self.get_logger().info("\n\nRiassunto dell'interazione:")
        self.get_logger().info(summary)
        
        memory.save_context(
            {"input": self.user_input}, 
            {"output": summary}
        )
        
        msg=Bool()
        msg.data=True
        self.hide_pub.publish(msg)
        
        self._log_conversation_to_file(
            timestamp=timestamp,
            user_input=self.user_input,
            agent_response=response['output'],
            intermediate_steps=response['intermediate_steps'],
            #camera_analysis=cam_result.content,
            summary=summary
        )

    def check_speaking(self,msg):
        msg2=Bool()
        msg2.data=True
        if not msg.data and self.start:
            self.record_pub.publish(msg2)
    
    def random_conversation_sentence(self):
        sentences = [
            "Ehi! Sono qui, a disposizione. Di cosa hai bisogno oggi?",
            "Eccomi, con le mie luci LED scintillanti pronte! Procedi pure, il mio hard disk è tutto orecchi (e circuiti).",
            "Mi hai chiamato? Perfetto, ero giusto in attesa. Dimmi pure!",
            "Tutto ok, pronto ad ascoltare! Lanciami la tua richiesta.",
            "Eccomi! stomaco brontolante? chiedimi pure una ricetta adatta alle tue esigenze",
            "Heyla, come ti senti oggi?",
            "Sono in ascolto! Hai già scelto il cibo? Spero sia vegano-galattico",
            "Connesso ai dati paziente. Vuoi che trovi una scusa per il dolce?",
            "Analisi veloce: dieta o esercizio? Non farmi faticare troppo, dai!",
            "Sono io! Cosa bolle in pentola ?"
        ]
        return random.choice(sentences)
    
    def start_conversation(self,msg_in):
        
        msg=Bool()
        msg.data=True
        self.hide_pub.publish(msg)
        
        msg2=String()
        if not msg_in.data:
            msg2.data="Iniziamo... " \
                "Ricorda che posso ascoltarti solo quando i miei occhi si colorano di verde.... " \
                "Puoi chiedermi, Pepper cosa posso mangiare per cena? oppure oggi sono stanco cosa mi consigli di fare per rilassarmi? "
            msg=String()
            msg.data="attivo.html"
            self.show_pub.publish(msg)
        else:
            msg2.data=self.random_conversation_sentence()
          
        self.speak_pub.publish(msg2)

    def start_tablet(self):
        msg2=String()
        msg2.data="Ciao sono Pepper!... Gentilmente inserisci i tuoi dati nel tuo dispositivo affinchè io possa aiutarti secondo le tue esigenze "
        self.speak_pub.publish(msg2) 

        msg=String()
        msg.data="registrazione.html"
        self.show_pub.publish(msg)
        self.get_logger().info("start")
     
    def load_person_info_to_memory(self):
        """
        Carica le informazioni principali della persona da Neo4j nella memoria dell'agente
        dopo la registrazione. Consente all'agente di accedere a questi dati senza interrogare il DB.
        """
        try:
            self.get_logger().info("[MEMORY] Carico informazioni persona dal database...")
            
            # Usa Update_Kg per interrogare il database
            data = self.Up_Kg2.search_inf_callback(f"Dammi tutte le informazioni personali dell'anziano")
            
            if not data or len(data) == 0:
                self.get_logger().warn("[MEMORY] Nessun dato trovato nel database")
                return
            
            person_data = data[0]
            
            # Estrai le informazioni principali
            nome = person_data.get('nome', 'Sconosciuto')
            cognome = person_data.get('cognome', 'Sconosciuto')
            peso = person_data.get('peso', 'Non disponibile')
            altezza = person_data.get('altezza', 'Non disponibile')
            
            # Estrai patologie e intolleranze principali
            patologie = person_data.get('patologie', [])
            patologia_principale = patologie[0]['id'] if patologie and len(patologie) > 0 else 'Nessuna'
            
            intolleranze = person_data.get('intolleranze', [])
            intolleranza_principale = intolleranze[0]['id'] if intolleranze and len(intolleranze) > 0 else 'Nessuna'
            
            # Estrai parametri vitali principali
            parametri_vitali = person_data.get('parametriVitali', [])
            pressione = battito = temperatura = 'Non disponibile'
            if parametri_vitali and len(parametri_vitali) > 0:
                pv = parametri_vitali[0]
                pressione = f"{pv.get('pressioneSistolica', '?')}/{pv.get('pressioneDiastolica', '?')}"
                battito = pv.get('battitoCardiaco', 'Non disponibile')
                temperatura = pv.get('temperaturaCorporea', 'Non disponibile')
            
            # Estrai stato nutrizionale
            stato_nutrizionale = person_data.get('statoNutrizionale', [])
            stato_nut = stato_nutrizionale[0]['stato'] if stato_nutrizionale else 'Non disponibile'
            
            # Estrai stato mobilità
            stato_mobilita = person_data.get('statoMobilita', [])
            stato_mob = stato_mobilita[0]['stato'] if stato_mobilita else 'Non disponibile'
            
            # Crea un testo naturale con le informazioni principali
            person_info_text = (
                f"Informazioni della persona registrata:\n"
                f"Nome: {nome}\n"
                f"Cognome: {cognome}\n"
                f"Peso: {peso} kg\n"
                f"Altezza: {altezza} m\n"
                f"Patologia principale: {patologia_principale}\n"
                f"Intolleranza principale: {intolleranza_principale}\n"
                f"Pressione arteriosa: {pressione} mmHg\n"
                f"Battito cardiaco: {battito} bpm\n"
                f"Temperatura corporea: {temperatura}°C\n"
                f"Stato nutrizionale: {stato_nut}\n"
                f"Stato mobilità: {stato_mob}\n"
                f"\nQueste sono le informazioni principali della persona. Puoi fare riferimento a questi dati quando necessario."
            )
            
            # Salva nella memoria dell'agente
            memory.save_context(
                inputs={"input": f"Registrazione completata per {nome} {cognome}"},
                outputs={"output": person_info_text}
            )
            
            self.get_logger().info(f"[MEMORY] ✓ Informazioni di {nome} {cognome} caricate in memoria")
            
        except Exception as e:
            self.get_logger().error(f"[MEMORY] Errore nel caricamento informazioni: {str(e)}")

    def update_user(self,msg):
        self.Up_Kg2=Update_Kg()
        user_data="Anziano con i parametri "+msg.data
        self.get_logger().info(f"Pepper controller riceve : "+user_data)
        user_update=self.Up_Kg2.update_user_callback(user_data) 
        self.get_logger().info(f"User_update : "+str(user_update))
        if self.Up_Kg2.delete_duplicates():
            self.get_logger().info(f"Eliminazione dei duplicati")
        msg=Bool()
        msg.data=True
         
        if user_update:
            # Carica le informazioni della persona nella memoria dell'agente
            self.load_person_info_to_memory()
            
            msg2=String()
            msg2.data="Grazie per esserti registrato... " \
                "Per attivare o disattivare l'ascolto puoi toccare la mia testa... " \
                "Non preoccuparti non posso sentire dolore..... " \
                "Attendi che i miei occhi si illuminino di verde affinchè io possa ascoltarti...., mi raccomando parla in modo chiaro e distinto....." \
                "Iniziamo?... "
            
            self.speak_pub.publish(msg2)
            self.start_bdi()


    def is_speaking_callback(self, msg):
        self.is_speaking_bool = msg.data
        if not self.is_speaking_bool and self.deve_rispondere:
            self.get_logger().info("[IS_SPEAKING] Fine del parlato, attivo il recording")
            start_record_msg = Bool()
            start_record_msg.data = True
            self.record_no_mic_pub.publish(start_record_msg)

    def transcription_bdi_callback(self, msg):
        self.get_logger().info("[TRANSCRIPTION] Testo ricevuto")
        data = json.loads(msg.data)
        trascrizione = data.get("trascrizione")
        agente = data.get("agente")
        percept = data.get("percept")
        
        if trascrizione.startswith('"') and trascrizione.endswith('"'):
            trascrizione = trascrizione[1:-1]
            if trascrizione.startswith('"') and trascrizione.endswith('"'):
                trascrizione = trascrizione[1:-1]
        s = trascrizione 

        if agente != "agente":
            messaggio_json = {
                "messaggio": s,
                "agente": agente,
                "percept": percept
            }
            msg = String()
            msg.data = json.dumps(messaggio_json)
            self.bridge_pub.publish(msg)

    def spedisci_a_nodo(self, message):
        self.get_logger().info(f"[TO_ROS] Messaggio ricevuto: {message.data}")
        try:
            data = json.loads(message.data)
            nodo = data.get("nodo")
        except json.JSONDecodeError:
            self.get_logger().error("Messaggio non è un JSON valido")
            return

        if nodo == "pepper_code":
            self.invia_a_pepper_interaction(data)
        elif nodo == "effettua_test":
            msg = String()
            msg.data = message.data
            self.invia_a_test.publish(msg)
        elif nodo == "db_node":
            msg = String()
            msg.data = message.data
        else:
            self.get_logger().warn(f"Nodo sconosciuto: {nodo}")

    def invia_a_pepper_interaction(self, data):
        messaggio = data.get('messaggio','Messaggio non definito')
        agente = data.get('agente','agente')
        percept = data.get('percept','percept')

        if agente != "agente":
            self.deve_rispondere = True
        else:
            self.deve_rispondere = False

        messaggio_json = {
            "messaggio": messaggio,
            "agente": agente,
            "percept": percept
        }
        msg = String()
        msg.data = json.dumps(messaggio_json)
        self.get_logger().info(f"[PEPPER INTERACTION] Messaggio inviato: {msg.data}")
        self.speak_pub.publish(msg)
    
    def query_al_db(self,msg):
        self.get_logger().info("QUERY")
        a = self.Up_Kg.execute_predefined_query(msg.data)
        time.sleep(5)
        return a

    def consiglia_esercizio(self, msg):
        self.get_logger().info("GENERO RISPOSTA")

        response = self.agent_executor.invoke({"input": msg})

        self.get_logger().info(f"{response['output']}")
        self.get_logger().info(f"{response}")

        response = response['output']
            
        msg_to_publish = String()
        msg_to_publish.data = response  

        self.speak_pub.publish(msg_to_publish)
        msg2=Bool()
        msg2.data=False
        self.start_bdi_pub.publish(msg2)

    def start_bdi(self):
        msg = String()

        messaggio_json = {
            "messaggio": "start"
        }
        msg.data = json.dumps(messaggio_json)
        self.get_logger().info(f"[DB] Messaggio ricevuto: {msg.data}")
        self.bridge_pub.publish(msg)

        msg2=Bool()
        msg2.data=True
        self.start_bdi_pub.publish(msg2)
    
    def __del__(self):
        """Cleanup quando il nodo viene distrutto"""
        #self.stop_periodic_monitoring()
        pass


def main(args=None):
    rclpy.init(args=args)
 
    node = Pepper_Controller()
  
    node.start_tablet()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Interruzione da tastiera ricevuta")
    finally:
        #node.stop_periodic_monitoring()
        rclpy.shutdown()


if __name__ == "__main__":
    try:
        main()
    finally:
        graph._driver.close()