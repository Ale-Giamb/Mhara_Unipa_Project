import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import random
import socket


class SensorsNode(Node):
    def __init__(self):
        super().__init__('sensors_node')
        
        self.parametri = [
            "BattitoCardiaco",
            "PressioneSistolica",
            "PressioneDiastolica",
            "TemperaturaCorporea",
            "FrequenzaRespiratoria"
        ]

        self.statoParametri = [1,1,1,1,1] # valori da 0 (basso), 1 (normale), 2 (alto)

        # limiti: 3 per ciascun parametro (basso, normale, alto)
        self.limiteInferiore = [30, 70, 110,  # Battito
                                80, 110, 150,        # Pressione Sistolica
                                60, 70, 90,          # Pressione Diastolica
                                34.0, 36.0, 38.0,  # Temperatura
                                5, 13, 26]  # Frequenza

        self.limiteSuperiore = [40, 85, 120,
                                100, 130, 160,
                                70, 80, 100,
                                35.0, 37.0, 39.0,
                                8, 18, 30]
        
        self.pub = self.create_publisher(String, 'vital_signs', 10)

        self.sub = self.create_subscription(String, 'signs_controller', self.modifica_parametri, 10)

        self.udp_ip = "127.0.0.1"
        self.udp_port = 9999
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



    def spin_node(self):
        self.get_logger().info("SensorsNode in esecuzione...")
        rclpy.spin(self)

    def genera_parametri(self):
        
        index_bc=self.statoParametri[0]
        index_ps=self.statoParametri[1]+3
        index_tc=self.statoParametri[2]+6
        index_fr=self.statoParametri[3]+9
        index_fr=self.statoParametri[4]+12

        battito = random.randint(self.limiteInferiore[index_bc], self.limiteSuperiore[index_bc])  
        pressioneSistolica = random.randint(self.limiteInferiore[index_ps], self.limiteSuperiore[index_ps])
        pressioneDiastolica = random.randint(self.limiteInferiore[index_ps], self.limiteSuperiore[index_ps])
        temperatura = round(random.uniform(self.limiteInferiore[index_tc], self.limiteSuperiore[index_tc]), 1)
        respirazione = random.randint(self.limiteInferiore[index_fr], self.limiteSuperiore[index_fr])

        msg = String()
        stampa_messaggio = f"Battito: {battito} bpm, pressioneSistolica: {pressioneSistolica} mmHg, pressioneDiastolica: {pressioneDiastolica}, Temperatura: {temperatura} °C, Respirazione: {respirazione} att/min"
        self.get_logger().info("Pubblico: " + stampa_messaggio)
        msg.data = f"parametri({battito},{pressioneSistolica},{pressioneDiastolica},{temperatura},{respirazione})"
        #self.pub.publish(msg)
        self.sock.sendto(msg.data.encode(), (self.udp_ip, self.udp_port))


    def modifica_parametri(self,msg):
        nome, valore = msg.data.strip().split()
        indice = self.parametri.index(nome)
        valore = int(valore)
        self.statoParametri[indice] = valore

        index_bc=self.statoParametri[0]
        index_ps=self.statoParametri[1]+3
        index_tc=self.statoParametri[2]+6
        index_fr=self.statoParametri[3]+9
        index_fr=self.statoParametri[4]+12

        battito = random.randint(self.limiteInferiore[index_bc], self.limiteSuperiore[index_bc])  
        pressioneSistolica = random.randint(self.limiteInferiore[index_ps], self.limiteSuperiore[index_ps])
        pressioneDiastolica = random.randint(self.limiteInferiore[index_ps], self.limiteSuperiore[index_ps])
        temperatura = round(random.uniform(self.limiteInferiore[index_tc], self.limiteSuperiore[index_tc]), 1)
        respirazione = random.randint(self.limiteInferiore[index_fr], self.limiteSuperiore[index_fr])

        msg = String()
        stampa_messaggio = f"Battito: {battito} bpm, pressioneSistolica: {pressioneSistolica} mmHg, pressioneDiastolica: {pressioneDiastolica}, Temperatura: {temperatura} °C, Respirazione: {respirazione} att/min"
        self.get_logger().info("Pubblico: " + stampa_messaggio)
        msg.data = f"parametri({battito},{pressioneSistolica},{pressioneDiastolica},{temperatura},{respirazione})"
        #self.pub.publish(msg)
        self.sock.sendto(msg.data.encode(), (self.udp_ip, self.udp_port))

    

def main(args=None):
    rclpy.init(args=args)
    controller_node = SensorsNode()

    try:
        controller_node.spin_node()
    except KeyboardInterrupt:
        pass

    controller_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
