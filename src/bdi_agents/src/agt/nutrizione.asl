//!start.

altezza(1.78).
peso(65).
data_ultimo_test_mobilita("2025-05-10").
//volonta_di_eseguire_test("Si").

//----------------------------------------

+start(_)[source(percept)]<-
    !start.

+!start : data_ultimo_test_mobilita(D) <-
    .print("[NUTRIZIONE] Controllo da quanti giorni manca il test...");
    !verifica_giorni(D).

+!verifica_giorni(D) <- 
    calcolo_giorni_dall_ultimo_test(D).

//----------------------------------------
+!start : altezza(H) & peso(P) <- 
    .print("[NUTRIZIONE] Calcolo dello stato nutrizionale...");
    !calcola_stato_nutrizionale(H, P).

+!calcola_stato_nutrizionale(H, P) <- 
    // Calcolo del BMI (Indice di Massa Corporea)
    BMI = P / (H * H);
    .print("[NUTRIZIONE] Il BMI calcolato è: ", BMI);
    .concat("Aggiorna o aggiungi se non è presente, il nodo statoNutrizionale con il parametro BMI: ", BMI, "", Msg);
    .send(coordinatore, achieve, condividi_bmi(Msg));
    !valuta_stato_di_nutrizionale(BMI).

+!valuta_stato_di_nutrizionale(BMI) : BMI < 18.5 
    <- .print("[NUTRIZIONE] StatoNutrizionale: Sottopeso");
    +valutazione_BMI(1);
    .send(coordinatore, achieve, aggiorna_stato_nutrizionale("Aggiorna o aggiungi se non è presente, il nodo statoNutrizionale con il parametro statoNutrizione: Sottopeso")).

+!valuta_stato_di_nutrizionale(BMI) : BMI > 18.4 | BMI < 25
    <- .print("[NUTRIZIONE] StatoNutrizionale: Normopeso");
    +valutazione_BMI(0);
    .send(coordinatore, achieve, aggiorna_stato_nutrizionale("Aggiorna o aggiungi se non è presente, il nodo statoNutrizionale con il parametro statoNutrizione: Normopeso")).

+!valuta_stato_di_nutrizionale(BMI) : BMI > 24.9 | BMI < 30 
    <- .print("[NUTRIZIONE] StatoNutrizionale: Sovrappeso");
    +valutazione_BMI(1);
    .send(coordinatore, achieve, aggiorna_stato_nutrizionale("Aggiorna o aggiungi se non è presente, il nodo statoNutrizionale con il parametro statoNutrizione: Sovrappeso")).

+!valuta_stato_di_nutrizionale(BMI) : BMI > 29.9 
    <- .print("[NUTRIZIONE] StatoNutrizionale: Obeso");
    +valutazione_BMI(2);
    .send(coordinatore, achieve, aggiorna_stato_nutrizionale("Aggiorna o aggiungi se non è presente, il nodo statoNutrizionale con il parametro statoNutrizione: Obeso")).

//-------------------------------------------------------
+giorni_differenza(N)[source(percept)] : N < 11 <- 
    .print("[NUTRIZIONE] Troppi pochi giorni passati: ", N).
    -volonta_di_eseguire_esercizi(_).

+giorni_differenza(N)[source(percept)] : N > 10 <- 
    .print("[NUTRIZIONE] Troppi giorni passati: ", N);
    -volonta_di_eseguire_esercizi(_);
    !verifica_capacita_per_test.

+!verifica_capacita_per_test : not trattamento_passato(_)<-
    .print("[NUTRIZIONE] è da tanto che non effettuiamo uno screening di nutrizione, lo vuoi fare adesso?");
    .send(coordinatore,achieve,chiedi_di_effettuare_test_nutrizione("è da tanto che non effettuiamo uno screening di nutrizione, lo vuoi fare adesso?")).

//-------------------------------------------------------
+volonta_di_eseguire_test("no")[source(percept)]
    <- .print("[STATO COGNITIVO] Se non te la senti faremo il test più avanti");
    -volonta_di_eseguire_test(_)[source(percept)];
    .send(coordinatore,achieve,comunica("Se non te la senti faremo il test più avanti")).

+volonta_di_eseguire_test("si")[source(percept)]
    <- .print("[NUTRIZIONE] Avvio test MUST");
    .send(coordinatore, achieve, avvia_test("MUST")).

    /*.send(coordinatore, achieve, domanda_perdita_di_peso);
    .send(coordinatore, achieve, domanda_malattia);
    .send(coordinatore, achieve, domanda_digiuno_prolungato).*/

+!start : perdita_peso(P) & malattia_acuta(M) & digiuno_prolungato(D) & valutazione_BMI(B)<- 
    .print("[NUTRIZIONE] Avvio calcolo del test MUST...");
    -perdita_peso(_);
    -malattia_acuta(_);
    -digiuno_prolungato(_);
    !calcola_rischio_must(P, M, D, B).

+!calcola_rischio_must(P, M, D, B)
    <- BMI = (P + M + D + B)/8;
    valutazione_test(BMI).

+!valutazione_test(BMI): BMI < 4
    <- .send(coordinatore, achieve, comunica_risultato_test("Non superato")).

+!valutazione_test(BMI): BMI > 3 & BMI < 7
    <- .send(coordinatore, achieve, comunica_risultato_test("Superto parzialmente")).

+!valutazione_test(BMI): BMI > 6
    <- .send(coordinatore, achieve, comunica_risultato_test("Superato")).


