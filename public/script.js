// --- Corrected script.js ---

// --- Initialize Cytoscape (cy variable) ---
const cy = cytoscape({
    container: document.getElementById('cy'), // The HTML element to render in

    // --- Define Nodes and Edges ---
    elements: [
        // Nodes (Inputs) - Add 'label' in data for display
        { data: { id: 'A1', label: 'A1: Domain Exp' } },
        { data: { id: 'A2', label: 'A2: Web Lit' } },
        { data: { id: 'A3', label: 'A3: Task Fam' } },
        { data: { id: 'A4', label: 'A4: Goal' } },
        { data: { id: 'A5', label: 'A5: Motivation' } },
        { data: { id: 'UI', label: 'UI: UI State' } },
        { data: { id: 'H', label: 'H: History' } },

        // Nodes (Internal States)
        { data: { id: 'IS1', label: 'IS1: Confidence' } },
        { data: { id: 'IS2', label: 'IS2: Cog Load' } },
        { data: { id: 'IS3', label: 'IS3: Confusion' } },
        { data: { id: 'IS4', label: 'IS4: Sub-Goal' } },
        { data: { id: 'IS5', label: 'IS5: Knowl Act' } },

        // Nodes (Outputs)
        { data: { id: 'O1', label: 'O1: Pred Action' } },
        { data: { id: 'O2', label: 'O2: Action Prob' } },
        { data: { id: 'O3', label: 'O3: Reasoning' } },

        // Edges (Based on NODE_PARENTS from main.py)
        // Give each edge a unique ID
        { data: { id: 'a1_is1', source: 'A1', target: 'IS1' } }, { data: { id: 'a1_is3', source: 'A1', target: 'IS3' } }, { data: { id: 'a1_is5', source: 'A1', target: 'IS5' } },
        { data: { id: 'a2_is1', source: 'A2', target: 'IS1' } }, { data: { id: 'a2_is2', source: 'A2', target: 'IS2' } }, { data: { id: 'a2_is3', source: 'A2', target: 'IS3' } },
        { data: { id: 'a3_is1', source: 'A3', target: 'IS1' } }, { data: { id: 'a3_is4', source: 'A3', target: 'IS4' } }, { data: { id: 'a3_is5', source: 'A3', target: 'IS5' } },
        { data: { id: 'a4_is4', source: 'A4', target: 'IS4' } },
        { data: { id: 'a5_is1', source: 'A5', target: 'IS1' } }, { data: { id: 'a5_is2', source: 'A5', target: 'IS2' } },
        { data: { id: 'ui_is1', source: 'UI', target: 'IS1' } }, { data: { id: 'ui_is2', source: 'UI', target: 'IS2' } }, { data: { id: 'ui_is3', source: 'UI', target: 'IS3' } },
        { data: { id: 'h_is1', source: 'H', target: 'IS1' } }, { data: { id: 'h_is4', source: 'H', target: 'IS4' } }, { data: { id: 'h_is3', source: 'H', target: 'IS3' } },
        { data: { id: 'is2_is3', source: 'IS2', target: 'IS3' } },
        { data: { id: 'is3_is1', source: 'IS3', target: 'IS1' } },
        { data: { id: 'is5_is1', source: 'IS5', target: 'IS1' } },
        { data: { id: 'is4_is5', source: 'IS4', target: 'IS5' } },
        { data: { id: 'is1_o1', source: 'IS1', target: 'O1' } }, { data: { id: 'is1_o2', source: 'IS1', target: 'O2' } },
        { data: { id: 'is3_o1', source: 'IS3', target: 'O1' } }, { data: { id: 'is3_o3', source: 'IS3', target: 'O3' } },
        { data: { id: 'is4_o1', source: 'IS4', target: 'O1' } },
        { data: { id: 'is5_o1', source: 'IS5', target: 'O1' } }, { data: { id: 'is5_o3', source: 'IS5', target: 'O3' } }
    ],

    // --- Define Basic Styles ---
    style: [
        // Style for all nodes
        {
            selector: 'node',
            style: {
                'background-color': '#ccc', // Default color
                'label': 'data(label)',     // Display the label property
                'width': 90,               // Make nodes smaller circles
                'height': 90,
                'shape': 'ellipse',        // Make nodes circles
                'text-valign': 'center',    // Center text vertically
                'text-halign': 'center',    // Center text horizontally
                'font-size': '10px',        // Adjust font size
                'text-wrap': 'wrap',        // Wrap text within the node
                'text-max-width': 80        // Max width before wrapping
            }
        },
        // Style for all edges
        {
            selector: 'edge',
            style: {
                'width': 2,                     // Edge thickness
                'line-color': '#666',           // Edge color
                'target-arrow-shape': 'triangle', // Shape of the arrowhead
                'target-arrow-color': '#666',   // Arrow color
                'curve-style': 'bezier'         // How edges curve (bezier looks nice)
                 // Use 'taxi' for straight lines with right angles if preferred
                 // 'taxi-direction': 'vertical' // Control taxi direction if needed
            }
        }
        // You can add more specific styles here later if needed
    ],

    // --- Define Layout ---
    layout: {
        name: 'dagre', // Use the Dagre layout for directed graphs
        // Optional Dagre configuration:
        rankDir: 'TB', // Layout top-to-bottom (can use LR for left-to-right)
        spacingFactor: 1.2 // Adjust spacing between nodes
    }
});

