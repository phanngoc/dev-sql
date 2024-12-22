
import os
import mysql.connector
from dotenv import load_dotenv
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb              # <------- HERE!


from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from operator import itemgetter
from typing import List

from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough
from model import Message

load_dotenv('.env')

# Access the OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")

db = SQLDatabase.from_uri("mysql://root:root@localhost:13306/eccubedb")


from langchain_openai import ChatOpenAI
import logging
llm = ChatOpenAI(model="gpt-4o-mini")


def get_fewshot_row():
    history_message = Message.select().order_by(Message.id.desc()).limit(12)

    example_sentences = []
    stack_q_a = {}
    for message in history_message:
        if message.role == "user":
            stack_q_a['input'] = message.content
        elif message.role == "assistant":
            stack_q_a['query'] = message.content
        if 'input' in stack_q_a and 'query' in stack_q_a:
            count = {
                'input': stack_q_a['input'],
                'query': stack_q_a['query']
            }
            example_sentences.append(count)
            stack_q_a = {}  # Reset stack_q_a after adding to example_sentences

    example_sentences = example_sentences[::-1]  # Reverse to maintain original order
    print('example_sentences:', example_sentences)
    return example_sentences


import mysql.connector

class SchemaAnalyzer:
    def __init__(self, host, user, password, database, port):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.cursor = self.connection.cursor()
        self.schema = {}

    def analyze_schema(self):
        self.cursor.execute("SHOW TABLES")
        tables = self.cursor.fetchall()

        for table in tables:
            table_name = table[0]
            self.schema[table_name] = {
                "columns": [],
                "foreign_keys": []
            }
            self._analyze_columns(table_name)
            self._analyze_foreign_keys(table_name)

    def _analyze_columns(self, table_name):
        self.cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = self.cursor.fetchall()
        for column in columns:
            self.schema[table_name]["columns"].append(column[0])

    def _analyze_foreign_keys(self, table_name):
        self.cursor.execute(f"""
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
        foreign_keys = self.cursor.fetchall()
        for fk in foreign_keys:
            self.schema[table_name]["foreign_keys"].append({
                "column": fk[0],
                "referenced_table": fk[1],
                "referenced_column": fk[2]
            })

    def get_schema(self):
        return self.schema

# Usage
analyzer = SchemaAnalyzer(
    host='127.0.0.1',
    user='root',
    password='root',
    database='eccubedb',
    port=13306
)

analyzer.analyze_schema()
schema = analyzer.get_schema()

table_name_list = list(schema.keys())
print('all table list', table_name_list)

class Table(BaseModel):
    """Table in SQL database."""

    name: str = Field(description="Name of table in SQL database.")

class SchemaChain:
    def __init__(self, table_name_list, llm, db):
        self.table_name_list = table_name_list
        self.llm = llm
        self.db = db
        self._setup_logging()
        self._setup_chain()

    def _setup_logging(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def _setup_chain(self):
        table_names = "\n".join(self.table_name_list)
        system = f"""Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
        The tables are:

        {table_names}

        Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""

        from few_shot import few_shot_prompt

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                # few_shot_prompt,
                ("human", "{input}"),
            ]
        )

        llm_with_tools = self.llm.bind_tools([Table])
        output_parser = PydanticToolsParser(tools=[Table])

        def get_tables(categories: List[Table]) -> List[str]:
            tables = []
            for category in categories:
                if category.name in self.table_name_list:
                    tables.append(category.name)
            return tables

        def log_step(step_name, data):
            self.logger.debug(f"{step_name}: {data}")
            print(f"{step_name}", data)
            return data

        table_chain = prompt | llm_with_tools | output_parser | get_tables | (lambda x: log_step("Table Chain Output", x))
        query_chain = create_sql_query_chain(self.llm, self.db) | (lambda x: log_step("Query Chain Output", x))

        table_chain = {"input": itemgetter("question")} | table_chain
        self.full_chain = RunnablePassthrough.assign(table_names_to_use=table_chain) | query_chain

    def generate_sql(self, query):
        return self.full_chain.invoke({"question": query})
    



schema_chain = SchemaChain(table_name_list, llm, db)
sql_query = schema_chain.generate_sql("Your query here")

def generate_sql(query):
    sql_query = schema_chain.generate_sql(query)
    return sql_query
