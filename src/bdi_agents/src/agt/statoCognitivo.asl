//!start.
data_ultimo_test_cognitivo("2025-05-10").
//volonta_di_eseguire_test("si").

//----------------------------------------

+start(_)[source(percept)]<-
    !start.

+!start : data_ultimo_test_cognitivo(D) <- 
    .print("[STATO COGNITIVO] Controllo da quanti giorni manca il test...");
    !verifica_giorni(D).

+!verifica_giorni(D) <- 
    calcolo_giorni_dall_ultimo_test(D).

//----------------------------------------
+giorni_differenza(N)[source(percept)] : N < 11 <- 
    .print("[STATO COGNITIVO] Troppi giorni passati: ", N);
    //-volonta_di_eseguire_test(_);
    !verifica_capacita_per_test.

+giorni_differenza(N)[source(percept)] : N > 10 <- 
    .print("[STATO COGNITIVO] Troppi giorni passati: ", N);
    //-volonta_di_eseguire_test(_);
    !verifica_capacita_per_test.

+!verifica_capacita_per_test<-
    .print("[STATO COGNITIVO] è da tanto che non effettuaimo uno screening uno screening cognitivo, lo vuoi fare adesso?");
    .send(coordinatore,achieve,chiedi_di_effettuare_test_statocognitivo("è da tanto che non effettuiamo uno screening cognitivo, lo vuoi fare adesso?")).

+volonta_di_eseguire_test("si")[source(percept)]
    <- .print("[STATO COGNITIVO] Avvio test MUST");
        -volonta_di_eseguire_test(_)[source(percept)];
        .send(coordinatore, achieve, avvia_test("minicog")).

+volonta_di_eseguire_test("no")[source(percept)]
    <- .print("[STATO COGNITIVO] Se non te la senti faremo il test più avanti");
    -volonta_di_eseguire_test(_)[source(percept)];
    .send(coordinatore,achieve,comunica("Se non te la senti faremo il test più avanti")).