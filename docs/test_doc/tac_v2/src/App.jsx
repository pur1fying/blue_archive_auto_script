import React, { useState, useCallback, useMemo, memo } from 'react';
import {
    ReactFlow,
    addEdge,
    applyNodeChanges,
    applyEdgeChanges,
    Controls,
    Background,
    Handle,
    Position,
} from '@xyflow/react';

import '@xyflow/react/dist/style.css';

// --- STYLES ---
// Using a component to inject global styles for better organization
const GlobalStyles = () => (
    <style>{`
        :root {
            --color-bg: #222;
            --color-node-bg: #333;
            --color-node-border: #555;
            --color-node-border-selected: #00ff00;
            --color-handle: #00aaff;
            --color-handle-default: #ffaa00;
            --color-text: #eee;
            --color-text-dim: #999;
            --color-input-bg: #111;
            --color-button-primary: #00aa00;
            --color-button-danger: #aa0000;
            --color-button-secondary: #444;
        }
        .baas-flow-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            background-color: var(--color-bg);
            color: var(--color-text);
            font-family: sans-serif;
        }
        .reactflow-wrapper {
            flex-grow: 1;
            height: 100%;
            position: relative;
        }
        .side-panel {
            width: 350px;
            background-color: #2a2a2a;
            padding: 15px;
            box-sizing: border-box;
            overflow-y: auto;
            height: 100%;
            border-left: 2px solid var(--color-node-border);
        }
        .panel-section {
            background-color: var(--color-node-bg);
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 15px;
        }
        .panel-section h3 {
            margin-top: 0;
            border-bottom: 1px solid var(--color-node-border);
            padding-bottom: 5px;
        }
        .top-bar {
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 10;
            display: flex;
            gap: 10px;
        }
        button {
            background-color: var(--color-button-primary);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: filter 0.2s;
        }
        button.secondary { background-color: var(--color-button-secondary); }
        button.danger { background-color: var(--color-button-danger); }
        button:hover { filter: brightness(1.2); }
        
        .react-flow__node-custom {
            background: var(--color-node-bg);
            border: 1px solid var(--color-node-border);
            color: var(--color-text);
            border-radius: 5px;
            padding: 0;
            font-size: 12px;
        }
        .react-flow__node-custom.selected {
            border-color: var(--color-node-border-selected);
        }
        .custom-node-header {
            background: #444;
            padding: 5px 10px;
            font-weight: bold;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        .custom-node-content {
            padding: 10px;
        }
        .form-group { margin-bottom: 10px; }
        .form-group label {
            display: block;
            margin-bottom: 4px;
            color: var(--color-text-dim);
        }
        input, select, textarea {
            width: 100%;
            background-color: var(--color-input-bg);
            color: var(--color-text);
            border: 1px solid var(--color-node-border);
            border-radius: 3px;
            padding: 5px;
            box-sizing: border-box;
        }
        textarea { resize: vertical; min-height: 80px; }
        .react-flow__handle {
            width: 10px; height: 10px;
            background-color: var(--color-handle);
        }
        .react-flow__handle.default { background-color: var(--color-handle-default); }
        .transition-item {
            position: relative;
            padding-right: 20px;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .transition-item select { flex-grow: 1; }
        .list-item {
            border: 1px solid #444;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 8px;
            background-color: #2c2c2c;
        }
        .list-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
    `}</style>
);

// --- CUSTOM NODES ---

