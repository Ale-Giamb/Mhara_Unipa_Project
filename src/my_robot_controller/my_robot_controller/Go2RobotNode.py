import cv2
import numpy as np
import asyncio
import logging
import threading
import time
import json
import os
import datetime
from queue import Queue
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Bool

from cv_bridge import CvBridge

"""
from ...go2_robot_node.go2_robot_node.unitree_webrtc_connect.webrtc_driver import WebRTCConnectionMethod

from ...go2_robot_node.go2_robot_node.unitree_webrtc_connect.webrtc_driver_alt import Go2WebRTCConnection

from ...go2_robot_node.go2_robot_node.unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD
from ...go2_robot_node.go2_robot_node.unitree_webrtc_connect.webrtc_audiohub import WebRTCAudioHub
"""
from .unitree_webrtc_connect.webrtc_driver import WebRTCConnectionMethod

from .unitree_webrtc_connect.webrtc_driver_alt import Go2WebRTCConnection

from .unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD
from .unitree_webrtc_connect.webrtc_audiohub import WebRTCAudioHub
from aiortc import MediaStreamTrack

# --- CONFIGURAZIONE ---
logging.basicConfig(level=logging.WARNING)
LOGGER = logging.getLogger("GO2_ROBOT")
LOGGER.setLevel(logging.INFO)

# Code globali per la comunicazione tra thread
frame_queue = Queue()
robot_ready_event = threading.Event()

# Variabile globale per il controller
global_controller = None


