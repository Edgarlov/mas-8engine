"use strict";

// --- CORE STATE ---
const state = {
    isProcessing: false,
    ontologyData: null,
    currentTab: 'tab-pipeline'
};

// --- DOM ELEMENTS ---
const elements = {
    tabs: document.querySelectorAll('.nav-tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    corpusInput: document.getElementById('corpus-input'),
    btnRun: document.getElementById('btn-run-pipeline'),
    btnLoadDemo: document.getElementById('btn-load-demo'),
    steps: [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4')
    ],
    treeContainer: document.getElementById('tree-container'),
    jsonViewer: document.getElementById('json-viewer-content'),
    btnCopy: document.getElementById('btn-copy-json'),
    btnDownload: document.getElementById('btn-download-json'),
    auditList: document.getElementById('audit-list'),
    stats: {
        total: document.getElementById('stat-nodes-total'),
        atomic: document.getElementById('stat-nodes-atomic'),
        depth: document.getElementById('stat-depth'),
        mece: document.getElementById('stat-mece-violations')
    },
    toastContainer: document.getElementById('toast-container')
};

// --- MOCK DATA GENERATOR (SOTA Fallback) ---
const mockCorpus = `Arquitectura de Microservicios:
Los microservicios deben aislar estados. La persistencia se maneja vía bases de datos relacionales o NoSQL. 
La comunicación ocurre mediante mensajería asíncrona (Kafka, RabbitMQ) o síncrona (REST, gRPC).
El despliegue requiere orquestadores como Kubernetes. Monitoreo esencial: Prometheus y Grafana.`;

const generateMockOntology = () => ({
    metadata: {
        nodes_total: 12,
        nodes_atomic: 8,
        max_depth: 3,
        mece_violations: 1
    },
    tree: [
        {
            id: "root",
            label: "Microservicios",
            type: "Concepto Principal",
            children: [
                {
                    id: "persistencia",
                    label: "Persistencia",
                    type: "Subsistema",
                    children: [
                        { id: "relacional", label: "Relacional", type: "Tecnología", children: [] },
                        { id: "nosql", label: "NoSQL", type: "Tecnología", children: [] }
                    ]
                },
                {
                    id: "comunicacion",
                    label: "Comunicación",
                    type: "Subsistema",
                    children: [
                        { id: "asincrona", label: "Asíncrona (Kafka, RabbitMQ)", type: "Patrón", children: [] },
                        { id: "sincrona", label: "Síncrona (REST, gRPC)", type: "Patrón", children: [] }
                    ]
                },
                {
                    id: "infraestructura",
                    label: "Infraestructura",
                    type: "Subsistema",
                    children: [
                        { id: "orquestacion", label: "Orquestación (Kubernetes)", type: "Herramienta", children: [] },
                        { id: "monitoreo", label: "Monitoreo", type: "Subcategoría", children: [
                            { id: "prometheus", label: "Prometheus", type: "Herramienta", children: [] },
                            { id: "grafana", label: "Grafana", type: "Herramienta", children: [] }
                        ]}
                    ]
                }
            ]
        }
    ],
    audit: [
        {
            id: "MECE-001",
            severity: "medium",
            message: "Posible traslape semántico en Comunicación Síncrona vs Asíncrona (Patrones híbridos no cubiertos)."
        },
        {
            id: "MECE-002",
            severity: "low",
            message: "Cobertura de persistencia asume esquema binario; ignora bases de datos de grafos."
        }
    ]
});

// --- UI UTILS ---
const showToast = (message, type = 'info') => {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
};

const switchTab = (tabId) => {
    elements.tabs.forEach(t => t.classList.remove('active'));
    elements.tabContents.forEach(c => c.classList.remove('active'));
    const targetTab = document.querySelector(`[data-target="${tabId}"]`);
    const targetContent = document.getElementById(tabId);
    if(targetTab) targetTab.classList.add('active');
    if(targetContent) targetContent.classList.add('active');
    state.currentTab = tabId;
};

// --- RENDERERS ---
const syntaxHighlight = (json) => {
    if (typeof json != 'string') json = JSON.stringify(json, undefined, 2);
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) cls = 'json-key';
            else cls = 'json-string';
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-boolean';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
};

