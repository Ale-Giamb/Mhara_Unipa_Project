from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .neo4j_driver import Neo4jGraphConnection
import os
from .shared import memory
from .update_kg import Update_Kg
from sensor_msgs.msg import Image
import requests
# Configurazione ambiente
os.environ["NEO4J_URI"] = "bolt://localhost:7690"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "12345678"




# Connessione al database Neo4j

graph = Neo4jGraphConnection(
    uri="bolt://localhost:7690",
    username="neo4j", 
    password="12345678"
)
Up_Kg=Update_Kg()



def get_information() -> str:
    try:
        data = Up_Kg.search_inf_callback(f"Dammi tutte le informazioni personali dell'anziano") # di nome: {name} e cognome: {surname}
        print(f"InformatioTool: {data} ", flush=True)
        if data:
            return f"""
                Nome: {data[0]['nome']}
                Cognome: {data[0]['cognome']}
                Peso: {data[0]['peso']} kg
                Altezza: {data[0]['altezza']} m
                Test Mobilità: {data[0]['statoMobilita'][0]['stato'].strip()}, Data: {data[0]['testMobilita'][0]['data']}, punteggio: {data[0]['testMobilita'][0]['punteggio']}
                Test Nutrizionale: {data[0]['testNutrizionale'][0]['tipo']}, Data: {data[0]['testNutrizionale'][0]['data']}, punteggio: {data[0]['testNutrizionale'][0]['punteggio']}
                Stato Cognitivo: {data[0]['statoCognitivo'][0]['stato']}
                Test Cognitivo: Punteggio {data[0]['testCognitivo'][0]['punteggio']} (Data: {data[0]['testCognitivo'][0]['data']})
                Trattamento Passato: {data[0]['trattamentoPassato'][0]['descrizione']} (ID: {data[0]['trattamentoPassato'][0]['id']})
                Terapia Fisica: {data[0]['terapiaFisica'][0]['tipo']}
                Parametri Ematici: Glicemia {data[0]['parametriEmatici'][0]['glicemia']}, Emoglobina {data[0]['parametriEmatici'][0]['emoglobina']}
                Stato Nutrizionale: {data[0]['statoNutrizionale'][0]['stato']}
                Patologie: {data[0]['patologie'][0]['id']} - {data[0]['patologie'][0]['descrizione']}
                Intolleranze: {data[0]['intolleranze'][0]['id']} - {data[0]['intolleranze'][0]['descrizione']}
                Parametri Vitali: Pressione {data[0]['parametriVitali'][0]['pressioneSistolica']}/{data[0]['parametriVitali'][0]['pressioneDiastolica']}, Battito {data[0]['parametriVitali'][0]['battitoCardiaco']}, Temperatura {data[0]['parametriVitali'][0]['temperaturaCorporea']}°C
                """

        elif not data:
            return "Non ho trovato informazioni su questa persona."
        
        
    except Exception as e:
        print(f"Errore nel recupero informazioni: {e}", flush=True)
        return "Nessuna informazione trovata"


  
def get_activities() -> str:
    try:
        # Query activities
        activities = Up_Kg.search_inf_callback(f"Dammi tutte le attività adatte all'anziano ")
        print(f"ActivityTool: {activities} ", flush=True)
        if activities:
            activity_list = [
                f"  Attività: {act['attivitaId']}\n"
                f"  Descrizione: {act['descrizioneAttivita']}\n"
                f"  Livello di mobilità richiesto: {act['livelloMobilita']}"
                for act in activities
            ]
            return "Attività consigliate:\n" + "\n".join(activity_list)+ "\n"
        else:
            return "Non ho trovato attività adatte alle tue condizioni."
    except Exception as e:
        return f"Errore durante la ricerca delle attività: {str(e)}"
   
def get_activitiesPhysical() -> str:
    try:
        # Query activities
        activities = Up_Kg.search_inf_callback(f"Dammi tutte le attività fisiche adatte all'anziano ")
        print(f"ActivityPhysicalTool: {activities} ", flush=True)
        if activities:
            activity_list = [
                f"  AttivitàFisica: {act['attivitaId']}\n"
                f"  Descrizione: {act['descrizioneAttivita']}\n"
                f"  Livello di mobilità richiesto: {act['livelloMobilita']}"
                for act in activities
            ]
            return "Attività Fisiche consigliate:\n" + "\n".join(activity_list)+ "\n"
        else:
            return "Non ho trovato attività fisiche adatte alle tue condizioni."
    except Exception as e:
        return f"Errore durante la ricerca delle attività: {str(e)}"


