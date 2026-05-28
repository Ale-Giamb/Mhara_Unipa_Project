import socket
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SocketServerNode(Node):
    def __init__(self):
        super().__init__('socket_server_node')

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', 5050))
        self.server_socket.listen(5)

        self.controller_pub = self.create_publisher(String, '/to_ros', 10)
        self.to_bdi_sub = self.create_subscription(String, '/to_bdi', self.send_to_bdi, 10)

        self.client_sockets = {}

        #self.clients = {}  # mappa: client_socket -> thread-safe queue o buffer

        threading.Thread(target=self.accept_connections, daemon=True).start()
        self.get_logger().info("ROS2 Socket Server con connessioni persistenti attivo")

    def accept_connections(self):
        while True:
            client_socket, address = self.server_socket.accept()
            self.get_logger().info(f"Nuovo client connesso: {address}")
            self.client_sockets[client_socket] = None  # puoi usare dict avanzato se servono metadati
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break  # connessione chiusa dal client

                self.get_logger().info(f"Messaggio ricevuto: {data}")

                msg = String()
                msg.data = data
                self.controller_pub.publish(msg)

                # Salva il client come "ultimo che ha parlato" per eventuale risposta
                self.client_sockets[client_socket] = data  # qui potresti usare un ID messaggio

        except Exception as e:
            self.get_logger().error(f"Errore nella comunicazione: {e}")
        finally:
            self.get_logger().info("Client disconnesso")
            del self.client_sockets[client_socket]
            client_socket.close()

    def send_to_bdi(self, msg):
        # Esempio: invia il messaggio a tutti i client connessi
        for client_socket in list(self.client_sockets.keys()):
            try:
                self.get_logger().info(f"Messaggio ricevuto: {msg}")
                client_socket.sendall((msg.data + "\n").encode())
            except Exception as e:
                self.get_logger().error(f"Errore durante invio al client: {e}")
                client_socket.close()
                del self.client_sockets[client_socket]

def main(args=None):
    rclpy.init(args=args)
    node = SocketServerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
