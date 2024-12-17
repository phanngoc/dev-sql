
import mysql.connector
import os
from dotenv import load_dotenv

import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb              # <------- HERE!


from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from operator import itemgetter
from typing import List

from langchain.chains import create_sql_query_chain
from langchain_core.runnables import RunnablePassthrough

load_dotenv('.env')

# Access the OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")

db = SQLDatabase.from_uri("mysql://root:root@localhost:13306/eccubedb")


from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")

import mysql.connector

# MySQL connection
mysql_conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='root',
    database='eccubedb',
    port=13306
)

# Create a cursor object for MySQL
mysql_cursor = mysql_conn.cursor()

# Execute the query to get all tables in the schema
mysql_cursor.execute("SHOW TABLES")

# Fetch all tables
tables = mysql_cursor.fetchall()

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

table_name_list = list(schema.keys())
print(table_name_list[:20])

class Table(BaseModel):
    """Table in SQL database."""

    name: str = Field(description="Name of table in SQL database.")


table_names = "\n".join(table_name_list)
system = f"""Return the names of ALL the SQL tables that MIGHT be relevant to the user question. \
The tables are:

{table_names}

Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{input}"),
    ]
)
llm_with_tools = llm.bind_tools([Table])
output_parser = PydanticToolsParser(tools=[Table])

def get_tables(categories: List[Table]) -> List[str]:
    tables = []
    for category in categories:
        tables.append(category.name)
    return tables

table_chain = prompt | llm_with_tools | output_parser | get_tables
query_chain = create_sql_query_chain(llm, db)
table_chain = {"input": itemgetter("question")} | table_chain


full_chain = RunnablePassthrough.assign(table_names_to_use=table_chain) | query_chain

def generate_sql(query):
    return full_chain.invoke({"question": query})
