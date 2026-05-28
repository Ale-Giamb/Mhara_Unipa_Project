import qi
import rclpy
from rclpy.node import Node
import sys
from std_msgs.msg import String,Bool
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import time
import numpy as np
import cv2

import threading
# Costanti per la risoluzione (prova modifica)
K_QVGA = 1     # 320x240
K_VGA = 2      # 640x480
K_HD = 4       # 1280x720
K_4VGA= 3
# Costanti per lo spazio colore
K_RGB = 13
K_BGR = 11
K_YUV = 10

class QiUnipa_vision(Node):
    
    def __init__(self):
        super().__init__('qi_unipa_vision')
        # Inizializza CvBridge all'interno della classe
        img_resolution = K_QVGA
        self.bridge = CvBridge()
   
        # Ottieni i parametri
        self.declare_parameter('ip', '192.168.0.161')
        self.declare_parameter('port', 9559)
        self.declare_parameter('camera_index', 0)#0 Top Camera, 1 Bottom Camera
        ip = self.get_parameter('ip').get_parameter_value().string_value
        port = self.get_parameter('port').get_parameter_value().integer_value
        self.camera_index = self.get_parameter('camera_index').get_parameter_value().integer_value
        
        # Connessione sessione
        self.session = self.set_connection(ip, port)
        
        self.camera_pub = self.create_publisher(Image, '/camera_call', 10)
        self.image_pub = self.create_publisher(Bool, '/image_tablet', 10)
        self.pose_pub = self.create_publisher(String, '/pose', 10)
        
        self.video_service = self.session.service("ALVideoDevice")
        self.video_service.unsubscribeAllInstances('Camera')
        self.camera_sub=self.create_subscription(Bool,"/get_camera",self.get_camera,10)
        #self.camera_timer = self.create_timer(0.1, self.get_camera)
        #self.video_client = self.video_service.subscribeCamera("Camera", self.camera_index, K_4VGA, K_RGB, 30) #ORIGINALE (1 immagine al secondo)
        self.video_client = self.video_service.subscribeCamera("Camera", self.camera_index, img_resolution, K_YUV, 30) #K_QVGA (Non funzione più il modello) #K_VGA(funziona ed è più veloci di K_4VGA)
        
        #threading.Thread(target=self.pose_detection, daemon=True).start()
  

    def set_connection(self, ip, port):
        session = qi.Session()
        try:
            session.connect(f"tcp://{ip}:{port}")
        except RuntimeError:
            self.get_logger().error(f"Can't connect to Naoqi at ip \"{ip}\" on port {port}.\n"
                                    "Please check your script arguments.")
            sys.exit(1)
        return session
    
    def get_camera(self,msg):
        #self.video_client = self.video_service.subscribeCamera("Camera", self.camera_index, K_4VGA, K_RGB, 30)
        result = self.video_service.getImageRemote(self.video_client)
        #result = ""

        if result is None:
            self.get_logger().info(f'\n##############\n Impossibile acquisire immagine')
            return
        try:           
            width = result[0]
            height = result[1]
            channels = result[2]
            image_binary = result[6]
        
            # Converti l'immagine binaria in un array numpy
            image_array = np.frombuffer(image_binary, dtype=np.uint8)
        
            image_array = image_array.reshape((height, width, channels))
            image_array = cv2.cvtColor(image_array, cv2.COLOR_YUV2BGR)

            # Pubblica l'immagine
        
            img_msg = self.bridge.cv2_to_imgmsg(image_array, encoding="bgr8")
            
            self.camera_pub.publish(img_msg)
            
            self.get_logger().info(f'\n##############\nImmagine Acquisita')
          
        except Exception as e:
            self.get_logger().error(f'Error publishing image: {str(e)}')
        #finally:
            #self.video_service.unsubscribe(self.video_client)

    def pose_detection(self):
       
        while True:
            """start_time = time.time()  # salva l'istante d'inizio del ciclo

            result = self.video_service.getImageRemote(self.video_client)
            end_time = time.time()  # salva l'istante di fine ciclo
            
            cycle_time = end_time - start_time  # calcola la durata del ciclo

            self.get_logger().info(f"CiclOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO completato in {cycle_time:.3f} secondi")
            self.get_logger().info(f"Tempo ciclo: {cycle_time:.3f}s  |  Frequenza: {1.0 / cycle_time:.2f} Hz")

            # opzionale: una piccola pausa per non saturare la CPU
            time.sleep(0.01)"""

          
            start_time = time.time()  # salva l'istante d'inizio del ciclo
            result = self.video_service.getImageRemote(self.video_client)

            if result is None:
                self.get_logger().info(f'\n##############\n Impossibile acquisire immagine')
                return
        
            width, height, channels = result[0], result[1], result[2]
            image_binary = result[6]
            image_array = np.frombuffer(image_binary, dtype=np.uint8).reshape((height, width, channels))
            image_array = cv2.cvtColor(image_array, cv2.COLOR_YUV2BGR)

            msg = Bool()
            msg.data = True  # success è True se cv2.imencode ha funzionato
            self.image_pub.publish(msg)

            msg=String()
            """
            for pose in self.pose_detector.run_detection(image_array):
                if pose != '':
                    msg.data=pose
                    #self.get_logger().info(f'Posa rilevata {pose}')
                    self.pose_pub.publish(msg)
            """
            end_time = time.time()  # salva l'istante di fine ciclo
            
            cycle_time = end_time - start_time  # calcola la durata del ciclo

            #self.get_logger().info(f"CiclOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO completato in {cycle_time:.3f} secondi")
            #self.get_logger().info(f"Tempo ciclo: {cycle_time:.3f}s  |  Frequenza: {1.0 / cycle_time:.2f} Hz")

            # opzionale: una piccola pausa per non saturare la CPU
            time.sleep(0.01)
            
def main(args=None):
    rclpy.init(args=args)
    node = QiUnipa_vision()
    rclpy.spin(node)
    node.video_service.unsubscribe(node.video_client)
    rclpy.shutdown()
 
if __name__ == '__main__':
    main()