def get_recipes() -> str:
    try:
        recipes = Up_Kg.search_inf_callback(f"Dammi tutte le ricette adatte all'anziano ")
        print(f"RecipeTool: {recipes} ", flush=True)
        if recipes:
            recipe_list = [
                f"Ricetta: {r['ricettaId']}\n"
                f"  Ingredienti: {r['ingredienti']}\n"
                f"  Intolleranze: {r['intolleranzeRicetta']}\n"
                f"  Adatta per obesità: {'Sì' if r['adattaPerObesita'] == True else 'No'}"
                for r in recipes
                ]
            return "Ecco alcune ricette adatte a te:\n\n" + "\n\n".join(recipe_list) + "\n"
        else:
            return "Non ho trovato ricette adatte alle tue intolleranze o preferenze."
    except Exception as e:
            return f"Errore durante la ricerca delle ricette: {str(e)}"


def get_memory(query:str)-> dict:
    print(query,flush=True)
    # Recupero della memoria attuale
    chat_history = memory.chat_memory.messages
    output_dict = {"memory": []}
    
    if len(chat_history) > 0:
        for msg in chat_history[-5:]:
            output_dict["memory"].append(f"{msg.type}: {msg.content}")
    else:
        output_dict["memory"].append("")

    return output_dict

# Definizione tool per LangChain

# tool per estrarre informazioni sulla persona
class InformationInput(BaseModel):
   name: str = Field(description="nome della persona menzionata nella domanda")
   surname: str = Field(description="cognome della persona menzionata nella domanda")
   

class InformationTool(BaseTool):
    name: str = "Information"
    description: str = "Strumento per recuperare informazioni personali"
    args_schema: Type[BaseModel] = InformationInput

    def _run(
        self,
        name: str,
        surname: str,
      
      
    ) -> str:
        return get_information()

    async def _arun(
        self,
        name: str,
        surname: str,
    ) -> str:
        return get_information()

# tool per estrarre informazioni sulle attività adatte alla persona
class ActivityInput(BaseModel):
    name: str = Field(description="nome della persona menzionata nella domanda")
    surname: str = Field(description="cognome della persona menzionata nella domanda")
    
class ActivityTool(BaseTool):
    name: str = "Activity"
    description: str = "Strumento per trovare attività adatte alle condizioni della persona"
    args_schema: Type[BaseModel] = ActivityInput

    def _run(
        self,
        name: str,
        surname: str,
       
    ) -> str:
        return get_activities()

    async def _arun(
        self,
        name: str,
        surname: str,
        
    ) -> str:
        return get_activities()
    
    
class ActivityPhysicalInput(BaseModel):
    name: str = Field(description="nome della persona menzionata nella domanda")
    surname: str = Field(description="cognome della persona menzionata nella domanda")

class ActivityPhysicalTool(BaseTool):
    name: str = "ActivityPhysical"
    description: str = "Strumento per trovare attività fisiche adatte alle condizioni della persona"
    args_schema: Type[BaseModel] = ActivityPhysicalInput

    def _run(
        self,
        name: str,
        surname: str,
       
    ) -> str:
        return get_activitiesPhysical()

    async def _arun(
        self,
        name: str,
        surname: str,
        
    ) -> str:
        return get_activitiesPhysical()
    
# tool per estrarre informazioni riguardanti le ricette adatte alla persona
class RecipeInput(BaseModel):
    name: str = Field(description="nome della persona menzionata nella domanda")
    surname: str = Field(description="cognome della persona menzionata nella domanda")

class RecipeTool(BaseTool):
    name: str = "Recipe"
    description: str = "Strumento per trovare ricette "
    args_schema: Type[BaseModel] = RecipeInput

    def _run(
        self,
        name: str,
        surname: str,
        
    ) -> str:
        return get_recipes()

    async def _arun(
        self,
         name: str,
        surname: str,
        
    ) -> str:
        return get_recipes()
    

 
# tool per ottenere informazioni dalla memoria   
class GetMemoryTool(BaseTool):
    name: str = "GetMemory"
    description: str = "strumento per  ottenere la memoria rispetto l'interlocutore attuale"
    query: str = ""
    def _run(
        self,
        query:str
    ) -> dict:
        return get_memory(query)

    async def _arun(
        self,
        query:str
    ) -> dict:
        return get_memory(query)


class WeatherTool(BaseTool):
    name: str = "Weather"
    description: str = "Prende il nome di una città e restituisce i dati meteo attuali come stringa."

    def _run(self) -> str:
        """
        Restituisce il meteo attuale di una città usando OpenWeatherMap API gratuita.
        """
        city="Palermo"
        API_KEY = "26fba3c459f9e8cac398c2be4e9c98c2"  
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=it"
        
        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code != 200:
                return f"Errore: {data.get('message', 'Impossibile ottenere il meteo')}"

            descrizione = data['weather'][0]['description']
            temperatura = data['main']['temp']
            umidita = data['main']['humidity']
            vento = data['wind']['speed']

            result = (f"Meteo a {city}:\n"
                      f"- Condizione: {descrizione}\n"
                      f"- Temperatura: {temperatura}°C\n"
                      f"- Umidità: {umidita}%\n"
                      f"- Vento: {vento} m/s")
            return result
        
        except Exception as e:
            return f"Errore durante il recupero del meteo: {e}"

    async def _arun(self) -> str:
        """Versione asincrona del tool meteo"""
        return self._run()
