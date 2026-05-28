package example;

import jason.asSyntax.*;
import jason.environment.*;
import jason.asSyntax.parser.*;

import java.util.logging.*;
import java.io.*;
import java.net.*;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

public class Env extends Environment {

    private Logger logger = Logger.getLogger("bdi_agent." + Env.class.getName());
    private ServerSocket serverSocket;
    private boolean listening = true;

    @Override
    public void init(String[] args) {
        super.init(args);

        // Inizio thread UDP listener PER SENSORI SIMULATI
        new Thread(() -> {
            try (DatagramSocket socket = new DatagramSocket(9999)) {
                byte[] buffer = new byte[1024];
                while (true) {
                    DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                    socket.receive(packet);

                    String message = new String(packet.getData(), 0, packet.getLength()).trim();

                    try {
                        Literal l = ASSyntax.parseLiteral(message);

                        if (l.getFunctor().equals("parametri") && l.getArity() == 4) {
                            Term tBattito = l.getTerm(0);
                            Term tPressione = l.getTerm(1);
                            Term tTemperatura = l.getTerm(2);
                            Term tRespirazione = l.getTerm(3);

                            // Rimuove vecchie credenze
                            removePerceptsByUnif("sensori", ASSyntax.parseLiteral("battito(_)"));
                            removePerceptsByUnif("sensori", ASSyntax.parseLiteral("pressione(_)"));
                            removePerceptsByUnif("sensori", ASSyntax.parseLiteral("temperatura(_)"));
                            removePerceptsByUnif("sensori", ASSyntax.parseLiteral("respirazione(_)"));

                            // Aggiunge nuove credenze
                            Literal battito = ASSyntax.createLiteral("battito", tBattito);
                            Literal pressione = ASSyntax.createLiteral("pressione", tPressione);
                            Literal temperatura = ASSyntax.createLiteral("temperatura", tTemperatura);
                            Literal respirazione = ASSyntax.createLiteral("respirazione", tRespirazione);

                            addPercept("sensori", battito);
                            addPercept("sensori", pressione);
                            addPercept("sensori", temperatura);
                            addPercept("sensori", respirazione);

                        } else {
                            addPercept("sensori", l);
                        }
                    } catch (ParseException e) {
                        logger.warning("[UDP] Errore parsing messaggio: " + message);
                    }
                }
            } catch (IOException e) {
                logger.warning("[UDP] Errore socket UDP: " + e.getMessage());
            }
        }).start();

        new Thread(() -> {
            try {
                Socket socket = new Socket("127.0.0.1", 5050);
                BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));

                logger.info("[TCP] Connessione stabilita con ROS su porta 5050.");

                String response;
                while ((response = in.readLine()) != null) {
                    logger.info("[TCP] Messaggio ricevuto da ROS: " + response);

                    // Esempio: aggiungi come percezione
                    try {
                       JSONObject json = new JSONObject(response);

                        String messaggio = json.getString("messaggio");
                        
                        if ("start".equals(messaggio)) {
                            logger.info("Sono dentrooooooo");
                            Literal perc = ASSyntax.createLiteral("start", new Term[] {
                                new StringTermImpl(messaggio)
                            });
                            addPercept(perc);
                        }else{
                            String agente = json.getString("agente");
                            String percept = json.getString("percept");
                            Literal perc = ASSyntax.createLiteral(percept, new Term[] {
                                new StringTermImpl(messaggio)
                            });

                            addPercept(agente, perc);
                        }

                    } catch (JSONException e) {
                        logger.warning("[TCP] Errore nel parsing del messaggio JSON: " + response);
                    }

                }

                socket.close();
                logger.warning("[TCP] Connessione terminata.");

            } catch (IOException e) {
                logger.warning("[TCP] Errore nella connessione con ROS: " + e.getMessage());
            }
        }).start();
    }


    @Override
    public boolean executeAction(String agName, Structure action) {
        String actionName = action.getFunctor();

        if (actionName.equals("connect_to_socket") && action.getArity() == 3) {  // 3 parametri
            try {

                String serverAddress = action.getTerm(0).toString().replaceAll("\"", "");
                int port = Integer.parseInt(action.getTerm(1).toString());
                String message = action.getTerm(2).toString();
                if (message.startsWith("\"") && message.endsWith("\"")) {
                    message = message.substring(1, message.length() - 1);
                }

                boolean response = SocketClient.sendMessage(logger, serverAddress, port, message, this);

                return true;
            } catch (Exception e) {
                logger.warning("Errore nell'azione connet_to_socket: " + e.getMessage());
                return false;
            }
        }else if (actionName.equals("calcolo_giorni_dall_ultimo_test")&& action.getArity() == 1){
            try {
                StringTermImpl dataTerm = (StringTermImpl) action.getTerm(0);
                String dataStr = dataTerm.getString(); // Es. "2025-06-15"

                LocalDate dataRicevuta = LocalDate.parse(dataStr); // Formato YYYY-MM-DD
                LocalDate oggi = LocalDate.now();

                long differenzaGiorni = ChronoUnit.DAYS.between(dataRicevuta, oggi);

                Literal differenza = ASSyntax.createLiteral("giorni_differenza", new NumberTermImpl(differenzaGiorni));
                removePerceptsByUnif(agName, ASSyntax.parseLiteral("giorni_differenza(_)")); //Rimuovo le vecchie date
                addPercept(agName, differenza);

                //logger.info("Giorni di differenza: " + differenzaGiorni);

                return true;

            } catch (Exception e) {
                logger.warning("Errore confronto data: " + e.getMessage());
                return false;
            }

        }

        logger.info("Azione sconosciuta: " + action);
        return false;
    }

    @Override
    public void stop() {
        super.stop();
    }

    private void processMessage(String message) {
        try {
            if (message.startsWith("sensor_data(")) {
                String[] parts = message.replace("sensor_data(", "").replace(")", "").split(",");
                if (parts.length == 2) {
                    String tipo = parts[0].trim();
                    String valore = parts[1].trim();

                    removePerceptsByUnif(Literal.parseLiteral(tipo + "(_)"));

                    // Aggiunge la nuova credenza
                    Literal newBelief = Literal.parseLiteral(tipo + "(" + valore + ")");
                    addPercept(newBelief);

                    logger.info("Credenza aggiornata: " + newBelief);
                }
            }
        } catch (Exception e) {
            logger.warning("Errore elaborazione messaggio: " + e.getMessage());
        }
    }
}


class SocketClient {
    public static boolean sendMessage(Logger logger, String serverAddress, int port, String message, Environment env) {
    try (Socket socket = new Socket(serverAddress, port);
         PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {

        logger.info("Invio messaggio al server: " + message);
        out.println(message);
        return true;

    } catch (IOException e) {
        e.printStackTrace();
        return false;
    }
}



private static void analizza(Logger logger, Environment env, JSONArray jsonArray) {
      for(int i = 0; i < jsonArray.length(); ++i) {
        JSONObject jsonObject = jsonArray.getJSONObject(i);
        logger.info(jsonObject.toString());

        String nome = jsonObject.getString("a.nome");
        Literal newPerception = ASSyntax.createLiteral("nome", new Term[]{ASSyntax.createString(nome)});
        env.addPercept(new Literal[]{newPerception});
      }

   }

}

