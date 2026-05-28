import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import json
import random
import time
from urllib.parse import quote
from datetime import datetime

class MiniCog:
    def __init__(self, node):
        self.node = node
        self.logger = node.get_logger()
        self.comunica = node.create_publisher(String, "/to_ros", 10)
        self.show_pub = node.create_publisher(String,'/show',10)
        self.hide_pub = node.create_publisher(Bool,'/hide',10)

        self.query_al_db = node.create_publisher(String,'/query_al_db',10)
        self.consiglia_esercizio = node.create_publisher(String,'/consiglia_esercizio',10)

        self.orologio_input_sub = node.create_subscription(String,'/orologio_input', self.ricevi_orologio_input, 10)
        self.fine_parole_sub  = node.create_subscription(Bool,'/fine_visualizzazione_3_parole', self.fine_visualizzazione_3_parole, 10)
        self.verifica_parole_selezionate_sub = node.create_subscription(String,'/parole_selezionate', self.verifica_parole_selezionate, 10)
        self.get_data_sub = node.create_subscription(String,'/get_data', self.set_data,10)

        self.orologio_input = None 
        self.timer_verifica = None  

        self.nome = 'Mario'
        self.cognome = 'Rossi'

        self.punteggio_orologio = 0
        self.punteggio_parole = 0

    def set_data(self,msg):
        data = json.loads(msg.data)
        self.nome = data.get("nome")
        self.cognome = data.get("cognome")
    
    def esegui_test(self):
        self.parole = random.sample([
            "Mela", "Chiave", "Libro", "Gatto", "Sedia", "Fiume",
            "Fiore", "Orologio", "Pane", "Albero", "Scuola", "Luce"
        ], 3)

        self.pubblica("Stiamo per iniziare il test MiniCog.")
        self.node.get_logger().info("[MINICOG] Inizio del test")

        w1, w2, w3 = self.parole
        url = f"minicog_parole.html?w1={w1}&w2={w2}&w3={w3}"

        msg = String()
        msg.data = url
        self.logger.info(f"[MINICOG] {self.parole}")
        self.logger.info(f"[MINICOG] {url}")

        self.show_pub.publish(msg)

        self.pubblica("Ricorda queste tre parole...")
        for parola in self.parole:

            self.pubblica(parola)
            self.logger.info(f"[MINICOG] {parola}")

            time.sleep(2)

    def pubblica(self, testo):
        msg = String()
        msg.data = json.dumps({"nodo":"pepper_code","comando":"messaggio","messaggio": testo})
        self.comunica.publish(msg)
        
    def fine_visualizzazione_3_parole(self, testo):
        
        self.pubblica("Ti mostrerò la schermata di un orologio, inserisci i numeri nella posizione corretta")

        msg = String()
        msg.data = "minicog_orologio.html"
        self.show_pub.publish(msg)
        
    def ricevi_orologio_input(self, msg):
        self.logger.info(f"[MINICOG] Risposta orologio ricevuta: {self.orologio_input}")
        orologio = json.loads(msg.data)
        corrette = 0
        for i in range(1, 13):
            key = f"ora{i}"
            valore_utente = orologio.get(key)
            valore_atteso = str(i)  # oppure metti qui valori diversi se hai un test personalizzato
            if valore_utente == valore_atteso:
                corrette += 1

        self.punteggio_orologio = corrette

        if corrette == 12:
            messaggio = "Perfetto! Hai completato il test dell'orologio senza errori."
        elif corrette >= 9:
            messaggio = f"Hai inserito {corrette} numeri corretti su 12. Ottimo lavoro!"
        elif corrette >= 6:
            messaggio = f"Hai inserito {corrette} numeri corretti su 12. Continua ad allenarti!"
        else:
            messaggio = f"Hai inserito solo {corrette} numeri corretti su 12. Puoi fare di meglio."

        self.pubblica(messaggio)

        self.pubblica("Ritorniamo alle parole dette prima")
        self.mostra_verifica_parole()

    def mostra_verifica_parole(self):
        self.pubblica("Adesso inserisci le parole che ti ho mostrato all'inizio.")

        # Mostra la pagina HTML per la verifica
        url = "minicog_parole_verifica.html"

        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def verifica_parole_selezionate(self, msg):
        try:
            dati = json.loads(msg.data)
            selezionate = dati.get("selezionate", [])
            self.logger.info(f"[MINICOG] Parole selezionate dall'utente: {selezionate}")

            corrette = [p for p in selezionate if p in self.parole]
            self.logger.info(f"[MINICOG] Parole corrette: {corrette} su 3")
            self.pubblica(f"Hai ricordato {len(corrette)} parole su 3.")

            self.punteggio_parole = len(corrette)

            # Torna alla schermata di default
            b = Bool()
            b.data = True
            self.hide_pub.publish(b)

            # Calcolo dello stato cognitivo finale
            self.valuta_stato_cognitivo()

        except json.JSONDecodeError:
            self.logger.error("[MINICOG] Errore nel parsing del messaggio ricevuto per la verifica parole.")

    def valuta_stato_cognitivo(self):
        punteggio_totale = self.punteggio_orologio + self.punteggio_parole  # max 15
        stato = ""
        if punteggio_totale >= 12:
            stato = "Ottimo"
            messaggio = f"Stato cognitivo buono. Hai totalizzato {punteggio_totale} su 15."
        elif punteggio_totale >= 8:
            stato = "Moderata"
            messaggio = f"Stato cognitivo nella norma, con alcune imprecisioni. Punteggio: {punteggio_totale} su 15."
        else:
            stato = "Pessima"
            messaggio = f"Attenzione: possibili difficoltà cognitive. Hai totalizzato {punteggio_totale} su 15."

        self.pubblica(messaggio)

        timestamp = datetime.now().strftime("%Y-%m-%d")
        query_test = f'''
        MATCH (a:Anziano)-[:ESSERE_VALUTATO]->(t:TestCognitivo)
        SET t.data = '{timestamp}', t.punteggio = '{punteggio_totale}', t.tipo='MiniCog'
        RETURN t
        '''
        msg = String()
        msg.data = query_test
        self.query_al_db.publish(msg)

        # Aggiornare lo stato cognitivo dell'anziano
        query_stato = f'''
        MATCH (s:StatoCognitivo)
        SET s.stato = '{stato}'
        RETURN s'''
        
        msg.data = query_stato
        self.query_al_db.publish(msg)
        

        msg = String()
        prompt = f"""
        Considerando le mie informazioni, che sono un anziano di nome {self.nome} e cognome {self.cognome} che ha ottenuto un punteggio di {punteggio_totale} su 15 in un test cognitivo, il suo stato cognitivo è valutato come {stato}

        In base a queste informazioni e a quello che trovi nella base di conoscenza, 
        scegli delle azioni legate alla stimolazione delle funzionalità cognitive, 
        tenendo conto dello stato cognitivo, della mobilità, delle attività preferite, 
        delle patologie e dello stato emotivo. Se è arrabbiato, ad esempio, 
        suggerisci attività rilassanti e usa un tono rassicurante. Se è felice, puoi proporre attività che stimolino ulteriormente la sua gioia.        
        Suggerisci azioni specifiche basate sul suo stato cognitivo e fisico.
        """
        msg.data = prompt
        # Pubblicazione del messaggio
        self.consiglia_esercizio.publish(msg)

        b = Bool()
        b.data = True
        self.hide_pub.publish(b)

    # Disattiva questo timer: viene invocato una sola volta, quindi nulla da fare

