from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

loader = TextLoader(r"C:\Users\alex\Desktop\langchain_first\documents.txt", encoding="utf-8")

documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

template = ChatPromptTemplate.from_messages([
    ("system", """Ты helpful ассистент. Отвечай на вопросы ТОЛЬКО на основе предоставленного контекста.
Если ответа нет в контексте — так и скажи.

Контекст:
{context}"""),
    ("human", "{question}"),
])

model = ChatGroq(model="llama-3.3-70b-versatile")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {
        "context": retriever | format_docs,
        "question": lambda x: x
    }
    | template
    | model
    | StrOutputParser()
)

question = input("Вопрос: ")
response = chain.invoke(question)
print(response)