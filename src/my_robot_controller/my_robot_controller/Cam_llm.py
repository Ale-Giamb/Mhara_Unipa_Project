import base64
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
from langchain_openai import ChatOpenAI
import ollama
from .token_logger import get_token_logger

class CamLLM:
    def __init__(self, provider="openai", model=None):
        self.image_path = os.path.expanduser("/home/roboticslab/Scrivania/Robot_Architecture/MHARA_Unipa/src/camera/")
        self.provider = provider
        self.token_logger = get_token_logger()
        
        # Configurazione del modello basata sul provider
        if provider == "groq":
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        elif provider == "openai":
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
       
        elif provider == "ollama":
            self.ollama_model = "moondream:1.8b" #"llava:7b"
            self.llm = None  # Non useremo LangChain per Ollama
        else:
            raise ValueError(f"Provider non supportato: {provider}")
            
        self.positive_example1 = "Dall'immagine fornita posso notare che la persona è molto soddisfatta dalla risposta del robot," \
                                "dalla sua postura posso notare che la persona è molto interessata alla risposta del robot. " \
                                "L'ambiente circostante è un ufficio dove sono presenti diverse persone "
        
        self.positive_example2 = "Dall'immagine fornita posso notare che la persona è molto triste quindi non ha gradito la risposta del robot," \
                                "dalla sua postura posso notare che la persona è molto distaccata quindi poco interessata al robot. " \
                                "L'ambiente circostante è una cucina, con un frigorifero ed un tavolo"
        
        # Prompt per provider LangChain
        self.cam_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            Analizza l'immagine fornita e concentrati sul feedback umano alla risposta del robot.
            Fornisci una descrizione che includa:
            1. L'emozione predominante mostrata dalla persona più vicina alla camera (felicità, confusione, frustrazione, soddisfazione, ecc.)
            2. Il linguaggio del corpo e le espressioni facciali osservate
            3. Una breve descrizione dell'ambiente circostante
            Rispondi in italiano in modo chiaro e conciso.
            Esempi di risposta: {self.positive_example1} ,{self.positive_example2}
            """),
            ("user", [
                {
                    "type": "text",
                    "text": "Analizza questa immagine per comprendere il feedback umano alla risposta del robot. Contesto aggiuntivo: {context}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,{image_data}"
                    }
                }
            ])
        ])

    def _load_image_as_base64(self) -> str:
        self.image_path_=os.path.join(self.image_path,"image.jpeg")
        with open(self.image_path_, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_with_ollama(self, context=""):
        """Metodo specifico per usare Ollama direttamente"""
        system_prompt = f"""
        Analizza l'immagine fornita e concentrati sul feedback umano alla risposta del robot.
        Fornisci una descrizione che includa:
        1. L'emozione predominante mostrata dalla persona più vicina alla camera (felicità, confusione, frustrazione, soddisfazione, ecc.)
        2. Il linguaggio del corpo e le espressioni facciali osservate
        3. Una breve descrizione dell'ambiente circostante
        Rispondi in italiano in modo chiaro e conciso.
        Esempi di risposta: {self.positive_example1} ,{self.positive_example2}
        
        Contesto aggiuntivo: {context}
        """
        
        response = ollama.chat(
            model=self.ollama_model,
            messages=[{
                'role': 'user',
                'content': system_prompt + "\n\nAnalizza questa immagine per comprendere il feedback umano alla risposta del robot.",
                'images': [self.image_path]  # Ollama accetta direttamente il path dell'immagine
            }]
        )
        
        # Ollama è gratuito (locale), non loghiamo costi
        return response['message']['content']

    def create_cam_chain(self):
        """Metodo per provider LangChain"""
        if self.provider == "ollama":
            raise ValueError("Per Ollama usa il metodo analyze_with_ollama() direttamente")
            
        def prepare_inputs(context):
            return {
                "image_data": self._load_image_as_base64(),
                "context": context
            }
        
        chain = RunnableLambda(prepare_inputs) | self.cam_prompt | self.llm
        
        # Wrap chain to log token usage
        def chain_with_logging(context):
            result = chain.invoke(context)
            
            # Log token usage
            if hasattr(result, 'response_metadata'):
                metadata = result.response_metadata
                if 'usage' in metadata:
                    usage = metadata['usage']
                    self.token_logger.log_token_usage(
                        model="gpt-4o-mini" if self.provider == "openai" else "llama-3.3-70b-versatile",
                        input_tokens=usage.get('prompt_tokens', 0),
                        output_tokens=usage.get('completion_tokens', 0),
                        source="Cam_llm",
                        metadata={"context": context[:50] if context else ""}
                    )
            
            return result
        
        return chain_with_logging

    def analyze_image(self, context=""):
        """Metodo unificato per analizzare l'immagine indipendentemente dal provider"""
        if self.provider == "ollama":
            print("Analizzando fotocamera ...",flush=True)
            return self.analyze_with_ollama(context)
        else:
            chain = self.create_cam_chain()
            return chain(context)