class MUST:
    def __init__(self, node):
        self.node = node
        self.logger = node.get_logger()
        self.comunica = node.create_publisher(String, "/to_ros", 10)
        self.show_pub = node.create_publisher(String,'/show',10)
        self.hide_pub = node.create_publisher(Bool,'/hide',10)

        self.consiglia_esercizio = node.create_publisher(String,'/consiglia_esercizio',10)

        self.must_test1_sub = node.create_subscription(String,'/must_test1', self.must_test1,10)
        self.must_test2_sub = node.create_subscription(String,'/must_test2', self.must_test2,10)
        self.must_test3_sub = node.create_subscription(String,'/must_test3', self.must_test3,10)

        self.get_data_sub = node.create_subscription(String,'/get_data', self.set_data,10)

        self.query_al_db = node.create_publisher(String,'/query_al_db',10)

        self.bmi = 0
        self.stato = "Normopeso"
        self.punteggio = 0

        self.nome = 'Mario'
        self.cognome = 'Rossi'

    def pubblica(self, testo):
        msg = String()
        msg.data = json.dumps({"nodo":"pepper_code","comando":"messaggio","messaggio": testo})
        self.comunica.publish(msg)

    def set_data(self,msg):
        data = json.loads(msg.data)
        self.nome = data.get("nome")
        self.cognome = data.get("cognome")
        
        
    def esegui_test(self):
        self.pubblica("Stiamo per iniziare il test MUST.")
        self.pubblica("Ti farò alcune semplici domande su peso, alimentazione e salute generale. " \
        "Rispondi con calma, non c’è una risposta giusta o sbagliata.")
        self.pubblica("Come prima cosa inserisci il tuo attuale peso e la tua altezza. Se non consci precisamente i dati vabene anche una stima")

        url = "dati_must.html"
        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def must_test1(self,msg):
        try:
            # Esempio: "70,175"
            peso_str, altezza_str = msg.data.split(',')
            peso = float(peso_str)
            altezza = float(altezza_str)

            self.node.get_logger().info(f"[MUST] Peso: {peso} kg")
            self.node.get_logger().info(f"[MUST] Altezza: {altezza} cm")

            # Puoi ora calcolare l'IMC (BMI)
            altezza_m = altezza / 100  # da cm a metri
            bmi = peso / (altezza_m ** 2)
            self.bmi = bmi
            self.node.get_logger().info(f"[MUST] BMI calcolato: {bmi:.2f}")

            if bmi < 18.5:
                self.stato = "Sottopeso"
                self.punteggio += 1
            elif 18.5 <= bmi < 25:
                self.stato = "Normopeso"
                self.punteggio += 0
            elif 25 <= bmi < 30:
                self.stato = "Sovrappeso"
                self.punteggio += 1
            else:
                self.stato = "Obeso"
                self.punteggio += 2

            #################
            query_stato_nutrizionale = f'''
            MATCH (s:StatoNutrizionale)
            SET s.BMI = '{self.punteggio}', s.statoFisico = '{self.stato}'
            RETURN s'''

            msg = String()
            msg.data = query_stato_nutrizionale
            self.query_al_db.publish(msg)

            self.pubblica(f"Il BMI calcolato ha stimato che sei nello stato {self.stato}")
            self.pubblica("Adesso cerca di ricordare se negli ultimi 3 mesi hai rilevato una perdita di peso")
            ########################
            
            url = "autovalutazione_3_opzioni.html?param=must2&op1=Nessuna%20perdita%20di%20peso&op2=Lieve%20perdita%20di%20peso&op3=Notevole%20perdita%20di%20peso&azioni1=0&azioni2=1&azioni3=2"

            msg = String()
            msg.data = url
            self.show_pub.publish(msg)

        except ValueError:
            self.node.get_logger().warn("[MUST] Errore nel parsing dei dati peso/altezza.")

    def must_test2(self,valore):
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test1.")
        self.pubblica("In questo periodo sei in un periodo di digiuno? Inserisci da quanti giorni")
        url = "autovalutazione_3_opzioni.html?param=must3&op1=0%20giorni&op2=1-2%20giorni&op3=3-5%20giorni&azioni1=0&azioni2=1&azioni3=2"

        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def must_test3(self,valore):
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test1.")


        if self.punteggio >= 4:
            stato = "Mal Nutrito"
            messaggio = "Attenzione! Alto rischio di malnutrizione"
        elif self.punteggio >= 2:
            stato = "Normale"
            messaggio = "Bene! Rischio medio di malnutrizione"
        else:
            messaggio = "Ottimo! Basso rischio di malnutrizione"
            stato = "Ben Nutrito"

        self.pubblica(f"Test completato {messaggio}, adesso genero delle ricette adatte a te")

        timestamp = datetime.now().strftime("%Y-%m-%d")
        query_test_nutrizionale = f'''
        MATCH (a:Anziano)-[:ESSERE_VALUTATO]->(tn:TestNutrizionale)
        SET tn.punteggio = '{self.punteggio}', tn.data = '{timestamp}', tn.tipo='MUST'
        RETURN tn
        '''
        msg = String()
        msg.data = query_test_nutrizionale
        self.query_al_db.publish(msg)
        
        query_stato_nutrizionale = f'''
        MATCH (s:StatoNutrizionale)
        SET s.stato = '{stato}'
        RETURN s'''
        
        msg.data = query_stato_nutrizionale
        self.query_al_db.publish(msg)


        # Creazione del messaggio String
        msg = String()
        msg.data = f"In base alle ricette presenti nella base di conoscenza, seleziona delle ricette per me, un anziano di nome {self.nome} e cognome {self.cognome}. \
        Tieni conto delle informazioni e dei vincoli presenti nella base di\
        conoscenza, come le intolleranze alimentari specifiche. Non menzionare intolleranze che non sono nel mio profilo. Se riscontri uno stato di malnutrizione,\
        ti prego di spronarmi di mangiare qualcosa di nutriente per migliorare la mia condizione."

        # Pubblicazione del messaggio
        self.consiglia_esercizio.publish(msg)

        b = Bool()
        b.data = True
        self.hide_pub.publish(b)

