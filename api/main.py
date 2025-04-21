# --- api/main.py (Single Call OpenAI GPT-4o Approach) ---
import sys
print("--- DEBUG: main.py TOP LEVEL EXECUTION ---", flush=True)
# Print Python version and path just in case
print(f"--- DEBUG: Python Version: {sys.version} ---", flush=True)
print(f"--- DEBUG: Python Path: {sys.path} ---", flush=True)

try:
    from fastapi import FastAPI
    print("--- DEBUG: Imported FastAPI ---", flush=True)
    app = FastAPI()
    print("--- DEBUG: FastAPI app created ---", flush=True)

    @app.get("/ping")
    def ping():
        print("--- DEBUG: /api/ping called ---", flush=True)
        return {"message": "pong"}

    print("--- DEBUG: Defined /api/ping ---", flush=True)

except Exception as e:
    print(f"--- DEBUG: ERROR during setup: {e} ---", flush=True)
    # Optionally re-raise or handle differently
    raise e
    
from pydantic import BaseModel
import os
import openai # Import the OpenAI library
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import json # For parsing JSON output from LLM
import time # Optional: for potential retries

print("DEBUG: Starting main.py execution...")
logging.info("DEBUG: Logging configured.") # Use logger too

# Load environment variables (for API keys)
# Looks for a .env file in the root directory where you run uvicorn
load_dotenv()

# --- IMPORTANT: Set your OpenAI API Key as an environment variable ---
# Name it OPENAI_API_KEY (e.g., in .env file or Vercel settings)
openai.api_key = os.getenv("OPENAI_API_KEY")

print(f"DEBUG: OpenAI Key loaded: {'Yes' if openai.api_key else 'NO - MISSING!'}") # Check if key loads

if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not found.")
    # Decide if you want the app to fail here or proceed (it will fail on API call)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Define your BN structure (nodes and parent dependencies)
# Used for describing the structure in the prompt
NODE_PARENTS = {
    "A1": [], "A2": [], "A3": [], "A4": [], "A5": [], "UI": [], "H": [],
    "IS1": ["A1", "A2", "A3", "A5", "UI", "H", "IS3", "IS5"],
    "IS2": ["A2", "A5", "UI"],
    "IS3": ["A1", "A2", "UI", "H", "IS2"],
    "IS4": ["A3", "A4", "H"],
    "IS5": ["A1", "A3", "IS4"],
    "O1": ["IS1", "IS3", "IS4", "IS5"],
    "O2": ["IS1"],
    "O3": ["IS3", "IS5"]
}
# All nodes in the network
ALL_NODES = list(NODE_PARENTS.keys())
# Nodes for which we want the LLM to estimate probabilities
TARGET_NODES = ["IS1", "IS2", "IS3", "IS4", "IS5", "O1", "O2", "O3"]


class ContinuousUserInput(BaseModel):
    # Accept probabilities as input (0.0 to 1.0)
    A1: float
    A2: float
    A3: float
    A4: float
    A5: float
    UI: float
    H: float

    # Optional validation for range 0-1
    # from pydantic import validator
    # @validator('*')
    # def check_range(cls, v):
    #     if not (0.0 <= v <= 1.0):
    #         raise ValueError('Input probabilities must be between 0.0 and 1.0')
    #     return v

