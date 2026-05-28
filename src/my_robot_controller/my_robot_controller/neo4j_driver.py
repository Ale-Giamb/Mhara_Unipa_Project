from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, ServiceUnavailable
import os

class Neo4jGraphConnection:
    """Wrapper per connessione diretta a Neo4j senza langchain_neo4j"""
    
    def __init__(self, uri=None, username=None, password=None):
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7690")
        self.username = username or os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "12345678")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self.driver.verify_connectivity()
            print(f"Connessione a Neo4j stabilita: {self.uri}", flush=True)
        except (DriverError, ServiceUnavailable) as e:
            print(f"ERRORE: Impossibile connettersi a Neo4j: {e}", flush=True)
            raise
    
    def query(self, query_str, params=None):
        """Esegui una query Cypher e ritorna i risultati"""
        if params is None:
            params = {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query_str, params)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"ERRORE nell'esecuzione della query: {e}", flush=True)
            raise
    
    def get_schema(self):
        """Ritorna lo schema del database"""
        schema_query = """
        CALL db.schema.visualization()
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        try:
            with self.driver.session() as session:
                result = session.run(schema_query)
                record = result.single()
                if record:
                    nodes = record.get('nodes', [])
                    relationships = record.get('relationships', [])
                    
                    # Formatta lo schema in un modo leggibile
                    schema_str = "Schema del Database Neo4j:\n\n"
                    schema_str += "NODI:\n"
                    for node in nodes:
                        schema_str += f"  - {node}\n"
                    
                    schema_str += "\nRELAZIONI:\n"
                    for rel in relationships:
                        schema_str += f"  - {rel}\n"
                    
                    return schema_str
        except Exception as e:
            print(f"ERRORE nel recupero dello schema: {e}", flush=True)
            # Ritorna uno schema alternativo usando APOC se disponibile
            return self._get_schema_fallback()
    
    def _get_schema_fallback(self):
        """Fallback per ottenere lo schema se la prima query fallisce"""
        try:
            schema_query = """
            MATCH (n)
            WITH DISTINCT labels(n) as types
            UNWIND types as type
            RETURN DISTINCT type
            ORDER BY type
            """
            with self.driver.session() as session:
                result = session.run(schema_query)
                node_types = [record['type'] for record in result if record['type']]
            
            rel_query = """
            MATCH ()-[r]-()
            RETURN DISTINCT type(r) as relType
            ORDER BY relType
            """
            with self.driver.session() as session:
                result = session.run(rel_query)
                rel_types = [record['relType'] for record in result if record['relType']]
            
            schema_str = "Schema del Database Neo4j:\n\n"
            schema_str += "NODI:\n"
            for node_type in node_types:
                schema_str += f"  - :{node_type}\n"
            
            schema_str += "\nRELAZIONI:\n"
            for rel_type in rel_types:
                schema_str += f"  - :{rel_type}\n"
            
            return schema_str
        except Exception as e:
            print(f"ERRORE nel recupero dello schema fallback: {e}", flush=True)
            return "Schema non disponibile"
    
    def close(self):
        """Chiudi la connessione"""
        if self.driver:
            self.driver.close()
    
    def __del__(self):
        self.close()