class Mobilita:
    def __init__(self, node):
        self.node = node
        self.logger = node.get_logger()
        self.comunica = node.create_publisher(String, "/to_ros", 10)
        self.show_pub = node.create_publisher(String,'/show',10)
        self.hide_pub = node.create_publisher(Bool,'/hide',10)
    
        self.consiglia_esercizio = node.create_publisher(String,'/consiglia_esercizio',10)

        self.risultato_test1 = node.create_subscription(String,'/risultato_test1', self.test2, 10)
        self.risultato_test2 = node.create_subscription(String,'/risultato_test2', self.test3, 10)
        self.risultato_test3 = node.create_subscription(String,'/risultato_test3', self.test4, 10)
        self.risultato_test4 = node.create_subscription(String,'/risultato_test4', self.test5, 10)
        self.risultato_test5 = node.create_subscription(String,'/risultato_test5', self.risultato_test, 10)
        
        self.get_data_sub = node.create_subscription(String,'/get_data', self.set_data,10)

        self.query_al_db = node.create_publisher(String,'/query_al_db',10)

        self.punteggio = 0
        self.bmi = 0

        self.nome = 'Mario'
        self.cognome = 'Rossi'

    def pubblica(self, testo):
        msg = String()
        msg.data = json.dumps({"nodo":"pepper_code","comando":"messaggio","messaggio": testo})
        self.comunica.publish(msg)

    def set_data(self,msg):
        data = json.loads(msg.data)
        self.nome = data.get("nome")
        self.cognome = data.get("cognome")

    def esegui_test(self):
        self.pubblica("Stiamo per iniziare il test Mobilità.")
        '''self.pubblica("Iniziamo con il test di equilibrio. " \
        "Mettiti in piedi accanto a una superficie stabile, come una sedia o un tavolo.")
        self.pubblica("Per prima cosa, unisci i piedi affiancati e mantieni questa posizione per dieci secondi.")
        self.pubblica("Conta per quanto tempo riesci a rimanere in questa posizione, aiutati con il timer nello schermo")
'''
        url = "autovalutazione_5_opzioni.html?param=test5&"

        #url = f"autovalutazione_3_opzioni.html?param=test1&op1=%3E10&op2=%3C10&op3=impossibile&azioni1=1&azioni2=0&azioni3=0"

        msg = String()
        msg.data = url

        self.show_pub.publish(msg)

    def test2(self,valore):
        self.pubblica("Ottimo! Ora prova a stare in piedi con i piedi sfalsati, uno leggermente avanti rispetto all'altro, come se stessi facendo un piccolo passo.")
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test1.")
        url = f"autovalutazione_3_opzioni.html?param=test2&op1=%3E10&op2=%3C10&op3=impossibile&azioni1=1&azioni2=0&azioni3=0"

        msg = String()
        msg.data = url
        self.show_pub.publish(msg)
    
    def test3(self,valore):
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test2.")
        self.pubblica("Benissimo! Ora, prova a stare in piedi con un piede davanti all'altro, in modo che il tallone tocchi la punta del piede dietro.")
        url = f"autovalutazione_3_opzioni.html?param=test3&op1=%3E10&op2=%3C10&op3=impossibile&azioni1=2&azioni2=1&azioni3=0"
        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def test4(self,valore):
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test3.")
        self.pubblica("Adesso eseguiremo il test della camminata. Dovrai camminare a passo normale per quattro metri, in linea retta")
        self.pubblica("Seleziona in quanto tempo li percorri")
        opzioni = ["0–4", "4–6", "6–9", ">9", "Impossibile"]
        url = "autovalutazione_5_opzioni.html?param=test4&" + "&".join(
            [f"op{i+1}={quote(opzioni[i])}" for i in range(len(opzioni))]
        )


        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def test5(self,valore):
        try:
            self.punteggio += int(valore.data.strip())
        except ValueError:
            self.logger.warn("Punteggio non numerico ricevuto in test4.")
        self.pubblica("Adesso eseguiremo il test del sollevamento dalla sedia. Al mio via, prova ad alzarti e sederti 5 volte il più velocemente possibile, senza usare le braccia.")
        opzioni = ["0–12", "12–15", "15–18", "18–60", "Impossibile"]
        url = "autovalutazione_5_opzioni.html?param=test5&" + "&".join(
            [f"op{i+1}={quote(opzioni[i])}" for i in range(len(opzioni))]
        )

        msg = String()
        msg.data = url
        self.show_pub.publish(msg)

    def risultato_test(self, valore):
        try:
            voto = int(valore.data.strip())
            self.punteggio += voto
        except (ValueError, AttributeError) as e:
            self.logger.warn(f"Punteggio non valido ricevuto in test5: {e}")
            return

        # Mostra il risultato finale
        self.logger.info(f"[MOBILITA] Punteggio finale: {self.punteggio}")

        if self.punteggio >= 8:
            stato = 'Mobilità Alta'
            valutazione = "Ottimo livello di mobilità."
        elif self.punteggio >= 4:
            stato = 'Mobilità Moderata'
            valutazione = "Mobilità moderata, potrebbe essere utile un supporto."
        else:
            stato = 'Mobilità Bassa'
            valutazione = "Mobilità ridotta."


        timestamp = datetime.now().strftime("%Y-%m-%d")

        query_test = f'''
        MATCH (a:Anziano)-[:ESSERE_VALUTATO]->(t:TestMobilita)
        SET t.punteggio = '{self.punteggio}', t.data = '{timestamp}'
        RETURN t
        '''
        msg = String()
        msg.data = query_test
        self.query_al_db.publish(msg)

        # Aggiornare lo stato cognitivo dell'anziano
        query_stato = f'''
        MATCH (a:StatoMobilita)
        SET a.stato = \'{stato}\'
        RETURN a'''
        
        msg.data = query_stato
        self.query_al_db.publish(msg)

        self.pubblica("Test completato.")
        self.pubblica(valutazione)


        # Creazione del messaggio String
        msg = String()
        msg.data = f"In base alle attività presenti nella base di conoscenza, scegli delle attività per me, un Anziano di nome: {self.nome}, e cognome: {self.cognome}, da svolgere per migliorare la sua mobilità, tenendo conto delle informazioni relative alla sua condizione fisica, cognitiva e emotiva."

        self.consiglia_esercizio.publish(msg)

        b = Bool()
        b.data = True
        self.hide_pub.publish(b)


