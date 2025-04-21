// script.js

// --- Initialize Cytoscape (cy variable) ---
// Define nodes and edges matching your BN structure
// Add styles, including styles based on probability (e.g., background-color)
// Choose a layout (e.g., dagre)
// See previous examples for structure...
const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [ /* Define Nodes and Edges Here */ ],
    style: [ /* Define Styles Here */ ],
    layout: { name: 'dagre' } // Example layout
});

// --- Function to update node appearance based on probabilities ---
function updateNodeProbabilities(probabilities) {
    cy.nodes().forEach(node => {
        const nodeId = node.id();
        if (probabilities[nodeId]) {
            const probState1 = probabilities[nodeId]["1"]; // P(Node=1)
            // Update label and style (e.g., color based on probState1)
            node.data('label', `${nodeId}\nP(1)=${probState1.toFixed(3)}`);
            const color = `rgb(${Math.round(255 * probState1)}, 0, ${Math.round(255 * (1 - probState1))})`;
            node.style('background-color', color);
        } else {
             node.style('background-color', '#ccc'); // Default if no data
             node.data('label', `${nodeId}\n(N/A)`);
        }
    });
}


// --- Function to gather inputs and fetch predictions from backend ---
async function fetchAndUpdateLLM() {
    // Get input values (ensure they are floats)
    const inputData = {
        A1: parseFloat(document.getElementById('input-A1').value) || 0.5,
        A2: parseFloat(document.getElementById('input-A2').value) || 0.5,
        A3: parseFloat(document.getElementById('input-A3').value) || 0.5,
        A4: parseFloat(document.getElementById('input-A4').value) || 0.5,
        A5: parseFloat(document.getElementById('input-A5').value) || 0.5,
        UI: parseFloat(document.getElementById('input-UI').value) || 0.5,
        H: parseFloat(document.getElementById('input-H').value) || 0.5,
    };

    // Add loading indicator maybe?
    document.getElementById('update-button').disabled = true;
    document.getElementById('update-button').textContent = 'Updating...';


    try {
        // Fetch from the single-call endpoint defined in api/main.py
        const response = await fetch('/predict_openai_bn_single_call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inputData)
        });

        if (!response.ok) {
             const errorData = await response.json();
             throw new Error(`HTTP error! status: ${response.status}, detail: ${errorData.detail || 'Unknown error'}`);
        }
        const allNodeProbabilities = await response.json();

        // Update Cytoscape graph
        updateNodeProbabilities(allNodeProbabilities);

    } catch (error) {
        console.error('Error fetching LLM predictions:', error);
        alert(`Error fetching predictions: ${error.message}`);
    } finally {
        // Remove loading indicator
        document.getElementById('update-button').disabled = false;
        document.getElementById('update-button').textContent = 'Update Probabilities';
    }
}

// --- Add event listener to the button ---
document.getElementById('update-button').addEventListener('click', fetchAndUpdateLLM);

// --- Optional: Initial fetch on page load? ---
// fetchAndUpdateLLM(); // Call once maybe with default inputs
// Or initialize nodes with default styles/labels
updateNodeProbabilities({}); // Initialize appearance
