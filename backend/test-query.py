import argparse
from langchain.vectorstores.chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

CHROMA_PATH = "chromaGemini"
GOOGLE_API_KEY = "APIKEYYYY"
MODEL = "models/embedding-001"

PROMPT_TEMPLATE = """
You are a application support chatbot, below will be context retrieved from a database of information.

Answer the question based only on the following context:

{context}

---

Answer the question based on the above context, if you are unable to answer it say "I am not sure sorry, please refer to our support documentation": {question}
"""


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    # Prepare the DB.
    embedding_function = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model=MODEL)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=5)
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")
        return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print(prompt)

    model = GoogleGenerativeAI(model="models/text-bison-001", google_api_key=GOOGLE_API_KEY)
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\n\nSources: {sources}"
    print(formatted_response)


if __name__ == "__main__":
    main()
