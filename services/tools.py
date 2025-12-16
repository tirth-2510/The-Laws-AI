from langchain_core.tools import tool



@tool
def act(query:str):
    '''
    Use this tool to fetch, interpret, and explain provisions from Central or State Acts.

    Purpose:
    - To assist in interpreting statutory provisions, their applicability, scope, and meaning.
    - To provide plain-language summaries or explanations of sections, clauses, and subsections from Acts.
    - To clarify cross-references within Acts or between related laws.

    Trigger Conditions:
    - Call this tool whenever the user asks about:
        * Any provision, section, clause, or subsection of a Central or State Act.
        * Legal interpretation or effect of a statutory provision.
        * Applicability, exceptions, or amendments under an Act.
        * References such as “Section 7 of CPC”, “as per the Companies Act”, etc.

    Non-Trigger Conditions: Queries About Following:
    - Court Orders (interim or final)
    - Procedural steps under CPC Orders and Rules
    - judgments, or tribunal decisions
    - Notifications, circulars, or government orders
    - State amendments to procedural rules (unless part of the Act text)
    - Supreme Court judgments
    - High Court judgments
    - Any Court Judgements
    Example Queries:
    -     "Suit can withdraw at any time as per the order 23 rule 1"
    -     "when the prima facie the provisions of sc/st (poa) not applicable, the petition for anticipatory bail maintainable"
    -     "What are the primary elements that need to be established to prove action under act of defense?"
    -     "What is the recent amendment in section 11 arbitration?"
    -     "What are the legal remedies available to an individual for violation of Right to Privacy?"
    -     "The suit is file for adverse possession.Limitation for the  filing of the suit  If any case law please send it"
    -     "When there is no doctor certificate attached to the WILL, the said WILL is not legal and valid."
    -     "Before the completion of the loan bank without recall the loan can not demand the outstanding amount. The bank only demand the overdue amount"
    '''
    pass

@tool
def order(query: str):

    """
    Use this tool to retrieve or summarize Indian court judgments,identify, classify, and explain court orders.

    Includes:
    - Supreme Court judgments,order
    - High Court judgments,order
    - Tribunal decisions (if applicable)
    - Any Court Judgements,order

    Trigger this tool whenever the user asks about:
    - Specific case laws or citations
    - Landmark judgments
    - Legal precedents in India
    - Court rulings related to a topic 
    - The “type” or “classification” of any court order.
    - Whether an order is CPC, CrPC, or general High Court administrative order.
    - Meaning of expressions in orders (e.g., "Rule discharged", "Dismissed", "Allowed").
    - Effect of an oral order or short order passed by any court.
    - Procedural implications of interim or final orders.
    
    Non-Trigger Conditions:Queries About Following:
    - Central Acts (e.g., IPC, Companies Act, IT Act, GST Act)
    - State-specific Acts
    - Explanations of legal sections
   
    Example Queries:
    - "Which type of order is this? It only says 'Dismissed. Rule discharged.'"  
    - "Is this order passed under CPC or CrPC?"
    - "What is the meaning of an oral order from the High Court?"
    - "Does this order count as a final order or interim order?"
    - "What is the effect of 'Rule made returnable' in an order?"
    - "What does it mean when a court says 'Notice discharged'?"
    - "Is this order a decreee,judgement, or procedural order?"
    - "Does this order fall under Order 39 CPC or CrPC 482?"
    - "Is there any judgment showing how much period needs to expire for an asset to become npa under sarfaesi act"
    - "Provide Supreme court judgments discussing the rights of daughters in a coparcenary property."
    - "First applicant (loan borrower) obtained a loan but the bank didnt get a life insurance policy assigned to bank. Please send citation for the same."
    - "Under Maharashtra Tenancy and Agricultural Lands Act, 1948 Relating to  Sec. 70 B"
    - "Please share the case law of Supreme Court Promoter & Builder can not sell common terrace and parking space"
    - "Witness came in the witnesses box one time and given half evidence but thereafter didnot come   whether the evidence discard or not"
    - "Between the two wills notary has been same and witness is differed then its must be call the notary for evidence"
    - "Provide Supreme court judgments discussing the rights of daughters in a coparcenary property."
    - "I need judgements. Estoppel under SARFASI Act for issuing second notice after withdrawal of proceedings under first notice"
    - "Judgement revision against interlocutory order of rejection of handwriting expert as defence witness"
    - "Provide me the latest judgments of Gujarat Hight court on Land Grabing"
       

    """
    pass

@tool
def list_response(query:str):
    '''
    This tool is designed to handle user queries that explicitly request a 
    list of legal matters such as acts, sections, cases, or other legal topics.  

    Trigger Condition:
    - Invoke this tool when the user clearly asks for a list of legal information 
    (e.g., acts, sections, or cases).
 
    Non-Trigger Condition:

    - Do not invoke this tool if the user's query is vague, underspecified, or 
    requires clarification through a follow-up question.  

    Examples of when to invoke:
    
    - "List all cases related to domestic violence"
    - "Show me the top 10 labor law cases"
    - "Provide some sections of IPC related to theft"

    '''
    pass

@tool 
def followup_handler(query:str):
    '''
    -  This tool is designed to resturcture the vague or underspecified follow-up query.
    If the query is identified as a follow-up,the tool evaluates whether it is vague or 
    underspecified. In cases where the query lacks clarity, context, or explicit details, 
    the tool restructures and rephrases the query into a clearer and more explicit form 
    that is easier for the LLM to understand and respond to accurately.

    Key responsibilities:
    - Detect if the query is a follow-up question.
    - Identify vague, incomplete, or ambiguous queries.
    - Restructure vague follow-up queries into well-formed, self-contained and detailed queries like shown in example.

    Intended use:
    - To improve conversational continuity and reduce ambiguity.
    - To ensure the LLM receives clear, structured inputs, leading to 
      more accurate and context-aware responses

       
    Example:
    ---
      
    --
    - User: "What does the Indian Contract Act, 1872 say about minors entering contracts?"
    - Assistant: "It states that contracts with minors are void from the beginning"
    - User: "What about exceptions?"
    - Tool → Restructured: "What are the exceptions to the rule that contracts with minors are void under the Indian Contract Act, 1872?"

    ---

    - User: "Explain the doctrine of precedent in common law."
    - Assistant: "It means courts must follow previous judicial decisions when deciding similar cases."
    - User: "And in India?"
    - Tool → Restructured: "How does the doctrine of precedent apply within the Indian legal system?"

    --- 

    - User: "Tell me about Article 21 of the Indian Constitution."
    - Assistant: "Article 21 guarantees the right to life and personal liberty."
    - User: "What about its recent interpretation?"
    - Tool → Restructured: "What is the recent judicial interpretation of Article 21 of the Indian Constitution?"

    ---

    - User: "What is intellectual property?"
    - Assistant: "It refers to creations of the mind, like inventions, literary works, and symbols."
    - User: "Can you explain more?"
    - Tool → Restructured: "Can you explain in more detail the different types of intellectual property rights?"
   
    '''
    pass