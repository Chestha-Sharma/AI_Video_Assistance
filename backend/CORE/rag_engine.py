


import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough , RunnableLambda , RunnableParallel
from CORE.vector_store import load_vector_store , get_retriver , build_vector_store



def get_llm():
    return ChatMistralAI(model = "mistral-small-latest" ,api_key=os.getenv("MISTRAL_API_KEY"),temperature=0.3)

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])


def build_rag_chain(transcript : str):  # ye question bnaega or neeche waa question ko load karega

    vector_store = build_vector_store(transcript)
    retriever = get_retriver(vector_store,k=4)

    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    # full LCEL rag pipeline

    rag_chain = (
        {
            "context":retriever |RunnableLambda(format_docs),
            "question":RunnablePassthrough(), # abhi question or aage kabhi question aaye se to ye seedha trigger ho sake iske liye
         }
         | prompt | llm | StrOutputParser()
    )

    return rag_chain

def load_rag_chain(rag_chain : str):
    vector_store = load_vector_store()
    retriever = get_retriver(vector_store,k=4)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context":retriever |RunnableLambda(format_docs),
            "question":RunnablePassthrough(), # abhi question or aage kabhi question aaye se to ye seedha trigger ho sake iske liye
         }
         | prompt | llm | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str) -> str:
    print(f"Question: {question}")
    answer = rag_chain.invoke(question)
    print(f"Answer: {answer}")
    return answer
