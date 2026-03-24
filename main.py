from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
import json
import os

load_dotenv()

model = ChatGroq(model="llama-3.3-70b-versatile")


class FraudAnalysis(BaseModel):
    risk_score: int
    is_suspicious: bool
    reason: str
    action: str


parser = JsonOutputParser(pydantic_object=FraudAnalysis)

VECTORSTORE_PATH = "fraud_vectorstore"

print("Инициализация эмбеддингов...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def setup_rag_knowledge_base():
    try:
        if not os.path.exists("documents.txt"):
            print("ОШИБКА: Файл documents.txt не найден!")
            return None

        if os.path.exists(VECTORSTORE_PATH):
            print("Загружаю векторную БД из кэша...")
            vectorstore = FAISS.load_local(
                VECTORSTORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("Векторная БД загружена!")
        else:
            print("Создаю векторную БД из documents.txt...")
            loader = TextLoader("documents.txt", encoding="utf-8")
            documents = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = splitter.split_documents(documents)
            print(f"Создано {len(chunks)} фрагментов")

            vectorstore = FAISS.from_documents(chunks, embeddings)
            vectorstore.save_local(VECTORSTORE_PATH)
            print("Векторная БД сохранена в кэш!")

        return vectorstore

    except Exception as e:
        print(f"Ошибка при инициализации RAG: {e}")
        return None


def retrieve_relevant_rules(vectorstore, transaction_description, k=3):
    try:
        docs = vectorstore.similarity_search(transaction_description, k=k)
        return "\n---\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"Ошибка при поиске правил: {e}")
        return "Ошибка при поиске в базе знаний. Используй общие правила."


print("\n=== Инициализация системы ===")
vectorstore = setup_rag_knowledge_base()

if not vectorstore:
    print("\nВНИМАНИЕ: Система работает без RAG.")

template = ChatPromptTemplate.from_messages([
    ("system", """Ты фрод-аналитик с доступом к базе знаний правил обнаружения мошенничества.

Контекст из базы знаний:
{rag_context}

Используй эти правила для анализа транзакции.
Возвращай ТОЛЬКО JSON без дополнительного текста.
{format_instructions}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = template | model | parser

history = []

print("\n=== Антифрод система с RAG ===")
print("Введите данные транзакции (или 'выход' для завершения)")
print("Пример: Сумма 15000 руб, Страна Россия, Время 03:30\n")

while True:
    user_input = input("\nТранзакция: ")

    if user_input.lower() == "выход":
        break

    if not user_input.strip():
        print("Введите данные транзакции")
        continue

    rag_context = "База знаний недоступна. Используй общие правила фрод-мониторинга."

    if vectorstore:
        print("[Поиск релевантных правил...]")
        rag_context = retrieve_relevant_rules(vectorstore, user_input)
        rules_count = rag_context.count("---") + 1
        print(f"[Найдено {rules_count} релевантных правил]")

    try:
        response = chain.invoke({
            "input": user_input,
            "history": history,
            "format_instructions": parser.get_format_instructions(),
            "rag_context": rag_context,
        })
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        print("Попробуйте переформулировать описание транзакции")
        continue

    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=json.dumps(response, ensure_ascii=False)))

    print(f"\n{'=' * 50}")
    if response['risk_score'] > 7:
        print("ТРАНЗАКЦИЯ ЗАБЛОКИРОВАНА!")
        print(f"Риск: {response['risk_score']}/10")
        print(f"Причина: {response['reason']}")
        print(f"Действие: {response['action']}")
    elif response['risk_score'] > 4:
        print("ВНИМАНИЕ: Повышенный риск!")
        print(f"Риск: {response['risk_score']}/10")
        print(f"Причина: {response['reason']}")
        print(f"Действие: {response['action']}")
        print("Рекомендуется дополнительная проверка")
    else:
        print("ТРАНЗАКЦИЯ ОДОБРЕНА")
        print(f"Риск: {response['risk_score']}/10")
        print(f"Причина: {response['reason']}")
        print(f"Действие: {response['action']}")
    print(f"{'=' * 50}")

print("\nСессия завершена.")