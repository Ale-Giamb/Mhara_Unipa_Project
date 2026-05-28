
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from .token_logger import get_token_logger

class LLMSummary:
    def __init__(self):
        #self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        self.token_logger = get_token_logger()
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """
                Analizza la risposta dell'agente e crea un riassunto rispetto queste informazioni:

                1. CONTESTO: Una frase che descrive il contesto della richiesta dell'utente.
                2. AZIONI: Le principali azioni intraprese dall'agente per rispondere.
                3. RISPOSTA: Il nucleo della risposta fornita dall'agente.
                4. DATI UTILIZZATI: I tool e le informazioni utilizzate per formulare la risposta.
               
                Il riassunto deve essere conciso, discorsivo ed informativo, evidenziando i punti chiave 
                dell'interazione senza ripetere informazioni non necessarie.
            """),
            ("user", "{response}")
        ])
    # 5. ANALISI IMMAGINE: Breve descrizione del feedback visivo rispetto la risposta dell'agente verso l'umano
    def create_summary_chain(self):
        chain = (
            {"response": RunnablePassthrough()} 
            | self.summary_prompt 
            | self.llm
        )
        
        # Create a wrapper that logs token usage
        class ChainWithLogging:
            def __init__(self, chain, logger):
                self.chain = chain
                self.logger = logger
            
            def invoke(self, input_data):
                result = self.chain.invoke(input_data)
                
                # Log token usage
                if hasattr(result, 'response_metadata'):
                    metadata = result.response_metadata
                    if 'usage' in metadata:
                        usage = metadata['usage']
                        self.logger.log_token_usage(
                            model="gpt-4o-mini",
                            input_tokens=usage.get('prompt_tokens', 0),
                            output_tokens=usage.get('completion_tokens', 0),
                            source="LLMSummary",
                            metadata={"response_length": len(str(input_data))}
                        )
                
                return result
        
        return ChainWithLogging(chain, self.token_logger)
        