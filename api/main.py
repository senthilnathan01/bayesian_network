# --- api/main.py (Adapted for OpenAI GPT-4o) ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai # Import the OpenAI library
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import time # Optional: for potential retries
import json # For parsing potentially JSON output from LLM

# Load environment variables (for API keys)
load_dotenv()
# --- IMPORTANT: Set your OpenAI API Key as an environment variable ---
# You can set this in your Vercel project settings or a .env file locally
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Define your BN structure (nodes and parent dependencies) - same as before
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
PROCESSING_ORDER = [
    "A1", "A2", "A3", "A4", "A5", "UI", "H", "IS2", "IS4", "IS5", "IS3", "IS1", "O1", "O2", "O3"
]

ALL_NODES = ["A1", "A2", "A3", "A4", "A5", "UI", "H", "IS1", "IS2", "IS3", "IS4", "IS5", "O1", "O2", "O3"]
TARGET_NODES = ["IS1", "IS2", "IS3", "IS4", "IS5", "O1", "O2", "O3"]

class ContinuousUserInput(BaseModel):
    A1: float
    A2: float
    A3: float
    A4: float
    A5: float
    UI: float
    H: float

def call_openai_for_full_bn(input_states: Dict[str, float]) -> Dict[str, float]:
    """
    Calls OpenAI API once to estimate probabilities for all target nodes.
    **Requires EXTREMELY careful prompt engineering and robust parsing.**
    """
    if not openai.api_key:
        # ... (error handling) ...
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # --- Very Complex Prompt Engineering Step ---
    # Describe inputs
    input_descriptions = []
    for node, value in input_states.items():
        state_desc = "High" if value >= 0.66 else ("Medium" if value >= 0.33 else "Low")
        input_descriptions.append(f"- {node}: {state_desc} (probability ≈ {value:.2f})")
    input_context = "\n".join(input_descriptions)

    # Describe BN structure and relationships (Example - needs much more detail)
    structure_description = """
    This network models user cognitive states and predicts actions. Key dependencies include:
    - IS1 (Confidence) depends on inputs A1, A2, A3, A5, UI, H and internal states IS3, IS5. Higher inputs generally boost confidence, higher IS3 lowers it.
    - IS2 (Cognitive Load) depends on A2, A5, UI. Higher values increase load.
    - IS3 (Confusion) depends on A1, A2, UI, H, IS2. Higher load (IS2) increases confusion.
    - IS4 (Sub-Goal) depends on A3, A4, H.
    - IS5 (Knowledge Activated) depends on A1, A3, IS4. Higher IS4 activates knowledge.
    - O1 (Predicted Action) depends on IS1, IS3, IS4, IS5. Higher confidence (IS1) and activated knowledge (IS5) favor successful action.
    - O2 (Action Probability) depends on IS1.
    - O3 (Reasoning/Thought) depends on IS3, IS5.
    (This description needs to be much more detailed and quantitative if possible for the LLM)
    """

    system_message = """
    You are an expert probabilistic reasoner simulating a Bayesian Network.
    Given the initial input node probabilities and a description of the network structure and relationships, estimate the probability (P=1, the 'High' state probability) for each of the following target nodes: IS1, IS2, IS3, IS4, IS5, O1, O2, O3.
    Reason through the dependencies step-by-step internally.
    Provide the final estimated probabilities in a JSON format like this: {"IS1": 0.75, "IS2": 0.3, ... "O3": 0.8}.
    Output ONLY the JSON object.
    """
    user_message = f"""
    Initial Input Probabilities:
    {input_context}

    Bayesian Network Structure and Relationships:
    {structure_description}

    Estimate the probability P(Node=1) for all target nodes (IS1-IS5, O1-O3) and provide the result ONLY as a JSON object.
    """

    logger.debug(f"OpenAI Single Call Prompt: System: {system_message}, User: {user_message}")

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            # Request JSON output if the model/API supports it reliably
            response_format={"type": "json_object"},
            max_tokens=500, # Needs more tokens for complex reasoning and JSON output
            temperature=0.2,
            n=1
        )
        llm_output_raw = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI Raw Output (Single Call): {llm_output_raw}")

        # --- Robust Parsing for JSON Output ---
        try:
            # Attempt to parse the entire output as JSON
            estimated_probs = json.loads(llm_output_raw)

            # Validate the structure and values (ensure all target nodes are present, values are 0-1)
            validated_probs = {}
            for node in TARGET_NODES:
                if node in estimated_probs and isinstance(estimated_probs[node], (float, int)):
                     validated_probs[node] = max(0.0, min(1.0, float(estimated_probs[node])))
                else:
                    logger.warning(f"Node '{node}' missing or invalid value in LLM JSON output.")
                    validated_probs[node] = 0.5 # Fallback or raise error

            return validated_probs # Returns dict like {"IS1": 0.75, ...}

        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM output as JSON: {llm_output_raw}")
            # Attempt fallback parsing if needed, or return error/default
            # Might need regex to find numbers if JSON fails completely
            raise HTTPException(status_code=500, detail="Failed to parse LLM JSON response.")

    # ... (Error handling for API calls - Authentication, RateLimit, etc.) ...
    except Exception as e:
         logger.error(f"Error in single call OpenAI interaction: {e}")
         raise HTTPException(status_code=500, detail=f"Error processing single LLM request.")


@app.post("/predict_openai_bn_single_call")
async def predict_openai_bn_single_call(data: ContinuousUserInput):
    try:
        # Get initial inputs
        input_probs = data.dict()

        # Make the single call to get all target probabilities
        estimated_target_probs = call_openai_for_full_bn(input_probs) # Returns {Node: P1, ...}

        # Combine inputs and estimated targets
        all_current_probabilities = {**input_probs, **estimated_target_probs}

        # Format final result with P0 and P1
        final_result = {}
        for node, p1 in all_current_probabilities.items():
            if node in ALL_NODES: # Ensure we only include nodes from our defined BN
                final_result[node] = {"0": 1.0 - p1, "1": p1}

        return final_result

    except HTTPException as e:
        raise e # Re-raise HTTP exceptions from the LLM call
    except Exception as e:
        logger.error(f"Error in single call endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during single call prediction.")

@app.get("/")
def root():
    return {"message": "OpenAI-Powered Bayesian Network API"}