def call_openai_for_full_bn(input_states: Dict[str, float]) -> Dict[str, float]:
    """
    Calls OpenAI API once to estimate probabilities for all target nodes.
    **Requires EXTREMELY careful prompt engineering and robust parsing.**
    """
    if not openai.api_key:
        logger.error("OpenAI API Key not configured during call.")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # --- Complex Prompt Engineering Step ---
    # Describe inputs clearly
    input_descriptions = []
    for node, value in input_states.items():
        # Describe the probability qualitatively for the LLM
        state_desc = "High" if value >= 0.66 else ("Medium" if value >= 0.33 else "Low")
        input_descriptions.append(f"- {node}: {state_desc} (probability approx {value:.2f})")
    input_context = "\n".join(input_descriptions)

    # Describe BN structure and relationships (Needs significant refinement!)
    # Be as specific as possible about how parents influence children
    structure_description = f"""
    This Bayesian Network models user cognitive factors and actions.
    Nodes and Dependencies: {json.dumps(NODE_PARENTS, indent=2)}

    Qualitative Relationship Descriptions:
    - Confidence (IS1) is generally increased by Domain Expertise (A1), Web Literacy (A2), Task Familiarity (A3), Motivation (A5), good UI State (UI), relevant History (H), and high Knowledge Activated (IS5). High Confusion (IS3) decreases Confidence.
    - Cognitive Load (IS2) increases with lower Web Literacy (A2), lower Motivation (A5), and poorer UI State (UI).
    - Confusion (IS3) increases with lower Domain Expertise (A1), lower Web Literacy (A2), poorer UI State (UI), negative History (H), and higher Cognitive Load (IS2).
    - Current Sub-Goal (IS4) is influenced by Task Familiarity (A3), Goal (A4), and History (H).
    - Relevant Knowledge Activated (IS5) increases with Domain Expertise (A1), Task Familiarity (A3), and having a clear Current Sub-Goal (IS4).
    - Predicted Action (O1) success probability increases with higher Confidence (IS1), lower Confusion (IS3), relevant Sub-Goal (IS4), and Activated Knowledge (IS5).
    - Action Probability (O2) magnitude is mainly influenced by Confidence (IS1).
    - Reasoning/Thought (O3) quality/type is influenced by Confusion (IS3) and Activated Knowledge (IS5).

    (Note: These descriptions are examples. Refine them based on your actual intended model relationships).
    """

    # Instruction for the LLM
    system_message = """
    You are an expert probabilistic reasoner simulating a Bayesian Network based on qualitative descriptions.
    Your task is to estimate the probability of multiple target nodes being in a 'High' state (equivalent to state 1), given the initial input probabilities and the network's structure and relationships.
    Reason through the dependencies step-by-step internally to arrive at the final probabilities.
    Provide the final estimated probabilities ONLY as a single, valid JSON object mapping the target node names to their estimated P(Node=1) value (a float between 0.0 and 1.0).
    Example format: {"IS1": 0.75, "IS2": 0.3, "IS3": 0.6, "IS4": 0.9, "IS5": 0.8, "O1": 0.85, "O2": 0.7, "O3": 0.65}
    Output ONLY the JSON object and nothing else.
    """
    user_message = f"""
    Initial Input Probabilities (P=1):
    {input_context}

    Bayesian Network Structure and Qualitative Relationships:
    {structure_description}

    Estimate the probability P(Node=1) for all target nodes ({', '.join(TARGET_NODES)}) based on the provided inputs and relationships. Return the result ONLY as a JSON object mapping each target node name to its estimated probability (a float between 0.0 and 1.0).
    """

    logger.debug("Constructing single call prompt to OpenAI...")
    # logger.debug(f"System: {system_message}\nUser: {user_message}") # Uncomment for full prompt debugging

    try:
        response = openai.chat.completions.create(
            model="gpt-4o", # Or another powerful model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}, # Request JSON output format
            max_tokens=600,  # Adjust based on expected output size and complexity
            temperature=0.2, # Lower temperature for more deterministic estimation
            n=1
        )
        llm_output_raw = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI Raw Output (Single Call): {llm_output_raw}")

        # --- Robust Parsing for JSON Output ---
        try:
            estimated_probs = json.loads(llm_output_raw)
            # Validate structure and values
            validated_probs = {}
            missing_nodes = []
            for node in TARGET_NODES:
                if node in estimated_probs and isinstance(estimated_probs[node], (float, int)):
                     # Clamp result to [0, 1]
                     validated_probs[node] = max(0.0, min(1.0, float(estimated_probs[node])))
                else:
                    logger.warning(f"Node '{node}' missing or invalid value in LLM JSON output: {estimated_probs.get(node)}")
                    missing_nodes.append(node)
                    # Decide on fallback: use 0.5? Raise error?
                    validated_probs[node] = 0.5 # Fallback

            if missing_nodes:
                 logger.warning(f"LLM output was missing or invalid for nodes: {', '.join(missing_nodes)}")
                 # Optionally raise an error here if completeness is critical

            return validated_probs # Returns dict like {"IS1": 0.75, ...}

        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM output as JSON: {llm_output_raw}. Error: {json_err}")
            # Attempt fallback parsing or raise error
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON response: {json_err}")

    except openai.APIError as e:
        logger.error(f"OpenAI API returned an API Error: {e}")
        raise HTTPException(status_code=502, detail=f"OpenAI API Error: {e}")
    except openai.AuthenticationError as e:
         logger.error(f"OpenAI Authentication Error: {e}")
         raise HTTPException(status_code=401, detail=f"OpenAI Authentication Failed - Check API Key")
    except openai.RateLimitError as e:
        logger.error(f"OpenAI Rate Limit Exceeded: {e}")
        raise HTTPException(status_code=429, detail="OpenAI Rate Limit Exceeded.")
    except Exception as e:
        # Catch any other unexpected errors during the API call or processing
        logger.error(f"Error in single call OpenAI interaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing single LLM request: {e}")


# --- API Endpoint using the single-call function ---
@app.post("/predict_openai_bn_single_call")
async def predict_openai_bn_single_call(data: ContinuousUserInput):
    print("DEBUG: Entered /predict_openai_bn_single_call function.") # Check if route handler is entered
    """
    Receives input probabilities and returns all node probabilities
    estimated by a single call to the OpenAI LLM.
    """
    try:
        # Get initial inputs
        input_probs = data.dict()

        # Make the single call to get all target probabilities
        # Note: This function now directly raises HTTPException on failure
        estimated_target_probs = call_openai_for_full_bn(input_probs) # Returns {Node: P1, ...}

        # Combine inputs and estimated targets
        all_current_probabilities = {**input_probs, **estimated_target_probs}

        # Format final result with P0 and P1 for all nodes
        final_result = {}
        for node in ALL_NODES:
            if node in all_current_probabilities:
                 p1 = all_current_probabilities[node]
                 # Ensure p1 is clamped just in case (should be done in call_openai_for_full_bn)
                 p1_clamped = max(0.0, min(1.0, p1))
                 final_result[node] = {"0": 1.0 - p1_clamped, "1": p1_clamped}
            else:
                 # This case should ideally not happen if TARGET_NODES includes all non-inputs
                 logger.warning(f"Node {node} was not found in final probability dictionary.")
                 final_result[node] = {"0": 0.5, "1": 0.5} # Fallback


        logger.info("Successfully generated prediction using single LLM call.")
        return final_result

    except HTTPException as e:
        # Re-raise HTTP exceptions that occurred during the process
        raise e
    except Exception as e:
        # Catch any other unexpected errors in the endpoint logic
        logger.error(f"Error in single call endpoint logic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during single call prediction: {e}")

print("DEBUG: /predict_openai_bn_single_call route defined.")

# --- Root endpoint ---
@app.get("/")
def root():
    """ Basic endpoint to check if the API is running. """
    print("DEBUG: Entered / route.")
    return {"message": "OpenAI-Powered Bayesian Network API (Single Call) is running."}

print("DEBUG: Finished defining routes.")
