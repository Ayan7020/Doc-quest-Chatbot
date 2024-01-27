import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, model_validator
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings,HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS 
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models  import ChatOpenAI
from htmlTemplates import css,bot_template,user_template

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text   
     
def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(separator="\n",chunk_size=1000,chunk_overlap=200,length_function=len)
    chunks = text_splitter.split_text(raw_text)
    return chunks
 
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(texts=text_chunks,embedding=embeddings) 
    return vector_store

def get_conversation_chain(vector_store):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory, 
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    for i,mess in enumerate(st.session_state.chat_history):
        if i & 2 == 0:
            st.write(user_template.replace("{{MSG}}",mess.content),unsafe_allow_html=True) 
        else:
            st.write(bot_template.replace("{{MSG}}",mess.content),unsafe_allow_html=True)  
                

# @model_validator(pre=False, skip_on_failure=True)    
def main():
    load_dotenv()
    st.set_page_config(page_title='DocQuest Chatbot',page_icon=":books:")
    st.write(css,unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
        
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
        
        
    st.header("DocQuest Chatbot :books:")
    
    user_question = st.text_input('Ask a Question Related to Doc:')
    if user_question:
        handle_userinput(user_question)
    
    with st.sidebar:
        st.subheader("your Document")
        pdf_docs = st.file_uploader("Upload Your PDF",accept_multiple_files=True)
        if st.button("process"):
            with st.spinner("Processing"):
                raw = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw)
                vector_store = get_vectorstore(text_chunks)
                st.session_state.conversation = get_conversation_chain(vector_store)
    st.write(user_template.replace("{{MSG}}","Ayan"),unsafe_allow_html=True)            
    st.write(bot_template.replace("{{MSG}}","Hello"),unsafe_allow_html=True)            
    
if __name__=='__main__':
    main()    