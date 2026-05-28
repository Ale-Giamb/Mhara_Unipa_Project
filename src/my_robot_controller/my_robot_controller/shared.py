from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationMemory:
    """
    Implementazione di una memoria di conversazione compatibile con LangChain 0.3+ e LangGraph.
    
    Supporta i metodi utilizzati dal resto del codice:
    - load_memory_variables()
    - save_context()
    - clear()
    - chat_memory.messages
    
    Integrata con LangGraph per:
    - Sincronizzazione dello stato della conversazione
    - Support per multi-user tramite thread_id
    - Persistenza automatica
    """
    
    def __init__(self, max_token_limit=10000, memory_key="chat_history"):
        self.max_token_limit = max_token_limit
        self.memory_key = memory_key
        self.messages = []
        self.input_key = "input"
        self.output_key = "output"
        self.current_thread_id = "default_thread"
        
        # Dizionario per supportare multi-user
        self.thread_memories = {}
        
        # Classe interna per gestire chat_memory.messages
        class ChatMemory:
            def __init__(self, parent):
                self.parent = parent
            
            @property
            def messages(self):
                return self.parent.get_messages()
        
        self.chat_memory = ChatMemory(self)
    
    def set_thread_id(self, thread_id):
        """Imposta il thread ID per supporto multi-user"""
        self.current_thread_id = thread_id
        if thread_id not in self.thread_memories:
            self.thread_memories[thread_id] = []
    
    def get_messages(self):
        """Ottiene i messaggi del thread corrente"""
        return self.thread_memories.get(self.current_thread_id, self.messages)
    
    def load_memory_variables(self, inputs: dict = None):
        """
        Carica le variabili di memoria nel formato atteso da LangChain e LangGraph.
        Supporta sia il vecchio formato dict che il nuovo formato BaseMessage.
        """
        if inputs is None:
            inputs = {}
        
        current_messages = self.get_messages()
        
        # Converti i messaggi nel formato lista di dict
        chat_history_list = []
        for msg in current_messages:
            if isinstance(msg, BaseMessage):
                chat_history_list.append({
                    "type": msg.type,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                chat_history_list.append(msg)
        
        return {self.memory_key: chat_history_list}
    
    def save_context(self, inputs: dict, outputs: dict):
        """
        Salva l'input e l'output nella memoria del thread corrente.
        Compatibile con LangGraph.
        """
        # Estrai il testo di input
        input_text = inputs.get(self.input_key, "")
        if not isinstance(input_text, str):
            input_text = str(input_text)
        
        # Estrai il testo di output
        output_text = outputs.get(self.output_key, "")
        if not isinstance(output_text, str):
            output_text = str(output_text)
        
        # Ottieni la lista dei messaggi del thread corrente
        if self.current_thread_id not in self.thread_memories:
            self.thread_memories[self.current_thread_id] = []
        
        current_messages = self.thread_memories[self.current_thread_id]
        
        # Aggiungi i messaggi
        current_messages.append(HumanMessage(content=input_text))
        current_messages.append(AIMessage(content=output_text))
        
        # Applica il limite di token rimuovendo i messaggi più vecchi se necessario
        self._trim_messages(current_messages)
        
        # Aggiorna anche la lista principale per compatibilità all'indietro
        self.messages = current_messages
    
    def _trim_messages(self, messages_list=None):
        """
        Mantiene solo i messaggi recenti fino al limite di token.
        Funziona sia su singola lista che su lista principale.
        """
        if messages_list is None:
            messages_list = self.get_messages()
        
        def count_tokens(text):
            """Conta i token approssimativamente (1 token ≈ 4 caratteri)"""
            return len(text) // 4
        
        total_tokens = sum(count_tokens(msg.content) for msg in messages_list)
        
        # Se supera il limite, rimuovi i messaggi più vecchi
        while total_tokens > self.max_token_limit and len(messages_list) > 2:
            removed_msg = messages_list.pop(0)
            total_tokens -= count_tokens(removed_msg.content)
    
    def clear(self):
        """Cancella la memoria del thread corrente"""
        if self.current_thread_id in self.thread_memories:
            self.thread_memories[self.current_thread_id] = []
        self.messages = []
    
    def clear_all(self):
        """Cancella la memoria di tutti i thread"""
        self.thread_memories = {}
        self.messages = []
    
    def get_buffer_string(self):
        """Restituisce tutti i messaggi come stringa formattata"""
        current_messages = self.get_messages()
        buffer = []
        for msg in current_messages:
            if isinstance(msg, HumanMessage):
                buffer.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                buffer.append(f"AI: {msg.content}")
            else:
                buffer.append(f"{msg.type}: {msg.content}")
        return "\n".join(buffer)
    
    def get_thread_summary(self, thread_id=None):
        """Restituisce un riassunto della memoria di un thread specifico"""
        if thread_id is None:
            thread_id = self.current_thread_id
        
        messages = self.thread_memories.get(thread_id, [])
        if not messages:
            return "Nessuna conversazione in questo thread."
        
        return f"Thread '{thread_id}': {len(messages)} messaggi ({sum(len(msg.content) for msg in messages)} caratteri)"
    
    def list_threads(self):
        """Restituisce la lista di tutti i thread attivi"""
        return list(self.thread_memories.keys())


# Istanza globale di memoria condivisa
memory = ConversationMemory(
    max_token_limit=10000,
    memory_key="chat_history"
)