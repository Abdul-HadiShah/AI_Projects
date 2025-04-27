import streamlit as st
import openai
import pandas as pd
import json
import faiss
import numpy as np
import boto3
import xml.etree.ElementTree as ET
from io import StringIO

# Initialize OpenAI API key
openai.api_key = ""

# FAISS index for vector database
def create_faiss_index(dimensions=512):
    index = faiss.IndexFlatL2(dimensions)  # Using a simple L2 distance index
    return index

# Function to load and extract data from different file types
def load_data(file, file_type):
    if file_type == "json":
        return json.load(file)
    elif file_type == "csv":
        return pd.read_csv(file).astype(str).values.flatten().tolist()  # Flatten and convert to list of strings
    elif file_type == "txt":
        return file.read().splitlines()
    elif file_type == "xml":
        tree = ET.parse(file)
        root = tree.getroot()
        return [elem.tag for elem in root.iter()]
    elif file_type == "s3":
        # Connect to AWS S3 and download the file
        s3 = boto3.client('s3')
        bucket_name = 'your_bucket_name'
        file_name = 'your_file_name.txt'  # Define logic for file name
        obj = s3.get_object(Bucket=bucket_name, Key=file_name)
        return obj['Body'].read().decode('utf-8').splitlines()

# Convert text into embeddings using OpenAI API (simple example with text embeddings)
def get_embeddings(text):
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    embeddings = np.array([embedding['embedding'] for embedding in response['data']])
    return embeddings  # Return embeddings as a numpy array

# Store embeddings in FAISS vector database
def store_in_faiss(index, data):
    embeddings = [get_embeddings(item) for item in data]
    embeddings = np.array(embeddings).astype('float32')  # Ensure it's in float32 format
    print(f"Shape of embeddings: {embeddings.shape}")  # Debugging step
    index.add(embeddings)  # Add the embeddings to the FAISS index

# Query the vector database
def query_faiss(index, query, top_k=5):
    query_embedding = get_embeddings(query)
    query_embedding = query_embedding.astype('float32')
    _, indices = index.search(query_embedding, top_k)  # Find top-k nearest neighbors
    return indices

# Streamlit UI
st.title("File Query Application")
file_type = st.selectbox("Select File Type", ["json", "csv", "txt", "xml", "s3"])
uploaded_file = st.file_uploader("Upload File", type=["json", "csv", "txt", "xml"])

if uploaded_file:
    # Load the file based on selected type
    if file_type == "s3":
        # AWS S3 file is handled differently, no file upload needed
        file_data = load_data(None, "s3")
    else:
        file_data = load_data(uploaded_file, file_type)
    
    # Initialize FAISS index (assuming 512 dimensional embeddings)
    index = create_faiss_index(dimensions=512)
    
    # Store data in FAISS
    store_in_faiss(index, file_data)
    
    # User enters a query
    query = st.text_input("Enter your query")
    
    if query:
        # Query the vector database
        result_indices = query_faiss(index, query)
        
        # Show results (Retrieve the actual data from the indices)
        results = [file_data[i] for i in result_indices[0]]
        st.write("Query Results:", results)
