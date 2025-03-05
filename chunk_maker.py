from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_documents(documents_texts):
    MARKDOWN_SEPARATORS = ["\n\n\n", "\n\n", "\n", " "]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,  # Set your desired chunk size here
        chunk_overlap=200,
        add_start_index=True,
        strip_whitespace=True,
        separators=MARKDOWN_SEPARATORS,
    )
    split_documents = []
    for doc in documents_texts:
        split_documents += text_splitter.split_text(doc)
    return split_documents