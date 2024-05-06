from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

app = Flask(__name__)
CORS(app, resources={r"/chat/*": {"origins": "*"}})

CHROMA_PATH = "chromaGPT"
API_KEY = "APIKEYHERE_OR USE .ENV"
CHROMA_PATH = 'chromaGPT'

PROMPT_TEMPLATE = """
You are an application support chatbot, below will be context retrieved from a database of information.

Answer the question based only on the following context:

{context}

---

Answer the question based on the above context in a friendly manner, if you are unable to answer it say "I am not sure sorry, please refer to our support documentation": 

{question}
"""

# Initialize embedding function and database once
embedding_function = OpenAIEmbeddings(openai_api_key=API_KEY)
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)


@app.route('/chat', methods=['POST'])
def chat():
    
    data = request.json
    print(data)
    query_text = data.get('query_text')
    if not query_text:
        return jsonify({'error': 'No query text provided'}), 400

    # Search the DB for context
    results = db.similarity_search_with_relevance_scores(query_text, k=5)
    if len(results) == 0 or results[0][1] < 0.7:
        return jsonify({'response': 'Unable to find matching results.'})

    # Generate the context for the chatbot
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Invoke the model with the generated prompt
    model = ChatOpenAI(openai_api_key=API_KEY)
    response_text = model.invoke(prompt)

    print(response_text)

    sources = [doc.metadata.get("source", None) for doc, _score in results]
    formatted_response = {
        'response': response_text.content,
        'sources': sources
    }


    return jsonify(formatted_response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
