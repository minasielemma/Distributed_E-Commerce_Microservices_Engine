import logging
import threading
from django.conf import settings

try:
    from neo4j import GraphDatabase, Driver
except ImportError:
    GraphDatabase = None
    Driver = None

logger = logging.getLogger(__name__)

class Neo4jClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Neo4jClient, cls).__new__(cls)
                cls._instance._driver = None
            return cls._instance

    def get_driver(self):
        if not GraphDatabase:
            logger.error("neo4j library is not installed.")
            return None

        if self._driver is None:
            with self._lock:
                if self._driver is None:
                    try:
                        uri = getattr(settings, 'NEO4J_URI', 'bolt://neo4j:7687')
                        user = getattr(settings, 'NEO4J_USER', 'neo4j')
                        password = getattr(settings, 'NEO4J_PASSWORD', 'recommendation_pass')
                        
                        if user and password:
                            auth = (user, password)
                        else:
                            auth = None

                        self._driver = GraphDatabase.driver(
                            uri,
                            auth=auth,
                            max_connection_lifetime=30 * 60,
                            max_connection_pool_size=50,
                            connection_acquisition_timeout=2.0
                        )
                        self._init_schema()
                    except Exception as e:
                        logger.error(f"Failed to connect to Neo4j at {uri}: {e}")
                        self._driver = None
        return self._driver

    def _init_schema(self):
        """Ensure indexes/constraints exist in Neo4j."""
        if not self._driver:
            return
        
        schema_queries = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
            "CREATE INDEX product_tenant_idx IF NOT EXISTS FOR (p:Product) ON (p.tenant_id)",
            "CREATE INDEX user_tenant_idx IF NOT EXISTS FOR (u:User) ON (u.tenant_id)",
        ]
        
        try:
            with self._driver.session() as session:
                for query in schema_queries:
                    try:
                        session.run(query)
                    except Exception as q_err:
                        logger.warning(f"Neo4j schema query failed (might already exist or community edition syntax): {q_err}")
        except Exception as e:
            logger.error(f"Failed initializing Neo4j schema: {e}")

    def execute_query(self, cypher, parameters=None):
        """
        Executes a Cypher query with parameters.
        Returns list of record maps or [] if failed/offline.
        """
        driver = self.get_driver()
        if not driver:
            logger.warning("Neo4j driver uninitialized. Returning empty result.")
            return []

        parameters = parameters or {}
        try:
            with driver.session() as session:
                result = session.run(cypher, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query execution error: {e}. Cypher: {cypher}")
            self._driver = None
            return []

    def close(self):
        with self._lock:
            if self._driver:
                try:
                    self._driver.close()
                except Exception as e:
                    logger.error(f"Error closing Neo4j driver: {e}")
                self._driver = None

neo4j_client = Neo4jClient()