const StateNode = memo(({ id, data }) => {
    // Callbacks to update the central state in App component
    const onNameChange = useCallback((evt) => data.onUpdate(id, { ...data, name: evt.target.value }), [id, data]);
    const onActionChange = useCallback((evt) => data.onUpdate(id, { ...data, action: evt.target.value }), [id, data]);
    const onConditionChange = useCallback((index, newCondition) => {
        const newTransitions = [...data.transitions];
        newTransitions[index] = { ...newTransitions[index], condition: newCondition };
        data.onUpdate(id, { ...data, transitions: newTransitions });
    }, [id, data]);
    const addTransition = useCallback(() => data.onUpdate(id, { ...data, transitions: [...data.transitions, { condition: '' }] }), [id, data]);
    const removeTransition = useCallback((index) => {
        data.onEdgeRemove(id, `trans-${index}`); // Important: remove connected edge first
        const newTransitions = data.transitions.filter((_, i) => i !== index);
        data.onUpdate(id, { ...data, transitions: newTransitions });
    }, [id, data]);

    return (
        <div className="react-flow__node-custom" style={{ width: 250 }}>
            <Handle type="target" position={Position.Left} />
            <div className="custom-node-header">State</div>
            <div className="custom-node-content">
                <div className="form-group">
                    <label>State Name</label>
                    <input value={data.name} onChange={onNameChange} placeholder="Enter state name" />
                </div>
                <div className="form-group">
                    <label>Action</label>
                    <select value={data.action || ''} onChange={onActionChange}>
                        <option value="">(None)</option>
                        {data.actionNames.map(name => <option key={name} value={name}>{name}</option>)}
                    </select>
                </div>
                <hr style={{ borderColor: '#555' }} />
                <div className="form-group">
                    <label>Transitions (Conditional)</label>
                    {data.transitions.map((trans, index) => (
                        <div key={index} className="transition-item">
                            <select value={trans.condition} onChange={(e) => onConditionChange(index, e.target.value)}>
                                <option value="">Select Condition</option>
                                {data.conditionNames.map(name => <option key={name} value={name}>{name}</option>)}
                            </select>
                            <button className="danger" style={{ padding: '2px 5px' }} onClick={() => removeTransition(index)}>X</button>
                            <Handle type="source" position={Position.Right} id={`trans-${index}`} style={{ top: 18 + index * 38, right: -15, position: 'absolute' }} />
                        </div>
                    ))}
                    <button className="secondary" onClick={addTransition} style={{ width: '100%', marginTop: '5px' }}>+ Add Transition</button>
                </div>
                <hr style={{ borderColor: '#555' }} />
                <div className="form-group">
                    <label>Default Transition</label>
                    <div style={{ position: 'relative', padding: '5px', background: '#222', borderRadius: '3px', textAlign: 'center' }}>
                        <span style={{ color: 'var(--color-text-dim)' }}>Connect From Here</span>
                        <Handle type="source" position={Position.Right} id="default_transition" className="default" />
                    </div>
                </div>
            </div>
        </div>
    );
});

const ConfigNode = memo(({ id, data }) => {
    const { config } = data;
    const handleConfigChange = (section, key, value) => {
        const newConfig = { ...config };
        if (section) {
            newConfig[section] = { ...newConfig[section], [key]: value };
        } else {
            newConfig[key] = value; // For root properties like 'name'
        }
        data.onUpdate(id, { ...data, config: newConfig });
    };
    const handleArrayChange = (section, key, value) => handleConfigChange(section, key, value.split(',').map(s => s.trim()).filter(Boolean));

    return (
        <div className="react-flow__node-custom" style={{ width: 400 }}>
            <div className="custom-node-header">Global Configuration</div>
            <div className="custom-node-content" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                <div className="panel-section">
                    <h3>General Info</h3>
                    <div className="form-group"><label>Axis Name (name)</label><input value={config.name} onChange={e => handleConfigChange(null, 'name', e.target.value)} /></div>
                    <div className="form-group"><label>Start State</label>
                        <select value={config.start_state || ''} onChange={e => handleConfigChange(null, 'start_state', e.target.value)}>
                            <option value="">Select Start State</option>{data.stateNames.map(name => <option key={name} value={name}>{name}</option>)}
                        </select>
                    </div>
                </div>
                <div className="panel-section">
                    <h3>Formation</h3>
                    <div className="form-group"><label>Front (comma-separated)</label><input value={config.formation.front.join(', ')} onChange={e => handleArrayChange('formation', 'front', e.target.value)} /></div>
                    <div className="form-group"><label>Back (comma-separated)</label><input value={config.formation.back.join(', ')} onChange={e => handleArrayChange('formation', 'back', e.target.value)} /></div>
                </div>
            </div>
        </div>
    );
});


// --- UI PANELS ---

const SidePanel = ({ actions, setActions, conditions, setConditions }) => {
    // Action Handlers
    const addAction = () => setActions({ ...actions, [`Action${Object.keys(actions).length + 1}`]: [] });
    const removeAction = name => { const newActions = { ...actions }; delete newActions[name]; setActions(newActions); };
    const addActionStep = actionName => setActions({ ...actions, [actionName]: [...actions[actionName], { t: 'skill', desc: 'New Step' }] });

    // Condition Handlers
    const addCondition = () => setConditions({ ...conditions, [`Condition${Object.keys(conditions).length + 1}`]: '{ "type": "..." }' });
    const removeCondition = name => { const newConditions = { ...conditions }; delete newConditions[name]; setConditions(newConditions); };
    const updateCondition = (name, newDef) => setConditions({ ...conditions, [name]: newDef });

    return (
        <div className="side-panel">
            <h2>Definitions</h2>
            <div className="panel-section">
                <h3>Actions</h3>
                {Object.entries(actions).map(([name, steps]) => (
                    <div key={name} className="list-item">
                        <div className="list-item-header"><strong>{name}</strong><button className="danger" onClick={() => removeAction(name)}>X</button></div>
                        {steps.map((step, index) => <div key={index} style={{ fontSize: '10px' }}>{step.t}: {step.skill_name || '...'}</div>)}
                        <button className="secondary" onClick={() => addActionStep(name)} style={{ width: '100%', marginTop: '8px' }}>+ Add Step</button>
                    </div>
                ))}
                <button onClick={addAction} style={{ width: '100%' }}>+ Add Action</button>
            </div>
            <div className="panel-section">
                <h3>Conditions</h3>
                {Object.entries(conditions).map(([name, definition]) => (
                    <div key={name} className="list-item">
                        <div className="list-item-header"><strong>{name}</strong><button className="danger" onClick={() => removeCondition(name)}>X</button></div>
                        <textarea value={definition} onChange={e => updateCondition(name, e.target.value)} />
                    </div>
                ))}
                <button onClick={addCondition} style={{ width: '100%' }}>+ Add Condition</button>
            </div>
        </div>
    );
};