# ============================================================
# CLASSE CONTROLLER (Adattata)
# ============================================================
class Go2Controller:
    def __init__(self, conn):
        self.conn = conn
        self.audio_hub = WebRTCAudioHub(self.conn, LOGGER)
        self.tts_audio_name = "tts_current"

    async def init_robot(self):
        """Inizializzazione post-connessione"""
        await self._ensure_normal_mode()
        LOGGER.info("Controller Robot Pronto")

    async def _ensure_normal_mode(self):
        if not self.conn.datachannel: return
        
        try:
            response = await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["MOTION_SWITCHER"],
                {"api_id": 1001}
            )
            data = json.loads(response["data"]["data"])
            current_mode = data.get("name")

            if current_mode != "normal":
                LOGGER.info(f"Switch motion mode: {current_mode} -> normal")
                await self.conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["MOTION_SWITCHER"],
                    {
                        "api_id": 1002,
                        "parameter": {"name": "normal"}
                    }
                )
                await asyncio.sleep(3)
        except Exception as e:
            LOGGER.error(f"Errore check mode: {e}")

    # --- MOVIMENTO ---
    async def move(self, x=0.0, y=0.0, z=0.0, duration=0.5):
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {
                    "api_id": SPORT_CMD["Move"],
                    "parameter": {"x": x, "y": y, "z": z}
                }
            )
        except Exception as e:
            LOGGER.error(f"Errore movimento: {e}")

    async def stop(self):
        await self.move(0, 0, 0, 0)

    # StandUp, StandDown, Hello, Stretch, Content
    async def sport_mod(self, pose):
        """
        Esegue una posa di sport mode.
        
        Args:
            pose (str): Nome della posa (StandUp, StandDown, Hello, Stretch, Content)
        """
        # Normalizza il nome della posa in modo robusto.
        # Accetta input come "stand_up", "stand up", "StandUp", "standup".
        try:
            import re
            parts = re.split(r'[^a-zA-Z]+', str(pose))
            pose_normalized = ''.join(p.capitalize() for p in parts if p)

            LOGGER.info(f"Esecuzione Sport Mod: {pose_normalized}")
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD[pose_normalized]}
            )
        except KeyError:
            LOGGER.error(f"Pose non riconosciuta: {pose} -> {pose_normalized}")
        except Exception as e:
            LOGGER.error(f"Errore SportMod {pose}: {e}")

    # da eliminare dopo test
    async def stand_up(self):
        LOGGER.info("Stand Up")
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["StandUp"]}
            )
        except Exception as e:
            LOGGER.error(f"Errore StandUp: {e}")

    async def hello(self):
        LOGGER.info("Hello")
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["Hello"]}
            )
        except Exception as e:
            LOGGER.error(f"Errore Hello: {e}")

    async def stretch(self):
        LOGGER.info("Stretch")
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["Stretch"]}
            )
        except Exception as e:
            LOGGER.error(f"Errore Stretch: {e}")

    async def content(self):
        LOGGER.info("Content")
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["Content"]}
            )
        except Exception as e:
            LOGGER.error(f"Errore Content: {e}")


    async def stand_down(self):
        LOGGER.info("Stand Down")
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["StandDown"]}
            )
        except Exception as e:
            LOGGER.error(f"Errore StandDown: {e}")



    # --- AUDIO ---
    async def play_audio(self, filename):
        LOGGER.info(f"Playing audio: {filename}")
        path = os.path.abspath(filename)
        if not os.path.exists(path):
            LOGGER.error(f"File non trovato: {path}")
            return

        name_no_ext = os.path.splitext(os.path.basename(filename))[0]
        try:
            response = await self.audio_hub.get_audio_list()
            audio_list = json.loads(response["data"]["data"]).get("audio_list", [])
            
            audio = next((a for a in audio_list if a["CUSTOM_NAME"] == name_no_ext), None)

            if not audio:
                LOGGER.info("Caricamento file audio sul robot...")
                await self.audio_hub.upload_audio_file(path)
                await asyncio.sleep(1)
                response = await self.audio_hub.get_audio_list()
                audio_list = json.loads(response["data"]["data"]).get("audio_list", [])
                audio = next((a for a in audio_list if a["CUSTOM_NAME"] == name_no_ext), None)

            if audio:
                await self.audio_hub.play_by_uuid(audio["UNIQUE_ID"])
                # Se disponibile, segnala al nodo ROS la fine della riproduzione
               
                if hasattr(self, 'node') and getattr(self, 'node') is not None and hasattr(self.node, 'audio_finished_pub'):
                    msg = Bool()
                    msg.data = True
                    try:
                        self.node.audio_finished_pub.publish(msg)
                    except Exception:
                        pass
            else:
                LOGGER.error("Audio non trovato dopo upload")

        except Exception as e:
            LOGGER.error(f"Errore Audio: {e}")

    async def speak(self, text):
        LOGGER.info(f"[SPEAK] Inizio TTS per: {text[:100]}")
        AUDIO_BASE_DIR = Path.home() / "audiogo2"
        AUDIO_BASE_DIR.mkdir(exist_ok=True)
        print("Audio in generazione...", flush=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        audio_path = AUDIO_BASE_DIR / f"tts_{timestamp}.wav"
        #audio_path = AUDIO_BASE_DIR / f"{self.tts_audio_name}.wav"
        
        piper_bin = "/home/roboticslab/piper/piper"
        model_path = "/home/roboticslab/piper_models/it_IT-riccardo-x_low.onnx"

        if not os.path.exists(piper_bin):
            LOGGER.error("Piper binario non trovato")
            return

        LOGGER.info(f"[SPEAK] Generazione audio con Piper in: {audio_path}")
        proc = await asyncio.create_subprocess_exec(
            piper_bin, "--model", model_path, "--output_file", str(audio_path),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate(text.encode("utf-8"))

        if proc.returncode == 0:
            LOGGER.info(f"[SPEAK] Audio generato con successo, riproduzione in corso")
            await self.play_audio(str(audio_path))
        else:
            LOGGER.error(f"[SPEAK] Errore generazione TTS Piper: {stderr.decode('utf-8', errors='ignore')}")


# ============================================================
# NODO ROS2
# ============================================================
class Go2RobotNode(Node):
    def __init__(self):
        super().__init__('go2_robot_node')
        
        self.cv_bridge = CvBridge()
        self.callback_group = ReentrantCallbackGroup()
        
        # Publisher
        self.status_pub = self.create_publisher(String, 'go2/status', 10)
        # Publisher che segnala la fine della riproduzione audio
        self.audio_finished_pub = self.create_publisher(Bool, 'go2/audio/finished', 10)
        
        # Subscriber
        self.cmd_vel_sub = self.create_subscription(
            Twist, 'go2/cmd_vel', self.cmd_vel_callback, 10, callback_group=self.callback_group)
        
        self.action_sub = self.create_subscription(
            String, 'go2/action', self.action_callback, 10, callback_group=self.callback_group)
        
        self.audio_sub = self.create_subscription(
            String, 'go2/audio/play', self.audio_callback, 10, callback_group=self.callback_group)
        
        self.speak_sub = self.create_subscription(
            String, 'go2/audio/speak', self.speak_callback, 10, callback_group=self.callback_group)
        
        self.camera_go2= self.create_subscription(
            Bool, 'go2/camera', self.publish_video_frame, 10, callback_group=self.callback_group)


        # Cartella per salvare le immagini
        
        self.camera_dir = Path.home() / "Scrivania" / "mhara_env" / "MHARA_Unipa" / "src" / "camera"
        self.camera_dir.mkdir(exist_ok=True)
        
        self.get_logger().info("Go2 Robot Node inizializzato")
        self.publish_status("Nodo avviato, in attesa di connessione robot...")

    def cmd_vel_callback(self, msg: Twist):
        """Riceve comandi Twist (geometry_msgs/Twist) e li invia al robot"""
        if global_controller is None:
            self.get_logger().debug("Go2 non disponibile, ignorando cmd_vel")
            return
            
        try:
            x = msg.linear.x
            y = msg.linear.y
            z = msg.angular.z
            self.get_logger().debug(f"Cmd Vel: x={x}, y={y}, z={z}")
            asyncio.run_coroutine_threadsafe(global_controller.move(x, y, z), loop)
        except Exception as e:
            self.get_logger().error(f"Errore cmd_vel_callback: {e}")

    def action_callback(self, msg: String):
        """Riceve comandi azione: stand_up, stand_down, hello, stretch, content, stop"""
        if global_controller is None:
            self.get_logger().debug("Go2 non disponibile, ignorando action")
            return
            
        try:
            action = msg.data.lower().strip()
            self.get_logger().info(f"Action ricevuta: {action}")
            
            if action == "stop":
                asyncio.run_coroutine_threadsafe(global_controller.stop(), loop)
            else:
                # Tutte le altre azioni vengono gestite da sport_mod
                asyncio.run_coroutine_threadsafe(
                    global_controller.sport_mod(action), 
                    loop
                )
        except Exception as e:
            self.get_logger().error(f"Errore action_callback: {e}")

    def audio_callback(self, msg: String):
        """Riceve comandi per riprodurre file audio"""
        if global_controller is None:
            self.get_logger().debug("Go2 non disponibile, ignorando audio")
            return
            
        try:
            filename = msg.data.strip()
            self.get_logger().debug(f"Play audio: {filename}")
            asyncio.run_coroutine_threadsafe(global_controller.play_audio(filename), loop)
        except Exception as e:
            self.get_logger().error(f"Errore audio_callback: {e}")

    def speak_callback(self, msg: String):
        """Riceve testo da sintetizzare con TTS"""
        text = msg.data.strip()
        self.get_logger().info(f"[SPEAK_CALLBACK] Ricevuto testo: {text[:100]}")
        
        if global_controller is None:
            self.get_logger().warn("⚠️  [SPEAK_CALLBACK] Go2 non disponibile! Controllare connessione WebRTC (192.168.12.1:8081)")
            return
            
        try:
            asyncio.run_coroutine_threadsafe(global_controller.speak(text), loop)
            self.get_logger().info(f"[SPEAK_CALLBACK] Coroutine schedulata nell'event loop")
        except Exception as e:
            self.get_logger().error(f"Errore speak_callback: {e}")


    def publish_video_frame(self,msg: Bool):
        """Salva il frame video dalla camera su disco"""
        if not frame_queue.empty():
            img = frame_queue.get()
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = self.camera_dir / f"image.jpeg"
                cv2.imwrite(str(filename), img)
                self.get_logger().info(f"Frame salvato: {filename}")
            except Exception as e:
                self.get_logger().error(f"Errore salvataggio frame: {e}")

    def publish_status(self, status_msg: str):
        """Pubblica lo stato del robot"""
        msg = String()
        msg.data = status_msg
        self.status_pub.publish(msg)


# ============================================================
# LOGICA ASYNC (Thread Secondario)
# ============================================================
def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    
    conn = None
    global global_controller

    async def recv_camera_stream(track: MediaStreamTrack):
        while True:
            try:
                frame = await track.recv()
                img = frame.to_ndarray(format="bgr24")
                if frame_queue.qsize() < 2: 
                    frame_queue.put(img)
            except Exception:
                pass

    async def setup_robot():
        global conn, global_controller
        
        try:
            LOGGER.info("Connessione WebRTC in corso...")
            conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)
            await conn.connect()
            
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(recv_camera_stream)
            
            global_controller = Go2Controller(conn)
            await global_controller.init_robot()
            
            robot_ready_event.set()
            LOGGER.info("Robot Go2 connesso e pronto")
            
        except Exception as e:
            LOGGER.warning(f"Go2 robot non disponibile: {e}")
            LOGGER.warning("Continuando senza Go2 robot...")
            robot_ready_event.set()

    loop.run_until_complete(setup_robot())
    loop.run_forever()


# ============================================================
# MAIN
# ============================================================
def main(args=None):
    rclpy.init(args=args)
    
    # Avvia thread asincrono
    global loop 
    loop= asyncio.new_event_loop()
    t = threading.Thread(target=run_async_loop, args=(loop,), daemon=True)
    t.start()

    # Crea il nodo ROS2
    node = Go2RobotNode()
    
    # Attendi connessione robot con timeout
    LOGGER.info("In attesa connessione robot Go2...")
    if robot_ready_event.wait(timeout=15):
        if global_controller is not None:
            # Associa il nodo ROS2 al controller per permettere callback/pub dal controller
            try:
                global_controller.node = node
            except Exception:
                pass
            node.publish_status("Robot Go2 connesso e pronto!")
            LOGGER.info("Robot Go2 connesso e operativo")
        else:
            node.publish_status("Sistema avviato senza Go2 robot")
            LOGGER.info("Sistema avviato in modalità degradata (senza Go2)")
    else:
        node.publish_status("Sistema avviato senza Go2 robot (timeout connessione)")
        LOGGER.warning("Timeout connessione robot Go2 - continuando senza")
        robot_ready_event.set()

    # Usa MultiThreadedExecutor per gestire callback con threading
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor=executor)
    
    node.destroy_node()
    rclpy.shutdown()
    loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    main()
