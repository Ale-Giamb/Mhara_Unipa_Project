import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import random


class SensorsController(Node):
    def __init__(self):
        super().__init__('sensors_controller')
        self.parametri = ["BattitoCardiaco","PressioneSanguigna","TemperaturaCorporea","FrequenzaRespiratoria"]

        self.parametriVitali=self.create_publisher(String,'signs_controller',10)

        self.timer = self.create_timer(1.0, self.menu)  # chiama menu ogni 1 secondo (o modifica a piacere)


    def menu(self):
        try:
            x = int(input("Inserisci il paramaetro da alterare:\n(0)Battito Caridaco\n(1)Pressione Sanguigna\n(2)Temperatura Corporea\n(3)Frequenza Respiratoria\n"))
            if x < 0 or x > 3:
                print("COMANDO NON VALIDO\n")
                return
            y = int(input("(0)Valore Basso\n(1)Valore Normale\n(2)Valore Alto\n"))
            if y < 0 or y > 2:
                print("COMANDO NON VALIDO\n")
                return
            msg = String()
            msg.data = self.parametri[x] + " " + str(y)
            print("Comando inviato: "+msg.data+"\n")
            self.parametriVitali.publish(msg)
        except ValueError:
            print("COMANDO NON VALIDO\n")
            return

    def spin_node(self):
        self.get_logger().info("SensorsController in esecuzione...")
        rclpy.spin(self)

def main(args=None):
    rclpy.init(args=args)
    controller_node = SensorsController()
    try:
        controller_node.spin_node()
    except KeyboardInterrupt:
        pass

    controller_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
