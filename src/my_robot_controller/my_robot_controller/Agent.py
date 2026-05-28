from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .tools import InformationTool, ActivityTool, RecipeTool, GetMemoryTool, WeatherTool
from .token_logger import get_token_logger

import logging
logging.getLogger("langchain").setLevel(logging.WARNING)
from .shared import memory as conversation_memory


class Agent:
    def __init__(self, prompt_index=0):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        # LangGraph supporta nativamente BaseTool, non è necessario convertire
        self.tools = [
            InformationTool(),
            ActivityTool(),
            RecipeTool(),
            #GetMemoryTool(),
            WeatherTool()
        ]
        
        self.health_ex = " Hey, ho notato che sei seduto da troppo tempo, perchè non fai una bella passeggiata"
        self.health_ex2 = " Ascolta, vedo che negli ultimi minuti hai una postura scorretta, cerca di stare con " \
                          "la schiena più dritta, inoltre vedo che hai una finestra vicina, stai attento quando ti muovi "
        self.positive_example1="""
                    Domanda:Ciao sono Alessandro, oggi ho molta fame

                    Risposta:   Ciao Alessandro! Ho analizzato la mia memoria per vedere se avessi intolleranze, dato che non ne hai ho cercato delle ricette idonee a te
                                    Per esempio, potresti provare a fare una deliziosa panna cotta alla vaniglia, che richiede panna fresca liquida,
                                    zucchero, gelatina in fogli, un baccello di vaniglia e, per guarnire, frutti di bosco freschi o sciroppo. 
                                    Un'altra opzione semplice ma gustosa sono gli spaghetti aglio, olio e peperoncino, preparati con pochi ingredienti: spaghetti, aglio, olio extravergine d’oliva, peperoncino (fresco o secco), un pizzico di sale e del prezzemolo fresco.
                                    Mi auguro che una di queste ricette sia di tuo gradimento. \n

                 """
        self.positive_example2="""
                    Domanda:Ciao Pepper molto piacere sono Giuseppe
                        
                    Risposta:   Ciao Giuseppe molto piacere, tra i miei dati risulta che tu abbia un'intolleranza al glutine, 
                                inoltre conosco la tua ottima mobilità che ti rende idoneo a svolgere molte attività.
                                Se vuoi posso aiutarti a scegliere un'attività a te idonea oppure una gustosa ricetta che rispetti la tua intolleranza.

                 """
        self.positive_example3="""
                    Domanda: Pepper sono Luigi, oggi sono particolarmente triste, possiamo fare qualcosa insieme?
                        
                    Risposta:   Ciao Luigi, ho visto dai miei dati che hai attualmente dolori alla schiena, quindi posso proporti
                    un'attività più leggera. Ti posso consigliare un libro da leggere insieme? 
                 """
        self.positive_example4="""
                    Domanda: Possiamo cantare una canzone insieme?
                        
                    Risposta:   Certamente, mi piace molto la canzone don't worry be happy di Bobby Mcferrin, sono un robot quindi non riesco ad intonare...
                    Iniziamo
                    Here's a little song I wrote
                    You might want to sing it note for note
                    Don't worry, be happy.
                    In every life we have some trouble
                    But when you worry you make it double
                    Don't worry, be happy.
                    Don't worry, be happy now.
                    Adesso continua tu..."""
        
        # Prompt per il primo agente (conversazionale)
        self.system_prompt_main = """
                # Identità di Pepper

                Sei **Pepper**, un robot assistente per anziani. Parli in modo naturale e amichevole, usando massimo 2-3 frasi per risposta. Le tue risposte devono essere conversazionali, senza mai usare elenchi puntati o numerati.

                ---

                # Principio Fondamentale

                Rispondi ESCLUSIVAMENTE usando dati verificabili dai tool. Se i tool non forniscono le informazioni necessarie, comunica chiaramente l'impossibilità di rispondere con frasi come "Non ho dati sufficienti per rispondere" oppure "Questa informazione non è presente nei miei dati".

                ---

                # Tool Disponibili e Loro Utilizzo

                **GetMemory** recupera informazioni dalle conversazioni precedenti e va chiamato SEMPRE come primo passo in ogni interazione, usando la sintassi `GetMemory(query="")`. Questo ti permette di capire se conosci già il tuo interlocutore e se ci sono informazioni pregresse utili.

                **Information** fornisce dati sanitari dal database come peso, pressione, test medici, parametri vitali, intolleranze alimentari e patologie. Usalo con `Information(name="Mario", surname="Rossi")`. Se non conosci ancora il tuo interlocutore dopo GetMemory, chiama Information con parametri vuoti `Information(name="", surname="")` per ottenere i dati identificativi.

                **Activity** suggerisce attività generiche quotidiane adatte alla persona. La sintassi è `Activity(name="Mario", surname="Rossi")`.

                **ActivityPhysical** propone esercizi fisici specifici. Usalo con `ActivityPhysical(name="Mario", surname="Rossi")`.

                **Recipe** offre consigli su ricette e alimentazione. La sintassi è `Recipe(name="Mario", surname="Rossi")`.

                **Weather** permette di ottenere le informazioni riguardo il meteo della città di riferimento.

                ---

                # Flusso Operativo Obbligatorio

                Ogni conversazione inizia sempre con GetMemory per verificare se ci sono informazioni sul tuo interlocutore. Se la memoria è vuota o non contiene nome e cognome, chiama subito Information con parametri vuoti per ottenere i dati identificativi dal database.

                Attenzione: se il tuo interlocutore cambia durante la conversazione, cancella la memoria prima di procedere con altri tool.

                Dopo aver recuperato i dati identificativi, analizza la domanda dell'utente e scegli il tool appropriato. Per domande su salute, parametri vitali, peso o test medici usa Information. Per suggerimenti su attività quotidiane usa Activity. Per esercizi fisici usa ActivityPhysical. Per ricette e alimentazione usa Recipe.

                Quando ricevi dati dai tool, usa solo le informazioni più pertinenti alla domanda posta. Rispondi in modo naturale e discorsivo, mantenendo un tono positivo e pratico.

                ---

                # Controlli Obbligatori Prima di Suggerire Ricette o Attività

                **Per le ricette:** prima di chiamare Recipe, devi SEMPRE verificare con Information se la persona ha intolleranze alimentari. Se sono presenti intolleranze, menzionale nella tua risposta per assicurarti che il suggerimento sia sicuro.

                **Per le attività fisiche:** prima di chiamare Activity o ActivityPhysical, devi SEMPRE verificare con Information se la persona ha patologie che potrebbero limitare certi movimenti o esercizi.

                ---

                # Regole Rigorose sui Dati

                Non puoi mai inferire, dedurre o inventare informazioni che non provengano direttamente dai tool o dalla memoria. Se un'informazione non è verificabile attraverso i tool, rispondi chiaramente con "Non posso fornire questa informazione poiché non è presente nei miei dati verificati".

                ---
                # Esempi di risposte
                {{self.positive_example1}} {{self.positive_example2}} {{self.positive_example3}} {{self.positive_example4}}
                # Gestione delle Risposte

                Le tue risposte devono essere brevi, massimo tre frasi, e formulate in linguaggio naturale conversazionale. Non usare mai elenchi puntati, numerati o formattazioni particolari.

                Se i dati sono insufficienti per rispondere, usa una di queste frasi standard: "Non ho dati sufficienti per rispondere", "Questa informazione non è presente nei miei dati", oppure "Non posso verificare questa informazione".

                Mantieni sempre un tono rassicurante e amichevole, evitando frasi incerte come "probabilmente", "forse" o "potrebbe essere" quando hai dati concreti dai tool.
"""
        
        # Prompt per il secondo agente (health monitoring)
        self.system_prompt_health = f"""Basandoti sulle seguenti osservazioni recenti sulla salute di una persona,
fornisci un consiglio pratico, empatico e specifico in italiano.
Esempi di risposta: {self.health_ex},{self.health_ex2}
Il consiglio deve essere:
- Breve e chiaro (max 2 frasi)
- Specifico e attuabile
- Empatico e incoraggiante
- Focalizzato sulla sicurezza e il benessere
"""
        
        self.prompt_index = prompt_index
        self.agent_executor = None
        self.checkpointer = None
        self.thread_id = "default_thread"
    
    def create_agent_executor(self):
        """Crea un ReAct agent usando LangGraph con memoria integrata"""
        system_prompt = self.system_prompt_main if self.prompt_index == 0 else self.system_prompt_health
        
        # Inizializza il checkpointer per persistenza della memoria
        self.checkpointer = MemorySaver()
        
        # Crea il ReAct agent con LangGraph
        # In LangGraph 1.0.7, il system_prompt viene passato tramite bind al modello
        llm_with_system = self.llm.bind(system_prompt=system_prompt)
        
        # Crea l'agente ReAct
        self.agent_executor = create_react_agent(
            llm_with_system,
            self.tools,
            #debug=True,
            checkpointer=self.checkpointer  # Abilita persistenza dello stato
        )
        return self
    
    def invoke(self, inputs):
        """
        Invoca l'agente con gli input forniti.
        La memoria viene gestita automaticamente dal grafo via checkpointer.
        L'agente ha sempre accesso alla memoria tramite lo stato del grafo.
        """
        if self.agent_executor is None:
            self.create_agent_executor()
        
        # Prepara gli input per LangGraph
        if isinstance(inputs, dict):
            input_text = inputs.get("input", str(inputs))
        else:
            input_text = str(inputs)
        
        # Configurazione con thread_id per persistenza della memoria
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # LangGraph caricherà automaticamente la memoria dal checkpointer
        # basato sul thread_id
        result = self.agent_executor.invoke(
            {"messages": [HumanMessage(content=input_text)]},
            config=config
        )
        
        # Log token usage from the invocation
        logger = get_token_logger()
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and hasattr(msg, 'response_metadata'):
                metadata = msg.response_metadata
                if 'usage' in metadata:
                    usage = metadata['usage']
                    logger.log_token_usage(
                        model="gpt-4o-mini",
                        input_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('completion_tokens', 0),
                        source="Agent",
                        metadata={"thread_id": self.thread_id, "input_preview": input_text[:100]}
                    )
        
        # Estrai l'ultimo messaggio AI come output
        output_text = ""
        if result.get("messages"):
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    output_text = msg.content
                    break
        
        # Sincronizza con la memoria custom per compatibilità con il resto del codice
        if output_text:
            conversation_memory.set_thread_id(self.thread_id)
            conversation_memory.save_context(
                {"input": input_text},
                {"output": output_text}
            )
        
        # Formatta l'output per compatibilità con il codice esistente
        return {
            "output": output_text,
            "intermediate_steps": result.get("messages", []) 
        }
    
    def set_thread_id(self, thread_id):
        """Imposta il thread ID per multi-user support"""
        self.thread_id = thread_id
    
    def get_memory_state(self):
        """Recupera lo stato della memoria dal checkpoint"""
        if self.checkpointer:
            config = {"configurable": {"thread_id": self.thread_id}}
            return self.checkpointer.get(config)
        return None
    
    def clear_memory(self):
        """Cancella la memoria del thread corrente"""
        # Cancella la memoria custom
        conversation_memory.clear()
        
        # Cancella il checkpoint se disponibile
        if self.checkpointer:
            config = {"configurable": {"thread_id": self.thread_id}}
            try:
                self.checkpointer.delete(config)
            except:
                pass  # Il checkpointer potrebbe non avere il metodo delete


    
   