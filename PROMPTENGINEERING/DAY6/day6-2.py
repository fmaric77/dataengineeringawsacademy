from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
import re

# Define Pydantic model
class MovieReview(BaseModel):
    movie_name: str = Field(description="Name of the movie")
    review_sentiment: str = Field(description="Sentiment of the review (positive or negative)")
    lead_actor_name: str = Field(description="Name of the leading actor in the movie")
    director_name: str = Field(description="Name of the director of the movie")

# Define tools
@tool
def analyze_sentiment(review: str) -> str:
    """Analyzes the sentiment of the review using AI"""
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    model = ChatBedrock(model_id=model_id)
    messages = [
        SystemMessage(content="You are a sentiment analysis tool."),
        HumanMessage(content=review)
    ]
    response = model.invoke(messages)
    sentiment = "positive" if "positive" in response.content.lower() else "negative"
    return sentiment

@tool
def extract_movie_details(wiki_content: str) -> dict:
    """Extracts the lead actor and director from the Wikipedia content using AI"""
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    model = ChatBedrock(model_id=model_id)
    
    extraction_prompt = f"""
    Given the following Wikipedia content, extract the lead actor and director names:
    
    {wiki_content}
    
    Provide the lead actor and director in the format:
    Lead Actor: [Name]
    Director: [Name]
    """
    
    messages = [
        SystemMessage(content="You are an information extraction tool."),
        HumanMessage(content=extraction_prompt)
    ]
    
    response = model.invoke(messages)
    details = {
        "lead_actor_name": "Unknown",
        "director_name": "Unknown"
    }
    
    # Define patterns for lead actor and director
    lead_actor_patterns = [
        r'Lead Actor:\s*([^\n]+)',
        r'Leading Actor:\s*([^\n]+)',
        r'Main Actor:\s*([^\n]+)',
        r'Starring:\s*([^\n]+)',
        r'Cast:\s*([^\n]+)'
    ]

    director_patterns = [
        r'Director:\s*([^\n]+)',
        r'Directed by:\s*([^\n]+)',
        r'Filmmaker:\s*([^\n]+)',
        r'Producer:\s*([^\n]+)'
    ]

    # Function to match patterns
    def match_patterns(patterns, content):
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    # Extract lead actor
    lead_actor_name = match_patterns(lead_actor_patterns, response.content)
    if lead_actor_name:
        details["lead_actor_name"] = lead_actor_name

    # Extract director
    director_name = match_patterns(director_patterns, response.content)
    if director_name:
        details["director_name"] = director_name

    # Print extracted details for debugging
    print(f"Extracted lead actor: {details['lead_actor_name']}")
    print(f"Extracted director: {details['director_name']}")
    
    return details

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1000)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)

# Bind tools to model
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model = ChatBedrock(model_id=model_id).bind_tools([analyze_sentiment, wiki_tool, extract_movie_details])

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the tools at your disposal to parse the movie review and fetch additional details."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

tools = [analyze_sentiment, wiki_tool, extract_movie_details]
agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Invoke agent
review = '"Inception" is an overly complex and confusing film that fails to engage audiences. The convoluted narrative and excessive exposition bog down the pacing, making it a frustrating viewing experience.'
response = agent_executor.invoke({"input": review})

# Extract information from response
movie_name_match = re.search(r'"([^"]+)"', review)
movie_name = movie_name_match.group(1) if movie_name_match else "Unknown"
review_sentiment = analyze_sentiment(review)

# Fetch additional details from Wikipedia
wiki_response = wiki_tool.invoke(movie_name)

# Use AI to extract lead actor and director names from the Wikipedia response
details = extract_movie_details(wiki_response)

# Create Pydantic object
movie_review = MovieReview(
    movie_name=movie_name,
    review_sentiment=review_sentiment,
    lead_actor_name=details["lead_actor_name"],
    director_name=details["director_name"]
)

# Print the structured movie review
print(movie_review)