// --- Function to update node appearance based on probabilities ---
function updateNodeProbabilities(probabilities) {
    cy.nodes().forEach(node => {
        const nodeId = node.id();
        if (probabilities[nodeId] && probabilities[nodeId]["1"] !== undefined) { // Check if data exists and has state "1"
            const probState1 = probabilities[nodeId]["1"]; // P(Node=1)
            const baseLabel = node.data('id'); // Get the base ID (like 'A1')
            // Update label and style (e.g., color based on probState1)
            // Using node.data('label') directly might overwrite initial pretty labels, use node.data('id') for consistency
            node.data('currentLabel', `${baseLabel}\nP(1)=${probState1.toFixed(3)}`); // Store calculated label in different data field
            node.style('label', node.data('currentLabel')); // Apply the calculated label

            // Map probability 0->1 to blue->red gradient
            const color = `rgb(${Math.round(255 * probState1)}, 0, ${Math.round(255 * (1 - probState1))})`;
            node.style('background-color', color);
        } else {
             // Apply default style if no probability data yet
             const baseLabel = node.data('id'); // Use base ID
             node.data('currentLabel', `${baseLabel}\n(N/A)`);
             node.style('label', node.data('currentLabel'));
             node.style('background-color', '#ccc'); // Default grey color
        }
    });
     // Maybe re-run layout slightly after label changes if needed?
     // cy.layout({ name: 'dagre', rankDir: 'TB', spacingFactor: 1.2 }).run();
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
    const updateButton = document.getElementById('update-button');
    updateButton.disabled = true;
    updateButton.textContent = 'Updating...';


    try {
        // Fetch from the single-call endpoint defined in api/main.py
        const response = await fetch('/predict_openai_bn_single_call', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inputData)
        });

        if (!response.ok) {
             // Try to parse error detail, default if parsing fails
             let errorDetail = 'Unknown error';
             try {
                 const errorData = await response.json();
                 errorDetail = errorData.detail || JSON.stringify(errorData);
             } catch (e) {
                 // If response wasn't JSON (like the HTML error page)
                 errorDetail = await response.text();
             }
             throw new Error(`HTTP error! status: ${response.status}, detail: ${errorDetail}`);
        }
        const allNodeProbabilities = await response.json();

        // Update Cytoscape graph
        updateNodeProbabilities(allNodeProbabilities);

    } catch (error) {
        console.error('Error fetching LLM predictions:', error);
        alert(`Error fetching predictions: ${error.message}`);
    } finally {
        // Remove loading indicator
        updateButton.disabled = false;
        updateButton.textContent = 'Update Probabilities';
    }
}

// --- Add event listener to the button ---
document.getElementById('update-button').addEventListener('click', fetchAndUpdateLLM);

// --- Initialize node appearance on page load ---
// Run layout first
cy.layout({ name: 'dagre', rankDir: 'TB', spacingFactor: 1.2 }).run();
// Then apply initial styles/labels
updateNodeProbabilities({}); // Initialize appearance with (N/A)
