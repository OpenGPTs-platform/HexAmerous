```python
from langchain.document_loaders import(
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader
)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.text_splitter import CharacterTextSplitter
import openai
from dotenv import load_dotenv
import os
from chatgpt import search_gpt
from ye_logger_of_yor import get_logger

logger = get_logger('Init log')

load_dotenv()

logger.info('Loading global variables')
#Load Langchain variables
openai.api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings()
llm = OpenAI(temperature=0)
text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=25)
vectorstore ='docs/index'
new_vectorstore = ''

logger.info('loading change_vectorstore function')
def change_vectorstore(optional_arg="new_vectorstore"):
    logger.info('running change_vectorstore')
    vectorstore
    new_vectorstore
    if not new_vectorstore:
        return vectorstore
    else:
        vectorstore = new_vectorstore
    print(vectorstore)
    return vectorstore

logger.info('base_formatter function')
def base_formatter(docs):
    logger.info('formatting')
    print(f"\n{'-' * 100}\n".join([f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)]))
    return (f"\n{'-' * 100}\n".join([f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)]))

logger.info('loading check_file function 43')
#Check if the files are valid
def check_file(file_path):
    logger.info('checking file')
    if file_path.endswith('.txt'):
        loader = TextLoader(file_path)
        print(loader.load())
        return loader.load()
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        print("pdf file loaded")
        return loader.load()
    if file_path.endswith('.md'):
        loader = UnstructuredMarkdownLoader(file_path)
        logger.info(loader.load())
        return loader.load()

logger.info('loading create_mass_embedding function')
#Loop files in a folder path for embedding
def create_mass_embedding(folder_path):
    logger.info('creating mass embedding')
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        result = create_embedding(file_path, filename)
        print(f"Embedding created for {filename}: {result}")

    return "Embeddings created"

logger.info('create_embedding function')
#Embed a single embedding
def create_embedding(file_path, optional_arg="metadata"):
    logger.info('creating embedding')
    data =check_file(file_path)
    metadata = optional_arg
    if metadata:
        meta = metadata
    else:
        meta = 'file_path'
    vectordb = Chroma.from_documents(documents=data, metadata=meta, embedding=embeddings, persist_directory='docs/')
    vectordb.persist()
    return "Embedding created"

#Load vectorstore database
logger.info('load_embedding function')
def load_embedding():
    logger.info('loading embedding')
    vectorstore = change_vectorstore()
    chromadb = Chroma(persist_directory=vectorstore, embedding_function=embeddings)
    return chromadb

logger.info('base_retriever function')
#Search for uncompressed docs in database
def base_retriever(user_query):
    logger.info('running base_retriever')
    retriever = load_embedding().as_retriever(llm=llm)
    docs = retriever.get_relevant_documents(user_query)
    return docs

logger.info('retriever function')
#Search for compressed docs in database
def retriever(user_query):
    logger.info('running retriever')
    compressor = LLMChainExtractor.from_llm(llm)
    retriever = load_embedding().as_retriever(llm=llm)
    cc_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)
    compressed_docs = cc_retriever.get_relevant_documents(user_query)
    docs = compressed_docs
    return docs

logger.info('load_vector_store_docs function')
def load_vector_store_docs():
    logger.info('running load_vector_store_docs')
    vectorstore = change_vectorstore()
    chromadb = Chroma(persist_directory=vectorstore, embedding_function=embeddings)
    docs = chromadb.documents
    return docs

logger.info('memory_search function')
#Query the database and pass the info to chatgpt for response
def memory_search(user_query):
    logger.info('running memory_search')
    data = base_retriever(user_query)
    prompt = [{
        "role":"system",
        "content":'''
        "The user has asked this question:

        {user_query}

        You have looked up the relevant information from your data store and it is:

        {data}

        Please answer the user's question using the data as relevant context."
        '''.format(user_query=user_query, data=data)
    }]

    result = search_gpt(user_query, prompt)

    return result
```