const renderTree = (nodes, container) => {
    if (!nodes || nodes.length === 0) return;
    nodes.forEach(node => {
        const nodeEl = document.createElement('div');
        nodeEl.className = 'tree-node';
        
        const contentEl = document.createElement('div');
        contentEl.className = 'node-content';
        
        const hasChildren = node.children && node.children.length > 0;
        const toggleEl = document.createElement('span');
        toggleEl.className = 'node-toggle';
        toggleEl.textContent = hasChildren ? '[-]' : '';
        
        const labelEl = document.createElement('span');
        labelEl.className = 'node-label';
        labelEl.textContent = node.label;
        
        const badgeEl = document.createElement('span');
        badgeEl.className = 'node-badge';
        badgeEl.textContent = node.type;

        contentEl.appendChild(toggleEl);
        contentEl.appendChild(labelEl);
        contentEl.appendChild(badgeEl);
        nodeEl.appendChild(contentEl);

        if (hasChildren) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
            renderTree(node.children, childrenContainer);
            nodeEl.appendChild(childrenContainer);

            toggleEl.addEventListener('click', () => {
                const isHidden = childrenContainer.style.display === 'none';
                childrenContainer.style.display = isHidden ? 'block' : 'none';
                toggleEl.textContent = isHidden ? '[-]' : '[+]';
            });
        }
        container.appendChild(nodeEl);
    });
};

const renderAudit = (auditLogs) => {
    elements.auditList.innerHTML = '';
    if (!auditLogs || auditLogs.length === 0) {
        elements.auditList.innerHTML = '<div class="audit-item severity-low"><strong>Óptimo.</strong> Zero violaciones MECE detectadas.</div>';
        return;
    }
    auditLogs.forEach(log => {
        const item = document.createElement('div');
        item.className = `audit-item severity-${log.severity}`;
        item.innerHTML = `<strong>[${log.id}]</strong> ${log.message}`;
        elements.auditList.appendChild(item);
    });
};

const updateDashboard = (data) => {
    elements.stats.total.textContent = data.metadata.nodes_total;
    elements.stats.atomic.textContent = data.metadata.nodes_atomic;
    elements.stats.depth.textContent = data.metadata.max_depth;
    elements.stats.mece.textContent = data.metadata.mece_violations;

    elements.treeContainer.innerHTML = '';
    renderTree(data.tree, elements.treeContainer);

    elements.jsonViewer.innerHTML = syntaxHighlight(data);
    renderAudit(data.audit);
};

// --- LOGIC ---
const delay = ms => new Promise(res => setTimeout(res, ms));

const runPipeline = async () => {
    if(state.isProcessing) return;
    const text = elements.corpusInput.value.trim();
    if(!text) { showToast("Corpus vacío. Inyecte datos.", "error"); return; }
    
    state.isProcessing = true;
    elements.btnRun.disabled = true;
    showToast("Ejecutando Pipeline SOTA...");

    // Animate steps
    for(let i=0; i<4; i++) {
        elements.steps.forEach(s => s.classList.remove('active', 'completed'));
        for(let j=0; j<i; j++) elements.steps[j].classList.add('completed');
        elements.steps[i].classList.add('active');
        await delay(600); // Mock processing time
    }
    elements.steps.forEach(s => { s.classList.remove('active'); s.classList.add('completed'); });

    // Mock API Fetch logic
    try {
        // En entorno real: await fetch('/api/process', { method: 'POST', body: JSON.stringify({ corpus: text }) });
        const result = generateMockOntology();
        state.ontologyData = result;
        updateDashboard(result);
        showToast("Procesamiento completado con éxito.");
        switchTab('tab-tree');
    } catch (e) {
        showToast("Falla sistémica en el procesamiento.", "error");
    } finally {
        state.isProcessing = false;
        elements.btnRun.disabled = false;
    }
};

// --- EVENT LISTENERS ---
elements.tabs.forEach(tab => {
    tab.addEventListener('click', (e) => switchTab(e.target.dataset.target));
});

elements.btnLoadDemo.addEventListener('click', () => {
    elements.corpusInput.value = mockCorpus;
    showToast("Corpus de demostración inyectado.");
});

elements.btnRun.addEventListener('click', runPipeline);

elements.btnCopy.addEventListener('click', () => {
    if(!state.ontologyData) return showToast("No hay datos para copiar.");
    navigator.clipboard.writeText(JSON.stringify(state.ontologyData, null, 2))
        .then(() => showToast("JSON copiado al portapapeles."))
        .catch(() => showToast("Error al copiar al portapapeles.", "error"));
});

elements.btnDownload.addEventListener('click', () => {
    if(!state.ontologyData) return showToast("No hay datos para descargar.");
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.ontologyData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "ontology_output.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    showToast("Descarga iniciada.");
});
