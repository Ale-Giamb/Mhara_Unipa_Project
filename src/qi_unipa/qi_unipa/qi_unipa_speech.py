import qi
import sys
import rclpy
import time
import os
import paramiko
from rclpy.node import Node
from std_msgs.msg import Bool,String
from qi_unipa_msgs.msg import PostureWithSpeed,Track
import json

class QiUnipaSpeech(Node):  
    def __init__(self):
        super().__init__('qi_unipa_speech')
        
        # Ottieni i parametri
        self.declare_parameter('ip','192.168.0.161')
        self.declare_parameter('port',9559)
        self.ip = self.get_parameter('ip').get_parameter_value().string_value
        port = self.get_parameter('port').get_parameter_value().integer_value
        
        # Connessione sessione
        self.session = self.set_connection(self.ip, port)

        #ALService
        self.memory = self.session.service("ALMemory")
        self.animated_service = self.session.service("ALAnimatedSpeech")
        self.audio_service = self.session.service("ALAudioRecorder")
        self.sound_detect_service = self.session.service("ALSoundDetection")
        self.sound_detect_service.setParameter("Sensitivity", 0.8)
        self.configuration = {"bodyLanguageMode":"contextual"}
        self.leds_service = self.session.service("ALLeds")

        self.tg = self.session.service('ALTactileGesture')
        self.s1 = self.tg.onGesture.connect(self.onTouched)
     
        #Variabili
        self.last_index=self.memory.getData("ALTextToSpeech/Status")[0]
        self.is_recognizing = False

        #Topic subscription
        self.tts_sub = self.create_subscription(String, "/speak", self.set_tts, 10)

        self.record_sub = self.create_subscription(Bool, "/record", self.record_callback, 10)
        self.record_no_mic = self.create_subscription(Bool, "/record_no_mic", self.record_callback_no_mic, 10)
        self.record_sub = self.create_subscription(Bool, "/end", self.ending_callback, 10)
        self.start_bdi_sub= self.create_subscription(Bool, "/start_bdi", self.start_bdi_callback, 10)
        #Topic publisher
        self.tracking_pub = self.create_publisher(Track, "/track", 10)
        self.posture_pub = self.create_publisher(PostureWithSpeed, "/posture", 10)
        self.isSpeaking_pub=self.create_publisher(Bool,'/is_speaking',10)
        self.isSpeaking_bdi_pub=self.create_publisher(Bool,'/is_speaking_bdi',10)
        self.start_pub=self.create_publisher(Bool,'/start_conv',10)
        self.show_pub=self.create_publisher(String,"/show",10)
        self.stt_pub =self.create_publisher(String,"/stt",10)
        self.stt_bdi_pub =self.create_publisher(String,"/stt_bdi",10)
        self.touched=self.create_publisher(Bool, "/touched", 10)
        
        # Publisher per PC microphone (se AUDIO_SOURCE=pc)
        audio_source = os.getenv("AUDIO_SOURCE", "pc").lower()
        if audio_source == "pc":
            self.record_pc_pub = self.create_publisher(Bool, "/record_pc", 10)
            self.get_logger().info("🎙 PC Microphone mode - publisher /record_pc creato")

        self.agente = "agente"      
        self.percept = "percept"
        self.start=False
        self.first=False
        self.tablet_on=True
        self.start_bdi=False
        self.create_timer(0.5, self.check_speaking)
        self.set_led(False)
        



    def ending_callback(self,msg):
     
            msg2=String()
            self.pub_track("Stop",0.3)
            self.pub_posture("Stand", 0.5)
            msg2.data="disattivo.html"
            self.tablet_on=True
            self.start=False
            self.set_led(False)
            self.show_pub.publish(msg2)

    def start_bdi_callback(self,msg):
     
            self.start_bdi=msg.data
        

    def onTouched(self,value):
        """ This will be called each time a touch
        is detected.

        """
        self.get_logger().info(f"Tocco: {value}")
       
        if not self.start: # sistema attivato

            self.start=True # stato sistema attivo
            msg=Bool()
            if self.first: # è già stata eseguita una prima interazione
                msg.data=True

            else: #prima interazione
                msg.data=False
                self.first=True

            self.start_pub.publish(msg)
         
            self.get_logger().info("Start")

        else:  # sistema disattivato
            self.start=False
            self.set_led(False)
            self.pub_posture("Stand", 0.5)
            self.get_logger().info("Ending")

        msg2=String()
        if  self.tablet_on: #tablet attivo
            self.pub_track("People",0.8) #People #Face
            msg2.data="attivo.html"
            self.tablet_on=False

            msg3=Bool()
            msg3.data=True
            self.touched.publish(msg3)
            
        else:  #tablet disattivo
            self.pub_track("Stop",0.3)
            msg2.data="disattivo.html"
            self.tablet_on=True
                       
            msg3=Bool()
            msg3.data=False
            self.touched.publish(msg3)

        self.show_pub.publish(msg2)

    def set_connection(self, ip, port):
        session = qi.Session()
        try:
            session.connect(f"tcp://{ip}:{port}")
        except RuntimeError:
            self.get_logger().error(f"Can't connect to Naoqi at ip \"{ip}\" on port {port}.\n"
                                    "Please check your script arguments.")
            sys.exit(1)
        return session

    def pub_track(self, name, distance):
        msg=Track()
        msg.target_name=name
        msg.distance=distance
        self.tracking_pub.publish(msg)

    def pub_posture(self, name, speed):
        msg=PostureWithSpeed()
        msg.posture_name=name
        msg.speed=speed
        self.posture_pub.publish(msg)

    def is_valid_json(self,stringa):
        try:
            json.loads(stringa)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def set_tts(self, msg):
        if self.is_valid_json(msg.data):

            data = json.loads(msg.data)
            messaggio = data.get("messaggio")
            self.agente = data.get("agente","agente")
            self.percept = data.get("percept","percept")

            self.animated_service.say(messaggio)
        else:

            self.set_fade_led(False)
            self.animated_service.say(msg.data)

        self.pub_posture("Stand", 0.5)

    
                
    def record_callback(self, msg):
        
        # CONTROLLO: Se AUDIO_SOURCE=pc, skippa Pepper e usa PC microphone
        audio_source = os.getenv("AUDIO_SOURCE", "pepper").lower()
        if audio_source == "pc":
            self.get_logger().info("[RECORD] 🎙 AUDIO_SOURCE=pc - Inibendo Pepper, usando PC microphone")
            
            # Pubblica su /record_pc per far registrare il PC microphone
            if hasattr(self, 'record_pc_pub'):
                pc_record_msg = Bool()
                pc_record_msg.data = True
                self.record_pc_pub.publish(pc_record_msg)
                self.get_logger().info("[RECORD] ✓ Comando registrazione inviato a PC microphone")
            else:
                self.get_logger().error("[RECORD] ✗ Publisher /record_pc non disponibile")
            
            return
        
        # FLUSSO NORMALE: Registrazione Pepper
        if getattr(self, "is_recording", False):
            self.get_logger().warn("Registrazione già in corso, callback ignorato.")
            
        self.is_recording = True

        try:
            self.audio_service.stopMicrophonesRecording()
            self.get_logger().info("Registrazione precedente interrotta.")
        except Exception:
            self.get_logger().warn("Nessuna registrazione attiva da fermare.")
        
        try:
            self.sound_detect_service.unsubscribe("Audio Detection")
            time.sleep(0.2)
        except:
            pass
        """
        # Configurazione della registrazione
        channels = [1, 1, 1, 1]  # Abilitare tutti e 4 i microfoni (frontale, posteriore, sinistro, destro)
        audio_format = "wav"
        sample_rate = 16000  # Frequenza di campionamento (16 kHz)
        output_file_robot = "/home/nao/audio_record_unipa/recording.wav"

        # Avviare la registrazione
        self.sound_detect_service.subscribe("Audio Detection")
        time.sleep(1.5)
        # Attendere l'inizializzazione del servizio SoundDetected
        max_retries = 30
        retry_count = 0
        sound_data = None
        
        while retry_count < max_retries:
            try:
                sound_data = self.memory.getData("SoundDetected")
               
                if sound_data is not None and len(sound_data) > 0 and len(sound_data[0]) > 1:
                    self.get_logger().info("Servizio SoundDetected inizializzato correttamente.")
                    break
                else:
                    self.get_logger().info(f"Attesa inizializzazione SoundDetected... tentativo {retry_count + 1}")
                    time.sleep(0.5)
                    retry_count += 1
            except Exception as e:
                self.get_logger().warn(f"Errore durante l'accesso a SoundDetected: {e}")
                time.sleep(0.5)
                retry_count += 1
        
        if sound_data is None:
            self.get_logger().error("Impossibile inizializzare il servizio SoundDetected. Annullamento registrazione.")
            self.sound_detect_service.unsubscribe("Audio Detection")
            self.is_recording = False
            return
        
        self.audio_service.startMicrophonesRecording(output_file_robot, audio_format, sample_rate, channels)
        self.get_logger().info("(Qi Unipa Speech: Avvio microfoni")
        self.set_led(True)
        time.sleep(0.3)


        while not self.is_recognizing:
            time.sleep(0.3)
        

            if  self.memory.getData("SoundDetected")[0][1]==1:
                self.get_logger().info("(Qi Unipa Speech: Avvio registrazione...")
                
                self.is_recognizing=True
                
        # Attendere la fine della registrazione
        while self.is_recognizing:
                time.sleep(4)
                if  self.memory.getData("SoundDetected")[0][1]==0:
                    self.is_recognizing=False
                     # Terminare la registrazione
                    self.audio_service.stopMicrophonesRecording()
                    self.set_led(False)
                    self.sound_detect_service.unsubscribe("Audio Detection")
                    self.get_logger().info(f"Registrazione terminata e salvata in: {output_file_robot}")
        

        path_ros_ws=os.path.join(os.path.abspath(__file__).split("/install")[0])
     
        # Trasferire il file al PC
        local_output_file = os.path.join(path_ros_ws,"src/audio/recording.wav")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip, username='nao', password='nao')#'192.168.0.161'

        sftp = ssh.open_sftp()
        sftp.get(output_file_robot, local_output_file)
        sftp.close()
        ssh.close()
        self.get_logger().info("File trasferito con successo!")
        """
        res=String()
        path_ros_ws=os.path.join(os.path.abspath(__file__).split("/install")[0])
        local_output_file = os.path.join(path_ros_ws,"src/audio/recording.wav")
        
        res.data=local_output_file
        
        self.set_fade_led(True)
        # gestire quando flusso termina e quando riparte
        if self.start:
            self.stt_pub.publish(res)

    def record_callback_no_mic(self,msg):

        res_bdi=String()
        messaggio_json = {
            "agente": self.agente,
            "percept": self.percept
        }
        res_bdi.data = json.dumps(messaggio_json)
        self.stt_bdi_pub.publish(res_bdi)


    def check_speaking(self):
        msg=Bool()
        status=self.memory.getData("ALTextToSpeech/Status")
        if self.start:  
            if status[1]=="done" and status[0]!=self.last_index:
                msg.data=False
                self.isSpeaking_pub.publish(msg)
                self.get_logger().info("Pepper ha terminato")
            else :
                msg.data=True
                self.isSpeaking_pub.publish(msg)
                #self.get_logger().info("Pepper in elaborazione")
            self.last_index=status[0]

        elif self.start_bdi:
            if status[1]=="done" and status[0]!=self.last_index:
                msg.data=False
                self.isSpeaking_bdi_pub.publish(msg)
                self.get_logger().info("BDI--------------Pepper ha terminato")
            else :
                msg.data=True
                self.isSpeaking_bdi_pub.publish(msg)
            
            self.last_index=status[0]



    def set_led(self, on):
        names = [
        "Face/Led/Green/Left/0Deg/Actuator/Value",
        "Face/Led/Green/Left/45Deg/Actuator/Value",
        "Face/Led/Green/Left/90Deg/Actuator/Value",
        "Face/Led/Green/Left/135Deg/Actuator/Value",
        "Face/Led/Green/Left/180Deg/Actuator/Value",
        "Face/Led/Green/Left/225Deg/Actuator/Value",
        "Face/Led/Green/Left/270Deg/Actuator/Value",
        "Face/Led/Green/Left/315Deg/Actuator/Value",

        "Face/Led/Green/Right/0Deg/Actuator/Value",
        "Face/Led/Green/Right/45Deg/Actuator/Value",
        "Face/Led/Green/Right/90Deg/Actuator/Value",
        "Face/Led/Green/Right/135Deg/Actuator/Value",
        "Face/Led/Green/Right/180Deg/Actuator/Value",
        "Face/Led/Green/Right/225Deg/Actuator/Value",
        "Face/Led/Green/Right/270Deg/Actuator/Value",
        "Face/Led/Green/Right/315Deg/Actuator/Value"]

        self.leds_service.createGroup("eyes",names)
        # Switch the new group on
        if on==True:
            self.leds_service.off("FaceLeds")
            self.leds_service.on("eyes")
        elif on==False:
            self.leds_service.off("eyes")
            self.leds_service.on("FaceLeds")
            
   

    def set_fade_led(self, on):
        # Lista dei LED del volto
        names = [
            "Face/Led/Green/Left/0Deg/Actuator/Value",
            "Face/Led/Green/Left/45Deg/Actuator/Value",
            "Face/Led/Green/Left/90Deg/Actuator/Value",
            "Face/Led/Green/Left/135Deg/Actuator/Value",
            "Face/Led/Green/Left/180Deg/Actuator/Value",
            "Face/Led/Green/Left/225Deg/Actuator/Value",
            "Face/Led/Green/Left/270Deg/Actuator/Value",
            "Face/Led/Green/Left/315Deg/Actuator/Value",
            "Face/Led/Green/Right/0Deg/Actuator/Value",
            "Face/Led/Green/Right/45Deg/Actuator/Value",
            "Face/Led/Green/Right/90Deg/Actuator/Value",
            "Face/Led/Green/Right/135Deg/Actuator/Value",
            "Face/Led/Green/Right/180Deg/Actuator/Value",
            "Face/Led/Green/Right/225Deg/Actuator/Value",
            "Face/Led/Green/Right/270Deg/Actuator/Value",
            "Face/Led/Green/Right/315Deg/Actuator/Value"
        ]

        self.leds_service.createGroup("eyes", names)

        # Lista di colori RGB in formato (R, G, B)
        colors = [
            (1.0, 0.0, 0.0),  # Rosso
            (0.0, 1.0, 0.0),  # Verde
            (0.0, 0.0, 1.0),  # Blu
            (1.0, 1.0, 0.0),  # Giallo
            (0.0, 1.0, 1.0),  # Ciano
            (1.0, 0.0, 1.0),  # Magenta
            (1.0, 1.0, 1.0)   # Bianco
        ]

        duration = 1.2  # Durata del fade per ogni colore

        if on==True:
            self.leds_service.off("FaceLeds")
            for r, g, b in colors:
                self.leds_service.fadeRGB("FaceLeds", r, g, b, duration)
                
        elif on==False:
          
             self.set_led(False)


def main(args=None):
    rclpy.init(args=args)
 
    node = QiUnipaSpeech()
    
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
