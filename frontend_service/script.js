document.getElementById('searchBtn').addEventListener('click', function() {
    const queryInput = document.getElementById('queryInput');
    const modelResponsesDiv = document.getElementById('modelResponses');
    const evaluationResultPre = document.getElementById('evaluationResult');
    const query = queryInput.value;

    if (!query) return;

    queryInput.disabled = true;
    modelResponsesDiv.innerHTML = '';
    evaluationResultPre.textContent = '';

    const websocket = new WebSocket('ws://127.0.0.2:9007/api/ws/model-output'); // Adjust this URL

    websocket.onopen = () => websocket.send(query);
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        Object.keys(data).forEach(model => {
            const responseDiv = document.createElement('div');
            const modelTitle = document.createElement('h3');
            modelTitle.textContent = model;
            const modelResponse = document.createElement('p');
            modelResponse.textContent = data[model];
            responseDiv.appendChild(modelTitle);
            responseDiv.appendChild(modelResponse);
            modelResponsesDiv.appendChild(responseDiv);
        });
    };
    websocket.onclose = () => {
        queryInput.disabled = false;
        evaluateModelResponses();
    };
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        queryInput.disabled = false;
    };
});

function evaluateModelResponses() {
    // Dummy function for evaluation - replace with actual API call
    const evaluationResultPre = document.getElementById('evaluationResult');
    evaluationResultPre.textContent = 'Evaluation results will be displayed here.';
}