class TestReceiver(Node):
    def __init__(self):
        super().__init__('test_node')
        
        self.query_al_db = self.create_publisher(String,'/query_al_db',10)

        self.subscription = self.create_subscription(
            String,
            '/test',
            self.listener_callback,
            10
        )
        self.get_logger().info('[TEST RECEIVER] Nodo inizializzato. In attesa dei test...')

        # Mappa test disponibili
        self.test_registry = {
            "minicog": MiniCog,
            "must": MUST,
            "mobilita": Mobilita
        }


    def listener_callback(self, msg):
        try:
            data = json.loads(msg.data)
            nome_test = data.get('test', 'undefined').lower()
            self.get_logger().info(f"[TEST RECEIVER] Test da effettuare ricevuto: {nome_test}")

            if nome_test in self.test_registry:
                test_classe = self.test_registry[nome_test]
                test_instance = test_classe(self)
                test_instance.esegui_test()
            else:
                self.get_logger().warn(f"[TEST RECEIVER] Test non riconosciuto: {nome_test}")
        except json.JSONDecodeError as e:
            self.get_logger().error(f"[TEST RECEIVER] Errore nel parsing del JSON: {e}")
        except Exception as e:
            self.get_logger().error(f"[TEST RECEIVER] Errore generico: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = TestReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()