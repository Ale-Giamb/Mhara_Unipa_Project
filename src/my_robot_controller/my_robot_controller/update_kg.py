from .neo4j_driver import Neo4jGraphConnection
import os
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
import re
from langchain_openai import ChatOpenAI
#from langchain_google_genai import ChatGoogleGenerativeAI
# Configurazione ambiente
os.environ["NEO4J_URI"] = "bolt://localhost:7690" 
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "12345678"

class Update_Kg():
    def __init__(self):
       
        self.graph = Neo4jGraphConnection()
        self.schema=self.graph.get_schema()

        self.examples = [
        { "question": "Aggiorna il nodo anziano con i seguenti parametri nome: Fabio, cognome: Neri, patologia: , intolleranza:glutine, peso: 70, altezza: 170"
        ,
        "query": '''
               MATCH 
                (int:Intolleranza {{id: 'Glutine'}}),
                (p:Anziano)
                SET p.peso = 70, p.altezza = 1.70, p.nome = 'Fabio', p.cognome = 'Neri'
                WITH p, int
                OPTIONAL MATCH (p)-[r1:AVERE]->(pat:Patologia)
                DELETE r1
                WITH p, int
                OPTIONAL MATCH (p)-[r2:AVERE]->(int_old:Intolleranza)
                DELETE r2
                WITH p, int
                CREATE (p)-[:AVERE]->(int)
                RETURN p
        ''' },

        {"question": "Aggiorna il nodo anziano con i seguenti parametri nome: Luigi, cognome: Rossi, patologia: mal di gola , intolleranza: , peso: 90, altezza: 180"
        ,
        "query": '''
               MATCH (pa:Patologia {{id: 'Mal Di Gola'}}),
                (p:Anziano)
                SET p.peso = 90, p.altezza = 1.80, p.nome = 'Luigi', p.cognome = 'Rossi'
                WITH p, pa
                OPTIONAL MATCH (p)-[r1:AVERE]->(pat:Patologia)
                DELETE r1
                WITH p, pa
                OPTIONAL MATCH (p)-[r2:AVERE]->(int_old:Intolleranza)
                DELETE r2
                WITH p, pa
                CREATE (p)-[:AVERE]->(pa)
              
                RETURN p
        ''' },
         {"question": "Aggiorna il nodo anziano con i seguenti parametri nome: Ugo, cognome: Neri, patologia: Dolori Muscolari, intolleranza: , peso: 90, altezza: 180"
        ,
        "query": '''
               MATCH (pa:Patologia {{id: 'Dolori Muscolari'}}),
                (p:Anziano)
                SET p.peso = 90, p.altezza = 1.80, p.nome = 'Ugo', p.cognome = 'Neri'
                WITH p, pa
                OPTIONAL MATCH (p)-[r1:AVERE]->(pat:Patologia)
                DELETE r1
                WITH p, pa
                OPTIONAL MATCH (p)-[r2:AVERE]->(int_old:Intolleranza)
                DELETE r2
                WITH p, pa
                CREATE (p)-[:AVERE]->(pa)
                
                RETURN p
        ''' },

        { "question": "informazioni personali ",
        "query": '''
                MATCH (a:Anziano)
                OPTIONAL MATCH (a)-[:ESSERE_VALUTATO]->(tm:TestMobilita)
                OPTIONAL MATCH (a)-[:ESSERE_VALUTATO]->(tn:TestNutrizionale)
                OPTIONAL MATCH (a)-[:AVERE]->(sc:StatoCognitivo)
                OPTIONAL MATCH (a)-[:ESSERE_VALUTATO]->(mc:TestCognitivo)
                OPTIONAL MATCH (tp:TrattamentoPassato)-[:ASSOCIATO_A]->(a)
                OPTIONAL MATCH (a)-[:DEVE_FARE]->(tf:TerapiaFisica)
                OPTIONAL MATCH (a)-[:AVERE]->(pe:ParametriEmatici)
                OPTIONAL MATCH (a)-[:AVERE]->(n:StatoNutrizionale)
                OPTIONAL MATCH (a)-[:AVERE]->(m:StatoMobilita)
                OPTIONAL MATCH (a)-[:AVERE]->(p:Patologia)
                OPTIONAL MATCH (a)-[:AVERE]->(i:Intolleranza)
                OPTIONAL MATCH (a)-[:AVERE]->(pv:ParametriVitali)
                RETURN 
                a.id AS id,
                a.nome AS nome,
                a.cognome AS cognome,
                a.peso AS peso,
                a.altezza AS altezza,

                COLLECT(DISTINCT {{
                data: tm.data,
                punteggio: tm.punteggio
                }}) AS testMobilita,

                COLLECT(DISTINCT {{
                stato: m.stato
                }}) AS statoMobilita,

                COLLECT(DISTINCT {{
                tipo: tn.tipo,
                data: tn.data,
                punteggio: tn.punteggio
                }}) AS testNutrizionale,

                COLLECT(DISTINCT {{
                stato: n.stato
                }}) AS statoNutrizionale,

                COLLECT(DISTINCT {{
                stato: sc.stato
                }}) AS statoCognitivo,

                COLLECT(DISTINCT {{
                data: mc.data,
                punteggio: mc.punteggio
                }}) AS testCognitivo,

                COLLECT(DISTINCT {{
                id: tp.id,
                descrizione: tp.descrizione
                }}) AS trattamentoPassato,

                COLLECT(DISTINCT {{
                tipo: tf.tipo
                }}) AS terapiaFisica,

                COLLECT(DISTINCT {{
                ferro: pe.Ferro,
                emoglobina: pe.Emoglobina,
                potassio: pe.Potassio,
                glicemia: pe.Glicemia,
                sodio: pe.Sodio,
                colesteroloTotale: pe.ColesteroloTotale,
                piastrine: pe.Piastrine,
                globuliBianchi: pe.GlobuliBianchi
                }}) AS parametriEmatici,

                COLLECT(DISTINCT {{
                id: p.id,
                descrizione: p.descrizione
                }}) AS patologie,

                COLLECT(DISTINCT {{
                id: i.id,
                descrizione: i.descrizione
                }}) AS intolleranze,

                COLLECT(DISTINCT {{
                pressioneDiastolica: pv.PressioneDiastolica,
                pressioneSistolica: pv.PressioneSistolica,
                battitoCardiaco: pv.BattitoCardiaco,
                temperaturaCorporea: pv.TemperaturaCorporea,
                frequenzaRespiratoria: pv.FrequenzaRespiratoria
                }}) AS parametriVitali

                ORDER BY a.cognome, a.nome;
        ''' },

        { "question": "ricette adatte all'anziano",
        "query": '''
                MATCH (a:Anziano)-[:AVERE]->(n:StatoNutrizionale)-[:PERMETTERE]->(r:Ricetta)
                WHERE NOT EXISTS {{
                MATCH (a)-[:AVERE]->(i:Intolleranza)-[:VIETARE]->(r)
                }}
                RETURN 
                n.stato AS statoNutrizionale,
                r.id AS ricettaId,
                r.ingredienti AS ingredienti,
                r.intolleranze AS intolleranzeRicetta,
                r.Obesità AS adattaPerObesita

                ORDER BY rand();
        ''' },

        { "question": "attività adatte all'anziano",
        "query": '''
                MATCH (a:Anziano), (att:Attività)
                WHERE NOT EXISTS {{
                MATCH (a)-[:AVERE]->(p:Patologia)-[:PROIBIRE]->(att)
                }}
                RETURN 
                att.id AS attivitaId,
                att.descrizione AS descrizioneAttivita,
                att.mobilità AS livelloMobilita

                ORDER BY rand();
        ''' },
        { "question": "attività fisiche adatte all'anziano",
        "query": '''
                MATCH (a:Anziano), (att:AttivitàFisica)
                WHERE NOT EXISTS {{
                MATCH (a)-[:AVERE]->(p:Patologia)-[:PROIBIRE]->(att)
                }}
                RETURN 
                att.id AS attivitaId,
                att.descrizione AS descrizioneAttivita,
                att.livelloMobilita AS livelloMobilita

                ORDER BY rand();
        ''' },
        { "question": "informazioni dottore",
        "query": '''
                MATCH (a:Anziano), (d:Dottore)
                OPTIONAL MATCH (a)-[:DEVE_FARE]->(tf:TerapiaFisica)<-[:DETERMINARE]-(d)
                OPTIONAL MATCH (a)<-[:ASSOCIATO_A]-(tp:TrattamentoPassato)<-[:CONOSCERE]-(d)
                WHERE tf IS NOT NULL OR tp IS NOT NULL
                RETURN 
                d.id AS dottoreId,
                d.nome AS dottoreNome,

                COLLECT(DISTINCT {{
                tipo: 'TerapiaFisica',
                tipoTerapia: tf.tipo
                }}) AS terapieFisicheComuni,

                COLLECT(DISTINCT {{
                tipo: 'TrattamentoPassato',
                id: tp.id,
                descrizione: tp.descrizione
                }}) AS trattamentiPassatiComuni
        ''' },

        { "question": "informazioni parametri vitali",
        "query": '''
                MATCH (a:Anziano)-[:AVERE]->(pv:ParametriVitali)
                RETURN 
                pv.PressioneDiastolica AS pressioneDiastolica,
                pv.PressioneSistolica AS pressioneSistolica,
                pv.BattitoCardiaco AS battitoCardiaco,
                pv.TemperaturaCorporea AS temperaturaCorporea,
                pv.FrequenzaRespiratoria AS frequenzaRespiratoria
        ''' }
        ,

        { "question": "Dammi la data del test di mobilità effettuato più di recente dall'aziano nome: Giovanni, cognome: Sortino",
        "query": '''
                MATCH (a:Anziano )-[:ESSERE_VALUTATO]->(t:TestMobilita)
                RETURN t
                ORDER BY date(t.data) DESC
                LIMIT 1
        ''' }
        ,

        { "question": "Dammi la data del test di nutrizione effettuato più di recente",
        "query": '''
                MATCH (a:Anziano)-[:ESSERE_VALUTATO]->(t:TestNutrizionale)
                RETURN t.data AS data
                ORDER BY date(t.data) DESC
                LIMIT 1
        ''' }
        ,

        { "question": "informazioni parametri vitali",
        "query": '''
                MATCH (a:Anziano)-[:ESSERE_VALUTATO]->(t:TestCognitivo)
                RETURN t.data AS data
                ORDER BY date(t.data) DESC
                LIMIT 1
        ''' }
        ,

        { "question": "Dammi le TerapiePassate associate all'anziano",
        "query": '''
                MATCH (t:TrattamentoPassato)-[:ASSOCIATO_A]->(a:Anziano)
                RETURN t.descrizione AS descrizione
                ORDER BY t.id
        ''' },
         { "question": "Inserisci i parametri vitali dell'anziano rilevato nome: Fabio, cognome: Rossi, patologia:,"
         " PressioneDiastolica:60, PressioneSistolica: 100, BattitoCardiaco: 80, FrequenzaRespiratoria:20, TemperaturaCorporea:37",
        "query": '''
                MATCH (a:Anziano )-[:AVERE]->(p:ParametriVitali)
                SET 
                p.PressioneDiastolica = 60,
                p.PressioneSistolica=100,
                p.BattitoCardiaco = 80,
                p.FrequenzaRespiratoria = 20,
                p.TemperaturaCorporea = 37
                RETURN p
        ''' },
        {
         "question": "Ritornami il peso e l'altezza dell'anziano",
        "query": '''
                MATCH (a:Anziano)
                RETURN a.peso AS peso, a.altezza AS altezza
        ''' }
   


        ]


        #self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  
        #self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0.5)
        self.example_prompt_template = PromptTemplate.from_template(
                '''Domanda: {question}\nQuery: {query}'''
                )

        self.generate_query_prompt = FewShotPromptTemplate(
                examples = self.examples,
                example_prompt  = self.example_prompt_template,
                prefix = '''
        devi generare una query cypher per neo4j sintatticamente corretta da eseguire.
        Devi solamente creare o eliminare relazioni, modificare attributi oppure semplicemente cercare informazioni nel grafo. 
        Qui trovi lo schema con le informazioni del database neo4j:
        {schema}.


                ''',suffix='''Ritornami esclusivamente la query da eseguire e non aggiungere altro testo.

        Domanda: {question}
        Query: "''',
                input_variables = ["question", "schema"],
                )
        self.chain=self.generate_query_prompt | self.llm | StrOutputParser()

    def update_user_callback2(self,query):
        query='Aggiorna il nodo con i seguenti parametri '+query
        print(f"domanda inserimento grafo :  {query}",flush=True)
       
        insert_query=self.chain.invoke({"question": query, "schema": self.schema})
        print(f"query {insert_query}",flush=True)
        insert_query = insert_query.strip()

        # Rimuove tutto il blocco ```cypher ... ```
        insert_query = re.sub(r"(?s)```cypher\s*(.*?)\s*```", r"\1", insert_query).strip()
        Anziano=self.graph.query(insert_query, params={})
        print(f"grafo aggiornato: {Anziano}",flush=True)
        return True
    
    def update_user_callback(self,query):
         query = 'Aggiorna il nodo con i seguenti parametri' + query
         print(f"Domanda inserimento grafo: {query}", flush=True)

         try:
                insert_query = self.chain.invoke({"question": query, "schema": self.schema})
                print(f"Risposta da chain: {insert_query}", flush=True)
                insert_query = insert_query.strip()

                # Rimuove blocchi ```cypher ... ```
                insert_query = re.sub(r"(?s)```cypher\s*(.*?)\s*```", r"\1", insert_query).strip()
                print(f"Query Cypher pulita: {insert_query}", flush=True)

                if not insert_query:
                        print("ERRORE: La query generata è vuota.", flush=True)
                        return False
                Anziano = self.graph.query(insert_query, params={})
                print(f"Grafo aggiornato: {Anziano}", flush=True)

                # Controlla se l'esecuzione ha prodotto risultati o non ha sollevato eccezioni
                if Anziano is None:
                        print("ERRORE: Nessuna risposta dal database.", flush=True)
                        return False

                # Eventuale controllo su Anziano, es. se è un ResultSet:
                if hasattr(Anziano, '__len__') and len(Anziano) == 0:
                        print("ATTENZIONE: La query è stata eseguita ma non ha modificato il grafo.", flush=True)
                        return insert_query

                return insert_query

         except Exception as e:
                print(f"ERRORE durante l'esecuzione della query: {e}", flush=True)
                return False    
         
                
    def search_inf_callback(self, query):
        print(f"domanda richiesta grafo :{query}", flush=True)
        
        search_query = self.chain.invoke({"question": query, "schema": self.schema})
        search_query = search_query.strip()

        # Rimuove tutto il blocco ```cypher ... ```
        search_query = re.sub(r"(?s)```cypher\s*(.*?)\s*```", r"\1", search_query).strip()

        print(f"query {search_query}", flush=True)

        resp = self.graph.query(search_query, params={})
        print(f"richiesta completata------> {resp}", flush=True)
        return resp

    def delete_duplicates(self):
        check_query="""MATCH (a)-[r]->(b)
                        WITH a, b, type(r) AS relType, collect(r) AS relationships
                        WHERE size(relationships) > 1
                        RETURN a, b, relType, size(relationships) AS count
                        ORDER BY count DESC;"""
        delete_query="""
                        MATCH (a)-[r]->(b)
                        WITH a, b, type(r) AS relType, collect(r) AS relationships
                        WHERE size(relationships) > 1
                        WITH a, b, relType, relationships[1..] AS duplicates
                        UNWIND duplicates AS duplicate
                        DELETE duplicate;

                        """
        if self.execute_predefined_query(check_query):
             self.execute_predefined_query(delete_query)
             return  True
        return False

    def execute_predefined_query(self, question):
        # Recupera la query associata alla domanda
        query = question
        if query:
            response = self.graph.query(query, params={})
            return response
        else:
            return "Domanda non riconosciuta"

