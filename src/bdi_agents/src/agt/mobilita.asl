
data_ultimo_test_mobilita("2025-03-19"). 
trattamento_passato("Interento al ginocchio").
terapia_attuale("Camminata").
//volonta_di_eseguire_esercizi("No").   

//------------------------------------
+start(_)[source(percept)]<-
    !start.

+!start : data_ultimo_test_mobilita(D) <- 
    .print("[MOBILITÀ] Controllo da quanti giorni manca il test...");
    !verifica_giorni(D).

+!verifica_giorni(D) <- 
    calcolo_giorni_dall_ultimo_test(D).

//------------------------------------
+giorni_differenza(N)[source(percept)] : N > 10 <- 
    .print("[MOBILITÀ] Troppi giorni passati: ", N);
    //-volonta_di_eseguire_esercizi(_);
    !verifica_capacita_per_test.

+!verifica_capacita_per_test : not trattamento_passato(_)<-
    .print("[MOBILITÀ] è da tanto che non effettuaimo uno screening di mobilità, lo vuoi fare adesso?");
    .send(coordinatore,achieve,chiedi_di_effettuare_test_mobilita("è da tanto che non effettuaimo uno screening di mobilità, lo vuoi fare adesso?")).

+!verifica_capacita_per_test : trattamento_passato(_) & not volonta_di_eseguire_esercizi(_)<-
    .print("[MOBILITÀ] Dovresti effettuare un test per la mobilità, te la senti per via dell'intervento?");
    .send(coordinatore,achieve,chiedi_di_effettuare_test_mobilita("Ho notato che hai fatto un intervento che limita la tua mobilità, vuoi ugualmente provare a fare qualche esercizio?")).

+volonta_di_eseguire_esercizi("si")[source(percept)]<-
    .print("[MOBILITÀ] Ok, proseguiamo per effettuare il test");
    -volonta_di_eseguire_esercizi(_)[source(percept)];
    .send(coordinatore,achieve,effettua_test("mobilita")).

+volonta_di_eseguire_esercizi("no")[source(percept)]<-
    .print("[MOBILITÀ] Se non te la senti faremo il test più avanti");
    -volonta_di_eseguire_esercizi(_)[source(percept)];
    .send(coordinatore,achieve,comunica("Se non te la senti faremo il test più avanti")).

//------------------------------------
+giorni_differenza(N)[source(percept)] : N < 11 
    <- .print("[MOBILITÀ] Pochi giorni passati ", N).
    
