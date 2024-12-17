
# table_chain.invoke({"input": "What customer order most product in last week ?"})

class SchemaAnalyzer:
    def __init__(self, host, user, password, database, port):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.cursor = self.conn.cursor()
        # self.nlp = spacy.load("en_core_web_md")
        self.schema_terms = self._get_schema_terms()

    def _get_schema_terms(self):
        # Execute the query to get all tables in the schema
        self.cursor.execute("SHOW TABLES")

        # Fetch all tables
        tables = self.cursor.fetchall()

        # Initialize a dictionary to store the schema
        schema = {}

        # Iterate through each table
        for table in tables:
            table_name = table[0]
            schema[table_name] = {
                "columns": [],
                "foreign_keys": []
            }
            
            # Execute the query to get all columns of the table
            mysql_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = mysql_cursor.fetchall()
            
            # Add columns to the schema
            for column in columns:
                schema[table_name]["columns"].append(column[0])
            
            # Execute the query to get foreign keys of the table
            mysql_cursor.execute(f"""
                SELECT
                    column_name,
                    referenced_table_name,
                    referenced_column_name
                FROM
                    information_schema.key_column_usage
                WHERE
                    table_name = '{table_name}' AND
                    referenced_table_name IS NOT NULL
            """)
            foreign_keys = mysql_cursor.fetchall()
            
            # Add foreign keys to the schema
            for fk in foreign_keys:
                schema[table_name]["foreign_keys"].append({
                    "column": fk[0],
                    "referenced_table": fk[1],
                    "referenced_column": fk[2]
                })
        return schema.keys()

    # def get_relevant_items_spacy(self, query, top_k=3):
    #     query_doc = self.nlp(query)
    #     relevance_scores = []
    #     for term in self.schema_terms:
    #         schema_doc = self.nlp(term)
    #         score = query_doc.similarity(schema_doc)
    #         relevance_scores.append((term, score))
    #     relevance_scores = sorted(relevance_scores, key=lambda x: x[1], reverse=True)
    #     relevant_items = relevance_scores[:top_k]
    #     return relevant_items

    def generate_sql(self, query):
        

    def create_query_chain(self, query):


    def close_connection(self):
        self.cursor.close()
        self.conn.close()