const TopBar = ({ generateJson, addStateNode, loadExample, resetForm }) => (
    <div className="top-bar">
        <button onClick={generateJson}>Generate & Copy JSON</button>
        <button onClick={addStateNode} className="secondary">+ Add State</button>
        <button onClick={loadExample} className="secondary">Load Example</button>
        <button onClick={resetForm} className="danger">Reset</button>
    </div>
);


// --- INITIAL DATA & HELPERS ---

const getInitialData = () => ({
    nodes: [
        { id: 'config', type: 'configNode', position: { x: 50, y: 50 }, data: { config: { name: "New BAAS Flow", start_state: null, formation: { front: [], back: [] } } } },
        { id: 'state-1', type: 'stateNode', position: { x: 550, y: 100 }, data: { name: 'StartState', action: null, transitions: [] } }
    ],
    edges: [],
    actions: { "ExampleAction": [{ t: "skill", skill_name: "Mika" }] },
    conditions: { "ExampleCondition": '{ "type": "boss_health_below", "value": 1000000 }' },
});

const getWikiExampleData = () => ({
    nodes: [
        { id: 'config', type: 'configNode', position: { x: 50, y: 50 }, data: { config: { name: "Special-Task-L Aris Maid", start_state: "自动战斗开始", formation: { front: ["Aris (Maid)", "Wakamo"], back: ["Ako", "Himari"] } } } },
        { id: 's1', type: 'stateNode', position: { x: 500, y: 50 }, data: { name: '自动战斗开始', action: null, transitions: [] } },
        { id: 's2', type: 'stateNode', position: { x: 800, y: 200 }, data: { name: '释放技能1', action: '释放技能1', transitions: [{ condition: '血量 > 500w' }] } },
        { id: 's3', type: 'stateNode', position: { x: 1100, y: 200 }, data: { name: '释放技能2', action: '释放技能2', transitions: [{ condition: 'boss血量 < 0' }] } },
        { id: 's4', type: 'stateNode', position: { x: 800, y: 400 }, data: { name: '重开', action: '重新开始', transitions: [] } },
        { id: 's5', type: 'stateNode', position: { x: 1400, y: 200 }, data: { name: '结束战斗', action: null, transitions: [] } },
    ],
    edges: [
        { id: 'e-s1-s2', source: 's1', target: 's2', sourceHandle: 'default_transition', type: 'smoothstep' },
        { id: 'e-s2-s3', source: 's2', target: 's3', sourceHandle: 'trans-0', type: 'smoothstep' },
        { id: 'e-s2-s4', source: 's2', target: 's4', sourceHandle: 'default_transition', type: 'smoothstep' },
        { id: 'e-s3-s5', source: 's3', target: 's5', sourceHandle: 'trans-0', type: 'smoothstep' },
    ],
    actions: { "释放技能1": [{ t: "skill", skill_name: "Mika" }], "释放技能2": [{ t: "skill", skill_name: "Ako" }], "重新开始": [{ t: "restart" }] },
    conditions: { "血量 > 500w": '{ "type": "boss_health_above", "value": 5000000 }', "boss血量 < 0": '{ "type": "boss_health_below", "value": 0 }' }
});


// --- MAIN APP COMPONENT ---

