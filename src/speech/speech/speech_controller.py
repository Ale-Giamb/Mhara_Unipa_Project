import rclpy
import wave
import time
from rclpy.node import Node
from std_msgs.msg import Bool,String,Int32
from openai import OpenAI
import os
import json

from .whisper_groq import WhisperGroq

# Import opzionale dei moduli audio - se non disponibili, funziona comunque con Pepper
try:
    # Tenta di importare da stesso package
    from .audio_config import AudioConfig, AudioSource
    from .pc_microphone import get_pc_recorder
    HAS_AUDIO_CONFIG = True
    
    # Leggi la sorgente audio dalla variabile d'ambiente ALL'INIZIO
    audio_source = os.getenv("AUDIO_SOURCE", "pepper").lower()
    if audio_source == "pc":
        AudioConfig.to_pc()
    else:
        AudioConfig.to_pepper()
        
except ImportError:
    # Se non disponibile, usa configurazione minima
    HAS_AUDIO_CONFIG = False
    AudioConfig = None
    AudioSource = None
    get_pc_recorder = None



class Speech_Controller(Node):
    def __init__(self):
        super().__init__("speech_controller")

        self.stt_sub = self.create_subscription(String, "/stt", self.stt_callback, 10)
        self.stt_bdi_sub = self.create_subscription(String, "/stt_bdi", self.stt_bdi_callback, 10)
        self.transcription_pub =self.create_publisher(String,"/transcription",10)
        self.transcription_bdi_pub =self.create_publisher(String,"/transcription_bdi",10)
        self.risposta_sub = self.create_subscription(String, "/risposta_si_no", self.condividi_risposta, 10)
        self.show_pub =  self.create_publisher(String,'/show',10)
        self.hide_pub = self.create_publisher(Bool,'/hide',10)
        
        # Sottoscrizione per PC microphone recording (solo se audio_config disponibile)
        if HAS_AUDIO_CONFIG:
            self.pc_record_sub = self.create_subscription(Bool, "/record_pc", self.record_pc_callback, 10)
            self.pc_stt_pub = self.create_publisher(String, "/stt", 10)
            self.audio_config = AudioConfig()
            self.pc_recorder = get_pc_recorder(self.get_logger())
        else:
            self.pc_record_sub = None
            self.pc_stt_pub = None
            self.audio_config = None
            self.pc_recorder = None

        self.agente = "agente"
        self.percept = "percept"
        self.whisper = WhisperGroq() 
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if HAS_AUDIO_CONFIG:
            self.get_logger().info(f"Speech Controller inizializzato. Sorgente audio: {self.audio_config.get_source_name()}")
        else:
            self.get_logger().info("Speech Controller inizializzato (audio_config non disponibile)")
     

 
    def stt_callback_old(self,msg):
        self.get_logger().info(f"path: {msg.data}")
        transcription=self.whisper.transcribe_audio(msg.data)
        #result=self.local_whisper.transcribe(msg.data, language = "it")
        #transcription = result['text']
        self.get_logger().info(f"\n #############################################\ntrascrizione effettuata {transcription}")

        res=String()
        res.data=transcription
        self.transcription_pub.publish(res)

    def stt_bdi_callback(self,msg):
        data = json.loads(msg.data)
        path = data.get("path")
        self.agente = data.get("agente")
        self.percept = data.get("percept")

        self.get_logger().info(f"Agente: {self.agente}, Percept: {self.percept}")
        
        url = f"si_no.html"
        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def stt_callback(self, msg):
        self.get_logger().info(f"path: {msg.data}")
        
        try:
            # Apri il file audio e trascrivi usando l'API OpenAI
            with open(msg.data, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="it"  # Specifica italiano
                )
            
            transcription = transcript.text
            self.get_logger().info(
                f"\n#############################################\n"
                f"trascrizione effettuata: {transcription}"
            )
            
            # Pubblica la trascrizione
            res = String()
            res.data = transcription
            self.transcription_pub.publish(res)
            
        except FileNotFoundError:
            self.get_logger().error(f"File audio non trovato: {msg.data}")
        except Exception as e:
            self.get_logger().error(f"Errore durante la trascrizione: {str(e)}")

    def condividi_risposta(self, msg):
        self.get_logger().info(f"Trascrizione ricevuta: {msg.data}")

        if msg.data == 'no':
            b = Bool()
            b.data = True
            self.hide_pub.publish(b)

        messaggio_json = {
            "trascrizione": msg.data,
            "agente": self.agente,
            "percept": self.percept
        }

        res = String()
        res.data = json.dumps(messaggio_json)

    def record_pc_callback(self, msg):
        """
        Registra audio dal microfono del PC quando riceve comando.
        Viene chiamato quando l'utente sceglie di usare il microfono del PC.
        """
        if not HAS_AUDIO_CONFIG:
            self.get_logger().error("[RECORD_PC] Audio config non disponibile")
            return
            
        try:
            self.get_logger().info("[RECORD_PC] Inizio registrazione dal microfono PC...")
            
            # Leggi la variabile d'ambiente per scegliere il tipo di registrazione
            use_silence_detection = os.getenv("PC_AUDIO_DETECTION", "false").lower() == "true"
            record_duration = int(os.getenv("PC_AUDIO_DURATION", "5"))
            
            if use_silence_detection:
                # Registra con rilevamento di silenzio (più intelligente)
                self.get_logger().info("[RECORD_PC] Usando rilevamento di silenzio...")
                audio_file = self.pc_recorder.record_with_detection(
                    max_duration=10,
                    silence_threshold=0.02
                )
            else:
                # Registra per tempo fisso (più affidabile)
                self.get_logger().info(f"[RECORD_PC] Registrando per {record_duration} secondi...")
                audio_file = self.pc_recorder.record_audio(
                    duration=record_duration
                )
            
            self.get_logger().info(f"[RECORD_PC] ✓ Registrazione completata: {audio_file}")
            
            # Pubblica il path del file registrato
            res = String()
            res.data = str(audio_file)
            self.pc_stt_pub.publish(res)
            
        except Exception as e:
            self.get_logger().error(f"[RECORD_PC] ✗ Errore nella registrazione: {str(e)}")



def main(args=None):
    rclpy.init(args=args)
 
    node = Speech_Controller()
    
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
