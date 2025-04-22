# --- main.py (Single Call OpenAI GPT-4o Approach) ---
import sys
print("--- DEBUG: main.py TOP LEVEL EXECUTION ---", flush=True)
# Print Python version and path just in case
print(f"--- DEBUG: Python Version: {sys.version} ---", flush=True)
print(f"--- DEBUG: Python Path: {sys.path} ---", flush=True)

try:
    from fastapi import FastAPI, HTTPException
    print("--- DEBUG: Imported FastAPI ---", flush=True)
    app = FastAPI()
    print("--- DEBUG: FastAPI app created ---", flush=True)

    @app.get("/api/ping")
    def ping():
        print("--- DEBUG: /api/ping called ---", flush=True)
        return {"message": "pong"}

    print("--- DEBUG: Defined /api/ping ---", flush=True)

except Exception as e:
    print(f"--- DEBUG: ERROR during setup: {e} ---", flush=True)
    raise e

from pydantic import BaseModel
import os
import openai
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import json
import time

print("DEBUG: Starting main.py execution...", flush=True)
logging.info("DEBUG: Logging configured.")

# Load environment variables (for API keys)
load_dotenv()

# Set OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

print(f"DEBUG: OpenAI Key loaded: {'Yes' if openai.api_key else 'NO - MISSING!'}", flush=True)

if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not found.", flush=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Bayesian Network structure
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
ALL_NODES = list(NODE_PARENTS.keys())
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
    """
    if not openai.api_key:
        logger.error("OpenAI API Key not configured during call.")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    input_descriptions = []
    for node, value in input_states.items():
        state_desc = "High" if value >= 0.66 else ("Medium" if value >= 0.33 else "Low")
        input_descriptions.append(f"- {node}: {state_desc} (probability approx {value:.2f})")
    input_context = "\n".join(input_descriptions)

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
    """

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
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0.2,
            n=1
        )
        llm_output_raw = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI Raw Output (Single Call): {llm_output_raw}")

        try:
            estimated_probs = json.loads(llm_output_raw)
            validated_probs = {}
            missing_nodes = []
            for node in TARGET_NODES:
                if node in estimated_probs and isinstance(estimated_probs[node], (float, int)):
                    validated_probs[node] = max(0.0, min(1.0, float(estimated_probs[node])))
                else:
                    logger.warning(f"Node '{node}' missing or invalid value in LLM JSON output: {estimated_probs.get(node)}")
                    missing_nodes.append(node)
                    validated_probs[node] = 0.5

            if missing_nodes:
                logger.warning(f"LLM output was missing or invalid for nodes: {', '.join(missing_nodes)}")

            return validated_probs

        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM output as JSON: {llm_output_raw}. Error: {json_err}")
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
        logger.error(f"Error in single call OpenAI interaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing single LLM request: {e}")

@app.post("/api/predict_openai_bn_single_call")
async def predict_openai_bn_single_call(data: ContinuousUserInput):
    print("DEBUG: Entered /api/predict_openai_bn_single_call function.", flush=True)
    """
    Receives input probabilities and returns all node probabilities
    estimated by a single call to the OpenAI LLM.
    """
    try:
        input_probs = data.dict()
        estimated_target_probs = call_openai_for_full_bn(input_probs)
        all_current_probabilities = {**input_probs, **estimated_target_probs}

        final_result = {}
        for node in ALL_NODES:
            if node in all_current_probabilities:
                p1 = all_current_probabilities[node]
                p1_clamped = max(0.0, min(1.0, p1))
                final_result[node] = {"0": 1.0 - p1_clamped, "1": p1_clamped}
            else:
                logger.warning(f"Node {node} was not found in final probability dictionary.")
                final_result[node] = {"0": 0.5, "1": 0.5}

        logger.info("Successfully generated prediction using single LLM call.")
        return final_result

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in single call endpoint logic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during single call prediction: {e}")

print("DEBUG: /api/predict_openai_bn_single_call route defined.", flush=True)

@app.get("/")
def root():
    """ Basic endpoint to check if the API is running. """
    print("DEBUG: Entered / route.", flush=True)
    return {"message": "OpenAI-Powered Bayesian Network API (Single Call) is running."}

print("DEBUG: Finished defining routes.", flush=True)
