!start.  

+sensor_data(temp, X) <- 
    -temperatura(_);  
    +temperatura(X).

+sensor_data(heartbeat, X) <- 
    -battito(_);
    +battito(X).

+sensor_data(mood, X) <- 
    -umore(_);
    +umore(X).

+!start <- 
    .print("Buongiorno! Sono il tuo assistente.");
    !send_message("localhost", 5050, "{\"nodo\":\"database\", \"comando\":\"get_beliefs\"}").

+!send_message(Server, Port, Message) <- 
    .print("Invio messaggio a ", Server, ":", Port, " -> ", Message);
    connet_to_socket(Server, Port, Message).

+socket_message(Msg) <- 
    .print("Messaggio ricevuto: ", Msg).

+nome(X)
  <- 
  .concat("{\"nodo\":\"pepper_code\", \"comando\":\"saluta\", \"nome\": \"", X,"\"}",Msg);
  .print(Msg);

  !send_message("localhost", 5050, Msg).


+temperatura(T) : T > 28
  <- .print("Fa troppo caldo! Accendo il condizionatore.");
     !send_message("localhost", 5050, "accendi_condizionatore").

+temperatura(T) : T < 18
  <- .print("Fa troppo freddo! Accendo il riscaldamento.");
     !send_message("localhost", 5050, "accendi_riscaldamento").
