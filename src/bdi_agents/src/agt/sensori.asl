+temperatura(T) : T > 38.0 | T < 35.0
  <- .print("[SENSORI] Tempratura Corporea anomala rilevata");
  .send(coordinatore,achieve,valuta_temperatura(T)).

+respirazione(R) : R > 24 | R < 10
  <- .print("[SENSORI] Frequenza Respiratoria anomala rilevata");
  .send(coordinatore,achieve,valuta_respirazione(R)).

+pressione(P) : P > 140 | P < 90
  <- .print("[SENSORI] Pressione Sangigna anomala rilevata");
  .send(coordinatore,achieve,valuta_pressione(P)).

+battito(B) : B > 100 | B < 50
  <- .print("[SENSORI] Battito Cardiaco anomalo rilevato");
  .send(coordinatore,achieve,valuta_battito(B)).