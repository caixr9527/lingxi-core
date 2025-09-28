**Read this in other languages: [English](README.md), [中文](README_zh.md).**

# 《AI Application Development Platform》

> Build Intelligent Apps with Zero Code, One-Click Publishing, Infinite Scalability

## **Platform Overview**

**No coding required**—rapidly build various intelligent applications powered by advanced AI models, from simple Q&A
bots to complex logic-driven workflows. Upon completion, **publish with one click** to major social platforms, web
pages, or integrate seamlessly into existing systems via **Open APIs** for deeper development.

## **Technical Foundation**

* **[Frontend](https://github.com/caixr9527/bdjw-ai-web.git):** Vue3 (Reactive Framework) + Arco Design (
  Enterprise-Grade UI) + Tailwind CSS (Efficient Styling)
* **[Backend](https://github.com/caixr9527/bdjw-ai-ops.git):** Python 3.12 + Flask (Lightweight Web Framework) +
  LangChain 0.3 & LangGraph 0.2 (Core AI Orchestration) + Redis (Cache/Message Queue) + JWT (Secure Authentication)
* **Data Storage:** PostgreSQL (Relational Database) + Weaviate (High-Performance Vector Database)
* **Asynchronous Processing:** Celery (Distributed Task Queue)

## **Core Feature Highlights**

1. **Intelligent Homepage:** Built-in assistant Agent helps you **quickly start** creating personalized AI applications.
2. **Personal Workspace:** Centrally manage your AI applications, plugins, workflows, and knowledge base resources.
3. **Powerful AI Application Orchestration:**
    * **Custom AI Personas & Logic:** Flexibly define AI personalities, response strategies, and **optimize prompts**.
    * **Multi-Agent System (Beta):** Supports both single-Agent operation and Supervisor-coordinated multi-Agent
      systems.
    * **Rich Capability Extensions:** Integrate plugins, workflows, knowledge bases; configure **long-term memory**,
      **opening prompts/preset questions**, **user question suggestions**, **multi-language/multi-modal input/output**,
      **content moderation**, etc.
    * **MCP Client Configuration:** Adhering to the MCP protocol specification, it can seamlessly invoke external tools
      and services, enhancing external scalability.
    * **Real-Time Preview & Debugging:** Test while you build with WYSIWYG editing, boosting development efficiency.
    * **Model Flexibility:** Supports **custom LLM integration** and key parameter tuning.
    * **Version Control:** Enables **historical version rollback** for AI applications, ensuring configuration security.
4. **Effortless Application Publishing:** Offers **one-click publishing** to **Web** interfaces and **WeChat Official
   Accounts**.
5. **Multi-Dimensional Analytics:** Provides **comprehensive operational insights** for Agent applications (e.g.,
   interaction volume, effectiveness).
6. **Custom Plugin Development:** Extend platform capabilities flexibly to meet **custom business requirements**.
7. **Visual Workflow Orchestration:**
    * Rich node library: Start/End, LLM Invocation, Plugin Execution, Knowledge Retrieval, Template Transformation,
      Intent Recognition, Loop Iteration, HTTP Request, Python Code Execution, Conditional Branching, etc.
    * Supports **workflow debugging** to ensure logical accuracy.
8. **Intelligent Knowledge Base Management:**
    * Supports **multi-format document upload**, intelligent text segmentation, and preprocessing.
    * Leverages Weaviate vector database for **RAG (Retrieval-Augmented Generation) Enhanced Retrieval**: Supports
      multiple **efficient retrieval strategies** like similarity search, full-text search, hybrid search.
9. **Built-In Resource Hub:** Offers ready-to-use **pre-built application templates** and **curated plugin libraries**
   to accelerate application development.
10. **Open API Interface:** Provides comprehensive **Open APIs** to **directly invoke Agent applications**, supporting
    both **streaming** and **non-streaming** outputs for deep integration.
