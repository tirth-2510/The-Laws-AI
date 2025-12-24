from pymilvus import MilvusClient, CollectionSchema, FieldSchema, DataType,AnnSearchRequest,Function,FunctionType,RRFRanker
from services.extractors import extractor
from services.embedder import generate_embeddings, search_embeddings
from utils.chunker import  create_ids

import time
import os
from dotenv import load_dotenv

load_dotenv()

bm25_function = Function(
    name="text_bm25_emb",
    input_field_names=["text"], 
    output_field_names=["sparse"],
    function_type=FunctionType.BM25, 
)
schema = CollectionSchema(
    fields=[
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=50),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768, metric_type="COSINE"),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
        FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR,metric_type="COSINE")
    ],
    description="Collection for storing text embeddings",
)
schema.add_function(bm25_function)

milvus_client = MilvusClient(uri=os.getenv("ZILLIS_URI_ENDPOINT"), token=os.getenv("ZILLIS_TOKEN"), password=os.getenv("ZILLIS_PASSWORD"), db_name=os.getenv("ZILLIS_DB_NAME"))
# milvus_client = MilvusClient(uri=os.getenv("MILVUS_URI"), db_name=os.getenv("MILVUS_DB_NAME"))
                
def create_collection(collection: str) -> dict:
    index_params = milvus_client.prepare_index_params()

    index_params.add_index(
        field_name="vector", 
        index_type="HNSW",
        metric_type="COSINE",
        efConstruction=256,
        M=64
    )
    index_params.add_index(
        field_name="sparse",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
        params={
            "inverted_index_algo": "DAAT_MAXSCORE",
            "bm25_k1": 1.2, #controls frequency saturation
            "bm25_b": 0.75 #controls document length nomalization
        }
    )

    try:
        milvus_client.create_collection(
            collection_name=collection,
            schema=schema,
            index_params=index_params,
        )
        return {"status": 200, "message": "created"}
    except Exception as e:
        return {"status": 400, "message": str(e)}

def insert(collection: str, file_name: str,  file_type: str, file) -> dict | None:
    chunks = extractor(file=file, type=file_type, category=collection)
    print("length of chunks:", len(chunks))
    current_time = time.time()
    embeddings = generate_embeddings(chunks)
    embedding_time = time.time()
    print("Time taken:", embedding_time - current_time)
    print("length of embeddings:", len(embeddings))

    # Check if Collection Exist
    collection_exist = milvus_client.has_collection(collection_name=collection)
    if not collection_exist:
        collection_response = create_collection(collection=collection)

        # Collection Created Successfully?
        if collection_response["status"] != 200:
            return collection_response["message"]

    chunk_ids = create_ids(name=file_name, length=len(chunks))
    data_to_insert = [{"id": chunk_id, "vector": embedding, "text": chunk} for embedding, chunk, chunk_id in zip(embeddings, chunks, chunk_ids)]
    response = milvus_client.insert(
        collection_name=collection,
        data=data_to_insert,
    )
    print("Inserted Data")
    print("Response from Milvus:", response)
    return response if response else None

def search(query: str,collection:str) -> str:
    search_query = search_embeddings(query=query)

    context=""

    search_param_1 = {
        "data": [search_query],
        "anns_field": "vector",
        "param": {"efSearch": 512},
        "limit": 2
    }
    request_1 = AnnSearchRequest(**search_param_1)

    search_param_2 = {
        "data": [query],
        "anns_field": "sparse",
        "param": {"drop_ratio_search": 0.0},
        "limit": 2
    }
    request_2 = AnnSearchRequest(**search_param_2)
    
    req=[request_1,request_2]
    ranker = RRFRanker(100)

    documents = milvus_client.hybrid_search(
    collection_name=collection,
    reqs=req,
    ranker=ranker,
    limit=5,
    output_fields=["text","id"]
)
    
    document_id=[]
    if documents:
        for document in documents:
            for doc in document:
                data=doc.get("entity",doc)
                document_id.append(data.get('id').split("_@_")[0])            
                print(f"Id: {data.get('id')}\nDistance: {doc.get('distance')}\nContent: {data.get('text')}\n")
                context+= f"\nContext: {data.get('text')}\n"
    document_id=set(document_id)
    document_id=list(document_id)
    if context:
        return context,document_id 
    else:
        print("No Context Passed")
        return None

def delete_colletion():
    collections= milvus_client.list_collections()
    for collection in collections:
        milvus_client.drop_collection(collection)
        print(f"Dropped {collection}")