export default function App() {
    const [nodes, setNodes] = useState(getInitialData().nodes);
    const [edges, setEdges] = useState(getInitialData().edges);
    const [actions, setActions] = useState(getInitialData().actions);
    const [conditions, setConditions] = useState(getInitialData().conditions);

    const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
    const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
    const onConnect = useCallback((connection) => setEdges((eds) => addEdge({ ...connection, type: 'smoothstep' }, eds)), []);

    // Memoized values to pass down to nodes, preventing unnecessary re-renders
    const actionNames = useMemo(() => Object.keys(actions), [actions]);
    const conditionNames = useMemo(() => Object.keys(conditions), [conditions]);
    const stateNames = useMemo(() => nodes.filter(n => n.type === 'stateNode').map(n => n.data.name), [nodes]);

    // Callbacks for nodes to update global state
    const updateNodeData = useCallback((nodeId, newData) => setNodes(nds => nds.map(node => node.id === nodeId ? { ...node, data: newData } : node)), []);
    const removeEdgeBySource = useCallback((nodeId, handleId) => setEdges(eds => eds.filter(edge => !(edge.source === nodeId && edge.sourceHandle === handleId))), []);

    // This is the magic: we inject the latest callbacks and data into nodes before rendering
    const nodesWithInjectedData = useMemo(() => {
        return nodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                // Inject data needed by all or specific nodes
                actionNames,
                conditionNames,
                stateNames,
                // Inject callbacks
                onUpdate: updateNodeData,
                onEdgeRemove: removeEdgeBySource,
            }
        }));
    }, [nodes, actionNames, conditionNames, stateNames, updateNodeData, removeEdgeBySource]);

    const nodeTypes = useMemo(() => ({ stateNode: StateNode, configNode: ConfigNode }), []);

    // --- Business Logic ---
    const addStateNode = () => {
        const newNode = {
            id: `state-${nodes.length + 1}`, type: 'stateNode',
            position: { x: Math.random() * 400 + 500, y: Math.random() * 400 },
            data: { name: `State${stateNames.length + 1}`, action: null, transitions: [] }
        };
        setNodes(nds => [...nds, newNode]);
    };

    const loadExample = () => {
        if (!window.confirm('This will replace your current workflow. Are you sure?')) return;
        const data = getWikiExampleData();
        setNodes(data.nodes); setEdges(data.edges); setActions(data.actions); setConditions(data.conditions);
    };

    const resetForm = () => {
        if (!window.confirm('This will clear the entire workflow. Are you sure?')) return;
        const data = getInitialData();
        setNodes(data.nodes); setEdges(data.edges); setActions(data.actions); setConditions(data.conditions);
    };

    const generateJson = useCallback(() => {
        const configNode = nodes.find(n => n.type === 'configNode');
        if (!configNode) { alert('Error: Config Node not found!'); return; }
        
        const output = { ...configNode.data.config };
        output.actions = actions;
        output.conditions = Object.entries(conditions).reduce((acc, [name, defStr]) => {
            try { acc[name] = JSON.parse(defStr); } catch (e) { acc[name] = { error: "Invalid JSON" }; }
            return acc;
        }, {});

        const stateNodes = nodes.filter(n => n.type === 'stateNode');
        const nodeMap = new Map(stateNodes.map(n => [n.id, n]));
        output.states = {};
        
        stateNodes.forEach(node => {
            const stateData = { action: node.data.action || undefined, transitions: [] };
            edges.filter(e => e.source === node.id).forEach(edge => {
                const targetNode = nodeMap.get(edge.target);
                if (!targetNode) return;
                if (edge.sourceHandle === 'default_transition') {
                    stateData.default_transition = targetNode.data.name;
                } else if (edge.sourceHandle?.startsWith('trans-')) {
                    const transIndex = parseInt(edge.sourceHandle.split('-')[1]);
                    const condition = node.data.transitions[transIndex]?.condition;
                    if (condition) stateData.transitions.push({ condition, next: targetNode.data.name });
                }
            });
            if (stateData.transitions.length === 0) delete stateData.transitions;
            output.states[node.data.name] = stateData;
        });
        
        const jsonString = JSON.stringify(output, null, 2);
        navigator.clipboard.writeText(jsonString)
            .then(() => alert('JSON copied to clipboard!'))
            .catch(err => { console.error('Failed to copy JSON:', err); alert('Failed to copy JSON.'); });
        console.log(jsonString);

    }, [nodes, edges, actions, conditions]);

    return (
        <>
            <GlobalStyles />
            <div className="baas-flow-container">
                <div className="reactflow-wrapper">
                    <TopBar generateJson={generateJson} addStateNode={addStateNode} loadExample={loadExample} resetForm={resetForm} />
                    <ReactFlow
                        nodes={nodesWithInjectedData}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        nodeTypes={nodeTypes}
                        fitView
                    >
                        <Controls />
                        <Background />
                    </ReactFlow>
                </div>
                <SidePanel actions={actions} setActions={setActions} conditions={conditions} setConditions={setConditions} />
            </div>
        </>
    );
}