from fastapi import FastAPI, HTTPException, Body, File, UploadFile,Form
from fastapi.responses import JSONResponse
from utils.llms import llm_with_tool
from services.tools import act, order, list_response, followup_handler
from fastapi.middleware.cors import CORSMiddleware

# Custom Imports
from services.milvus_services import insert, search,delete_colletion
from services.llm_response import llm

# <----- FastAPI ----->
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# <----- ENDPOINTS ----->
@app.get("/")
async def root():
    return JSONResponse(content="Hello from The Laws!!!", status_code=200)

# <----- File Upload ----->
@app.post("/upload")
async def ask(category: str = Form(...), file: UploadFile = File(...)):
    file_name = file.filename
    allowed_extensions = ["pdf", "json"]
    file_extension = file_name.split(".")[-1]
    f_name = file_name.split(".")[0]
    print(f"File Extension: {file_extension}")

    if file_extension not in allowed_extensions:
        return JSONResponse(content="Unsupported file format!!!", status_code=400)
    
    if not category:
        return JSONResponse(content="Category Invalid!!!", status_code=400)
    
    response = insert(collection=category, file_name=f_name, file_type=file_extension, file=file)
    if response:
        return JSONResponse(content="success", status_code=200)
    else:
        raise HTTPException(detail="There was an error inserting Data", status_code=400)

# <----- Chat ----->
@app.post("/chat")
async def chat(request: dict =  Body(...)):
    query = request.get("query")
    # tool_llama = llm_with_tool(act, order)
    chat_history = request.get("chat_history", [])
    # current_intent = request.get("intent")
    # prompt = f"""You are an Legal AI assistant with access to the following tools:
    # 1. act: Use this tool to provide details about Indian Acts and their sections.
    # 2. order: Use this tool to fetch or explain Indian court orders or judgements.

    # Rule:
    # - When a user query matches the function of a tool, Always CALL the tool 
    # - Do NOT just suggest which tool could be called
    # - Only if the query does NOT match any tool, respond normally.

    # User's Last Query is About  :{current_intent}
    
    # Query:
    # {query}
    # """
    # try:
        # intent_prompt = {"role" : "human" , "content" : prompt}
        # chat_history.append(intent_prompt)
        # res=tool_llama.invoke(input=chat_history)
        # initial_token=res.usage_metadata["total_tokens"]
        # chat_history.pop()

        # if(res.tool_calls):
            # print(f"Intent Tool Called:{res.tool_calls[0]['name']}")
    listtool=llm_with_tool(followup_handler)
    listprompt=f"""You are a Legal AI assistant.  
    You have access to 1 tool: `followup_handler`.  

    You MUST CALL `followup_handler` if:  
    1. The user's message is a follow-up to a previous conversation.  
    2. The user's message is unclear, ambiguous, or lacks sufficient context to provide a confident answer.  

    Examples:  
    - User: "What does the Indian Contract Act, 1872 say about minors entering contracts?"  
    Assistant: "It states that contracts with minors are void from the beginning."  
    User: "What about exceptions?"  
    Tool: `followup_handler`  

    - User: "Explain the legal implications here." (without context)  
    Tool: `followup_handler`  

    Query:  
    {query}
    """
    toolprompt={"role":"human","content":listprompt}
    chat_history.append(toolprompt)
    listres=listtool.invoke(input=chat_history)
    chat_history.pop()
    list_token=0
    if(listres.tool_calls):
        list_token=listres.usage_metadata["total_tokens"]
        if(listres.tool_calls[0]['name']=="followup_handler"):
            query=listres.tool_calls[0]['args']['query']
            print(f"Restructured Query: {query}")
            context = search(query=query,collection="order",islist=False,radius=0.6)
    else:
            context = search(query=query,collection="order",islist=False,radius=0.6)
    if(context):
        ids=context[1]
        response = llm(query=query,chat_history=chat_history, context=context[0])
        response=list(response)
        response[1] = response [1]  + list_token
        response.append("order")
        response.append(ids)
        return JSONResponse(content=response, status_code=200)
    else:
        response=["Sorry, but I couldn't find any relevant information related to your query. Kindly provide additional details or clarify your request so I may assist you accurately.",list_token,"order",[]]
        return JSONResponse(content=response,status_code=200)
        # else:
        #     return ["As a Legal Assistant, my role is to provide information and guidance on legal matters.\n\nTo answer your question, I would need to provide information outside of my designated scope. Instead, I would like to inform you to ask a question relevant to a legal context, such as contract law, intellectual property, or any other legal topic. I'll be happy to assist you with that.\n\nPlease ask a question related to law, and I'll do my best to provide a helpful response.",initial_token,current_intent]
    # except Exception as e:
    #     if "rate limit" in str(e).lower():
    #         raise HTTPException(status_code=429, detail="Groq rate limit exceeded. Try Again After 24 Hours")
    #     print(e)
    #     raise  HTTPException(status_code=500, detail=str(e))

# <------ Delete------->
@app.post("/delete")
async def delete(delete: str = Body(...)):
    if delete=="Yes":
        delete_colletion()
    
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="localhost", port=5000, reload=True)