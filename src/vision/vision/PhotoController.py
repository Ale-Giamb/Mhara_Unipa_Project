#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Int32, String
from qi_unipa_msgs.msg import StringArray
from langchain_openai import ChatOpenAI
import os 
import cv2
import numpy as np
import matplotlib.pyplot as plt
import queue
import datetime

class PhotoController(Node):
    def __init__(self):
        super().__init__("PhotoController")
        self.cam_subscription = self.create_subscription(Image, "/camera_call", self.image_callback, 10)
        self.look_sub = self.create_subscription(Int32, "/look",self.look_image, 10)
        self.speak_pub = self.create_publisher(String, "/speak", 10)
        self.look_pub = self.create_publisher(StringArray, "/look_resp", 10)
        
        self.img = queue.Queue()
        self.bridge = CvBridge()

        # Specifica il percorso ai file YOLO
        yolo_dir = os.path.expanduser("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/src/camera")
        self.camera_dir = os.path.expanduser("/home/roboticslab/Scrivania/mhara_env/MHARA_Unipa/src/camera/")
        """
        weights_path = os.path.join(yolo_dir, "yolov3.weights")
        config_path = os.path.join(yolo_dir, "yolov3.cfg")

        # Carica YOLO
        self.net = cv2.dnn.readNet(weights_path, config_path)
        with open(os.path.join(yolo_dir, "coco.names"), "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.net.getLayerNames()

         #Gestione dell'output delle layer non connesse
        output_layers_indices = self.net.getUnconnectedOutLayers()
        if len(output_layers_indices) > 0:
            self.output_layers = [self.layer_names[i - 1] for i in output_layers_indices.flatten()]
        else:
            self.output_layers = []
        """
    def add_two_ints_callback(self, request, response):
        try:
            imgs = list(self.img.queue)
            self.get_logger().info(str(len(imgs)))
            label=[]
            self.get_logger().info("____________----")
            for image in imgs:
                cv_image = image
                height, width, _ = cv_image.shape
   
                # Prepara l'immagine per YOLO
                blob = cv2.dnn.blobFromImage(cv_image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                self.net.setInput(blob)
                outs = self.net.forward(self.output_layers)

                # Inizializza le liste per le informazioni sugli oggetti rilevati
                class_ids = []
                confidences = []
                boxes = []

                # Elaborazione degli output di YOLO
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.5:
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)

                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)
                            

                
                for i in class_ids:
                    if (self.classes[i] not in label):
                        label.append(self.classes[i])
            self.get_logger().info(str(label))
            self.speak("ho visto ")
            for l in label:
                self.speak(l)
                



        except Exception as e:
            self.get_logger().error(f"Error in image_callback: {str(e)}")

        response.resp = label

        return response
    

    def speak(self,testo):
        msg=String()
        msg.data=testo
        self.speak_pub.publish(msg)

    def look_resp(self,data):
        msg=StringArray()
        msg.data=data
        self.look_pub.publish(msg)

    def delete_files(full_path):
      # Elimina tutte le immagini esistenti nella cartella
        if os.path.exists(full_path):
            for filename in os.listdir(full_path):
                file_path = os.path.join(full_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    os.remove(file_path)

    def image_callback(self, msg):
        self.get_logger().info(f"\n\nimage_callback start")
        # Converti il messaggio in immagine OpenCV
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Metti l'immagine nella coda
        self.img.put(cv_image)
       
   
        filename = "image.jpeg"
        full_path = os.path.join(self.camera_dir, filename)
        self.get_logger().info(f"\n\nimage_callback{full_path}")
        # Gestisci la coda (mantieni solo l'ultima immagine)
        if self.img.qsize() > 0:
            img_save=self.img.get()  # Rimuovi l'immagine precedente
            self.get_logger().info(f"Img saved")
            # Salva l'immagine
            success = cv2.imwrite(full_path,img_save )#cv_image
            if success:
                self.get_logger().info(f"Immagine salvata  : {full_path}")
                
            else:
                self.get_logger().info(f"Errore nel salvare l'immagine: {full_path}")



    def look_image(self, msg):
        try:
            imgs = list(self.img.queue)
            self.get_logger().info(str(len(imgs)))
            label=[]
            self.get_logger().info("____________----")
            for image in imgs:
                cv_image = image
                height, width, _ = cv_image.shape
   
                # Prepara l'immagine per YOLO
                blob = cv2.dnn.blobFromImage(cv_image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                self.net.setInput(blob)
                outs = self.net.forward(self.output_layers)

                # Inizializza le liste per le informazioni sugli oggetti rilevati
                class_ids = []
                confidences = []
                boxes = []

                # Elaborazione degli output di YOLO
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.5:
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)

                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)
                            

                
                for i in class_ids:
                    if (self.classes[i] not in label):
                        label.append(self.classes[i])
            self.get_logger().info(str(label))
            self.speak("ho visto ")
            self.look_resp(label)
            for l in label:
                self.speak(l)
                



        except Exception as e:
            self.get_logger().error(f"Error in image_callback: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    photo_controller = PhotoController()
    
    rclpy.spin(photo_controller)
    rclpy.shutdown()

if __name__ == "__main__":
    main()