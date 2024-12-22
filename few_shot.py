
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
# print('example_sentences:', example_sentences)

# from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# example_prompt = PromptTemplate.from_template("User input: {input}\nSQL query: {query}")
# prompt = FewShotPromptTemplate(
#     examples=example_sentences,
#     example_prompt=example_prompt,
#     prefix="You are a SQLite expert. Given an input question, create a syntactically correct SQLite query to run. Unless otherwise specificed, do not return more than {top_k} rows.\n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries.",
#     suffix="User input: {input}\nSQL query: ",
#     input_variables=["input", "top_k", "table_info"],
# )


from langchain_core.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate
)

example_prompt = ChatPromptTemplate.from_messages(
    [('human', '{input}'), ('ai', '{query}')]
)


few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=example_sentences,
    # This is a prompt template used to format each individual example.
    example_prompt=example_prompt,
)

def get_few_shot_prompt(input_text):
    return few_shot_prompt.format(input=input_text)

# temp = few_shot_prompt.format(input="how many orders in last week ?")
# print('few_shot_prompt', temp)

# final_prompt = ChatPromptTemplate.from_messages(
#     [
#         ('system', 'You are a helpful AI Assistant'),
#         few_shot_prompt,
#         ('human', '{input}'),
#     ]
# )
# final_prompt.format(input="how many orders in last week ?")
          


# # Initialize the language model
# llm = ChatOpenAI(model="gpt-4o-mini")

# # Define the input for the prompt
# input_text = "how many orders in last week?"

# # Create the chain
# chain = few_shot_prompt | llm

# # Execute the chain with the input using invoke
# response = chain.invoke({"input": input_text})

# # Print the response
# print(response.content)