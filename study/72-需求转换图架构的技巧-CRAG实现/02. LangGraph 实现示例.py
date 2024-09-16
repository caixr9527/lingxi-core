#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2024/9/16 22:02
@Author : rxccai@gmail.com
@File   : 02. LangGraph 实现示例.py
"""
from typing import TypedDict, Any

import dotenv
import weaviate
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore
from langgraph.graph import StateGraph
from weaviate.auth import AuthApiKey

dotenv.load_dotenv()


class GradeDocument(BaseModel):
    """文档评分Pydantic模型"""
    binary_score: str = Field(description="文档与问题是否关联，请回答yes或者no")


class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="执行谷歌搜索的查询语句")


class GraphState(TypedDict):
    """图结构应用程序数据状态"""
    question: str  # 原始问题
    generation: str  # 大语言模型生成内容
    web_search: str  # 网络搜索内容
    documents: list[str]  # 文档列表


def format_docs(docs: list[Document]) -> str:
    """格式化传入的文档列表为字符串"""
    return "\n\n".join([doc.page_content for doc in docs])


# 1.创建大语言模型
llm = ChatOpenAI(model="gpt-4o-mini")

# 2.创建检索器
vector_store = WeaviateVectorStore(
    client=weaviate.connect_to_wcs(
        cluster_url="https://uiufdvagtjkaf9i4ey0a.c0.us-west3.gcp.weaviate.cloud",
        auth_credentials=AuthApiKey("zGnUn1q5oI3hQUtmqP4NiRty83LNLqDaGoqw"),
    ),
    index_name="LLMOps",
    text_key="text",
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
)
retriever = vector_store.as_retriever(search_type="mmr")

# 3.构建检索评估器
system = """你是一名评估检索到的文档与用户问题相关性的评估员。
如果文档包含与问题相关的关键字或语义，请将其评级为相关。
给出一个是否相关得分为yes或者no，以表明文档是否与问题相关。"""
grade_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "检索文档: \n\n{document}\n\n用户问题: {question}"),
])
retrieval_grader = grade_prompt | llm.with_structured_output(GradeDocument)

# 4.RAG检索增强生成
template = """你是一个问答任务的助理。使用以下检索到的上下文来回答问题。如果不知道就说不知道，不要胡编乱造，并保持答案简洁。

问题: {question}
上下文: {context}
答案: """
prompt = ChatPromptTemplate.from_template(template)
rag_chain = prompt | llm.bind(temperature=0) | StrOutputParser()

# 5.网络搜索问题重写
rewrite_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个将输入问题转换为优化的更好版本的问题重写器并用于网络搜索。请查看输入并尝试推理潜在的语义意图/含义。"
    ),
    ("human", "这里是初始化问题:\n\n{question}\n\n请尝试提出一个改进问题。")
])
question_rewriter = rewrite_prompt | llm.bind(temperature=0) | StrOutputParser()

# 6.网络搜索工具
google_serper = GoogleSerperRun(
    name="google_serper",
    description="一个低成本的谷歌搜索API。当你需要回答有关时事的问题时，可以调用该工具。该工具的输入是搜索查询语句。",
    args_schema=GoogleSerperArgsSchema,
    api_wrapper=GoogleSerperAPIWrapper(),
)


# 7.构建图相关节点函数
def retrieve(state: GraphState) -> Any:
    """检索节点，根据原始问题检索向量数据库"""
    print("---检索节点---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}


def generate(state: GraphState) -> Any:
    """生成节点，根据原始问题+上下文内容调用LLM生成内容"""
    print("---LLM生成节点---")
    question = state["question"]
    documents = state["documents"]
    generation = rag_chain.invoke({"context": format_docs(documents), "question": question})
    return {"question": question, "documents": documents, "generation": generation}


def grade_documents(state: GraphState) -> Any:
    """文档与原始问题关联性评分节点"""
    print("---检查文档与问题关联性节点---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    web_search = "no"
    for doc in documents:
        score: GradeDocument = retrieval_grader.invoke({
            "question": question, "document": doc.page_content,
        })
        grade = score.binary_score
        if grade.lower() == "yes":
            print("---文档存在关联---")
            filtered_docs.append(doc)
        else:
            print("---文档不存在关联---")
            web_search = "yes"
            continue
    return {**state, "documents": filtered_docs, "web_search": web_search}


def transform_query(state: GraphState) -> Any:
    """重写/转换查询节点"""
    print("---重写查询节点---")
    question = state["question"]
    better_question = question_rewriter.invoke({"question": question})
    return {**state, "question": better_question}


def web_search(state: GraphState) -> Any:
    """网络检索节点"""
    print("---网络检索节点---")
    question = state["question"]
    documents = state["documents"]

    search_content = google_serper.invoke({"query": question})
    documents.append(Document(
        page_content=search_content,
    ))

    return {**state, "documents": documents}


def decide_to_generate(state: GraphState) -> Any:
    """决定执行生成还是搜索节点"""
    print("---路由选择节点---")
    web_search = state["web_search"]
    if web_search.lower() == "yes":
        print("---执行Web搜索节点---")
        return "transform_query"
    else:
        print("---执行LLM生成节点---")
        return "generate"


# 8.构件图/工作流
workflow = StateGraph(GraphState)

# 9.定义工作流节点
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search_node", web_search)

# 10.定义工作流边
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges("grade_documents", decide_to_generate)
workflow.add_edge("transform_query", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.set_finish_point("generate")

# 11.编译工作流
app = workflow.compile()

print(app.invoke({"question": "能介绍下什么是LLMOps么?"}))
