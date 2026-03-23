from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
import json

load_dotenv()

model = ChatGroq(model="llama-3.3-70b-versatile")

class FraudAnalysis(BaseModel):
    risk_score: int
    is_suspicious: bool
    reason: str
    action: str

parser = JsonOutputParser(pydantic_object=FraudAnalysis)

template = ChatPromptTemplate.from_messages([
    ("system", "Ты фрод-аналитик. Возвращай ТОЛЬКО JSON.\n{format_instructions}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = template | model | parser

history = []

while True:
    user_input = input("Транзакция: ")
    if user_input.lower() == "выход":
        break

    try:
        response = chain.invoke({
            "input": user_input,
            "history": history,
            "format_instructions": parser.get_format_instructions(),
        })
    except Exception as e:
        print("Ошибка парсинга, попробуй ещё раз")
        continue

    history.append(HumanMessage(content=user_input))
    history.append(AIMessage(content=json.dumps(response, ensure_ascii=False)))

    if response['risk_score'] > 7:
        print(f"Транзакция заблокирована: {response['reason']}")
    else:
        print(f"Транзакция одобрена. Риск: {response['risk_score']}/10")
