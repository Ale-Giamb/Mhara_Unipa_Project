//---------------------------------------------------------------
+!send_message(Server, Port, Message) <- 
    .print("Invio messaggio a ", Server, ":", Port, " -> ", Message);
    connect_to_socket(Server, Port, Message).

+!comunica(M)<-
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"", M ,"\"}",Msg);
  !send_message("localhost", 5050, Msg).
//-------------------------------Sensori----------------------------------------
+!valuta_temperatura(T): T > 38
  <- .print("[COORDINATORE] Stato di Febbre rilevato: ", T);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Febbre rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_temperatura(T): T < 35
  <- .print("[COORDINATORE] Stato di Ipotermia rilevato: ", T);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Ipotermia rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_respirazione(R): R > 24
  <- .print("[COORDINATORE] Frequenza Respiratoria alta: ", R);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Techipnèa rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_respirazione(R): R < 10
  <- .print("[COORDINATORE] Frequenza Respiratoria bassa: ", R);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Bradipnèa rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_pressione(P): P > 140
  <- .print("[COORDINATORE] Pressione Sanguigna alta: ", P);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Ipertensione rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_pressione(P): P < 90
  <- .print("[COORDINATORE] Pressione Sanguigna bassa: ", P);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Ipotensione rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_battito(B): B > 100
  <- .print("[COORDINATORE] Battito Cardiaco alto: ", B);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Tachicardìa rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!valuta_battito(B): B < 50
  <- .print("[COORDINATORE] Battito Cardiaco basso: ", B);
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"Attezione! Stato di Bradicardìa rilevato\"}",Msg);
  !send_message("localhost", 5050, Msg).

//---------------------------------Nutrizione----------------------------------------
+!condividi_bmi(BMI)
  <- .print("[COORDINATORE] Sto inviando il nuovo BMI aggiornato");
  .concat("{\"nodo\":\"db_node\", \"messaggio\": \"", BMI, "\"}", Msg);
  !send_message("localhost", 5050, Msg).

+!aggiorna_stato_nutrizionale(N)
<- .print("[COORDINATORE] Sto inviando lo Stato nutrizionale aggiornato");
  .concat("{\"nodo\":\"db_node\", \"messaggio\": \"", N, "\"}", Msg);
  !send_message("localhost", 5050, Msg).

+!domanda_perdita_di_peso
  <- .print("[COORDINATORE] Hai notato perdita di peso in questo periodo? Rispondimi con TANTO, POCO, NULLA");
  .concat("{\"nodo\":\"pepper_code\", \"agente\":\"nutrizione\", \"comando\":\"messaggio\", \"messaggio\": \"Hai notato perdita di peso in questo periodo? Rispondimi con TANTO, POCO, NULLA\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!domanda_malattia
  <- .print("[COORDINATORE] In questo periodo hai avuto sintomi possibilemente correlati all'alimentazione");
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"In questo periodo hai avuto sintomi possibilmente correlati all'alimentazione\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!domanda_digiuno_prolungato
  <- .print("[COORDINATORE] A quanti gionri fa risale l'ultimo pasto? Rispondi con il numero di giorni di digiuno");
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"messaggio\", \"messaggio\": \"A quanti gionri fa risale l'ultimo pasto? Rispondi con il numero di giorni di digiuno\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!chiedi_di_effettuare_test_nutrizione(M)
  <- .print("[COORDINATORE] Vuoi effettuare un test?");
  .concat("{\"nodo\":\"pepper_code\",\"agente\":\"nutrizione\", \"percept\":\"volonta_di_eseguire_test\", \"comando\":\"messaggio\", \"messaggio\": \"", M, "\"}",Msg);
  !send_message("localhost", 5050, Msg).

//---------------------------------Mobilità---------------------------------------
+!chiedi_di_effettuare_test_mobilita(M)
  <- .print("[COORDINATORE] Vuoi effettuare un test?");
  .concat("{\"nodo\":\"pepper_code\",\"agente\":\"mobilita\", \"percept\":\"volonta_di_eseguire_esercizi\", \"comando\":\"messaggio\", \"messaggio\": \"", M, "\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!effettua_test(M)
  <- .print("[COORDINATORE] Vuoi effettuare un test?");
  .concat("{\"nodo\":\"effettua_test\",\"agente\":\"mobilita\", \"percept\":\"volonta_di_eseguire_esercizi\", \"comando\":\"effettua_test\", \"test\": \"", M, "\"}",Msg);
  !send_message("localhost", 5050, Msg).

//--------------------------------Stato Cognitivo--------------------------------------
+!chiedi_di_effettuare_test_statocognitivo(M)
  <- .print("[COORDINATORE] Vuoi effettuare un test?");
  .concat("{\"nodo\":\"pepper_code\",\"agente\":\"statoCognitivo\", \"percept\":\"volonta_di_eseguire_test\", \"comando\":\"messaggio\", \"messaggio\": \"", M, "\"}",Msg);
  !send_message("localhost", 5050, Msg).

+!avvia_test(M)
  <- .print("[COORDINATORE] Vuoi effettuare un test?");
  .concat("{\"nodo\":\"effettua_test\",\"agente\":\"statoCognitivo\", \"percept\":\"volonta_di_eseguire_test\", \"comando\":\"effettua_test\", \"test\": \"", M, "\"}",Msg);
  !send_message("localhost", 5050, Msg).

