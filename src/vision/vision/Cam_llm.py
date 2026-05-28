from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class CamLLM:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        self.cam_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            Analizza l'immagine fornita e concentrati sul feedback umano alla risposta del robot.
            
            Fornisci una descrizione che includa:
            1. L'emozione predominante mostrata dalla persona (felicità, confusione, frustrazione, soddisfazione, ecc.)
            2. Il linguaggio del corpo e le espressioni facciali osservate
            3. Una breve descrizione dell'ambiente circostante
            4. Un'interpretazione del livello di gradimento/soddisfazione del feedback umano
            5. Suggerimenti su come il robot potrebbe migliorare la sua risposta basandosi sul feedback osservato
            
            Rispondi in italiano in modo chiaro e conciso.
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

    def create_cam_chain(self):
        return (
            {"response": RunnablePassthrough()} 
            | self.cam_prompt 
            | self.llm
        )