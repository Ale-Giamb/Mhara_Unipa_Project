import qi
import rclpy
from rclpy.node import Node
import sys
from std_msgs.msg import Bool, String
import time
import threading
import os
import numpy as np
import cv2

# --- Selenium + Chrome ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class qi_unipa_tablet(Node):
    def __init__(self):
        super().__init__('qi_unipa_tablet')

        # --- Parametri ROS ---
        self.declare_parameter('ip', '192.168.0.161')
        self.declare_parameter('port', 9559)
        
        ip_robot = self.get_parameter('ip').get_parameter_value().string_value
        port_robot = self.get_parameter('port').get_parameter_value().integer_value
       

        # --- Connessione al robot Pepper ---
        self.session = self.set_connection(ip_robot, port_robot)
        self.tabletService = self.session.service("ALTabletService")
        self.tabletService.resetTablet()
        # --- Sottoscrizioni ROS ---
        self.show_sub = self.create_subscription(String, "/show", self.show, 10)
        self.show_tablet_sub = self.create_subscription(String, "/show_tablet", self.show_tablet, 10)
        self.hide_sub = self.create_subscription(Bool, "/hide", self.hide, 10)
        self.ip_sub = self.create_subscription(String, "/ip", self.set_ip, 10)
        self.ip_tablet_sub = self.create_subscription(String, "/ip_tablet", self.set_ip_tablet, 10)
        self.image_sub = self.create_subscription(
            Bool,
            "/image_tablet",
            self.show_tablet_stream_callback,
            10
        )

        # --- Variabili di stato ---
        self.webserver_ip = ""
        self.tablet_ip = ""
        self.tablet_lock = threading.Lock()
        self.last_url = ""
        self.driver = None  # Selenium driver (inizializzato solo se serve)

        self.get_logger().info("Nodo tablet avviato correttamente")

        # --- Configurazione browser Chrome ---
        self.options = Options()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")

        # Se vuoi farlo partire in background, scommenta la riga seguente:
        # self.options.add_argument("--headless")

        self.setup_browser()

    def setup_browser(self):
        """Avvia il browser locale (Chrome) se la modalità è 'local_selenium'."""
      
      
        try:
            self.get_logger().info("Avvio del browser locale (Chrome) con Selenium...")
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=self.options
            )
            self.get_logger().info("Browser locale (Chrome) avviato con successo.")
        except Exception as e:
            self.get_logger().error(f"Errore nell'avvio di Chrome: {e}")
            self.driver = None

    def set_ip(self, msg):
        self.webserver_ip = msg.data

    def set_ip_tablet(self, msg):
        self.tablet_ip = msg.data

    def set_connection(self, ip, port):
        session = qi.Session()
        try:
            session.connect(f"tcp://{ip}:{port}")
            self.get_logger().info(f"Connesso a Pepper su {ip}:{port}")
        except RuntimeError:
            self.get_logger().error(
                f"Non riesco a connettermi a Naoqi su ip '{ip}' e porta {port}.\n"
                "Controlla gli argomenti dello script."
            )
            sys.exit(1)
        return session

    def show(self, msg):
        """Mostra la pagina richiesta sul tablet o nel browser locale."""
        with self.tablet_lock:
            try:
                webPage = msg.data
                full_url = f"{self.tablet_ip}/{webPage}"  # o webserver_ip se vuoi

                # Controlla se la pagina è già quella mostrata
                if full_url == self.last_url:
                    self.get_logger().info(f"Pagina già aperta: {full_url}, salto il reload")
                    return  # esci senza fare nulla

                self.get_logger().info(f"Richiesta visualizzazione: {full_url}")

                # Aggiorna Chrome solo se necessario
                if self.driver:
                    self.get_logger().info("[BROWSER LOCALE] Caricamento pagina in Chrome...")
                    self.driver.get(full_url)
                    self.get_logger().info(f"Pagina caricata nel browser locale: {full_url}")

                self.last_url = full_url

                # Mostra la pagina sul tablet Pepper
                #self.tabletService.showWebview(full_url)

            except Exception as e:
                self.get_logger().error(f"Errore durante la funzione show: {e}")

    def show_tablet(self, msg):
        """Mostra la pagina richiesta sul tablet o nel browser locale."""
        with self.tablet_lock:
            try:
                webPage = msg.data
                full_url = f"{self.tablet_ip}/{webPage}" 

                self.last_url = full_url

                # Mostra la pagina sul tablet Pepper
                #self.tabletService.showWebview(full_url)

            except Exception as e:
                self.get_logger().error(f"Errore durante la funzione show: {e}")

    def show_tablet_stream_callback(self, msg):
        page_name = "mostra_immagine.html"
        #page_name = "si_no.html"

        msg = String()
        msg.data = page_name

        #self.show(msg)
        url = f"{self.tablet_ip}/{page_name}"
        
        try:
            #self.tabletService.showWebview(url)
            pass
        except Exception as e:
            self.get_logger().error(f"Errore nel mostrare il video sul tablet: {e}")


    def hide(self, msg):
        """Nasconde la pagina visualizzata."""
        with self.tablet_lock:
    
            self.get_logger().info("[BROWSER LOCALE] Pulisco la schermata di Chrome.")
            self.driver.get("about:blank")
           

    def cleanup(self):
        """Pulizia risorse prima di terminare il nodo."""
        self.get_logger().info("Esecuzione pulizia nodo...")
        try:
            if self.tabletService:
                self.tabletService.hideWebview()
        except Exception as e:
            self.get_logger().warn(f"Impossibile nascondere la webview: {e}")

        if self.driver:
            self.get_logger().info("Chiusura del browser locale Selenium (Chrome)...")
            try:
                self.driver.quit()
            except Exception:
                pass


def main(args=None):
    rclpy.init(args=args)
    time.sleep(0.5)
    node = qi_unipa_tablet()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


