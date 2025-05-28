


// src/store/formData.js
import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

const initialFormDataInternal = () => ({
    name: "My BAAS Axis",
    formation: {
        front: [],
        back: [],
        slot_count: 3,
        all_appeared_skills: [],
        initial_skills: [],
        borrow: ""
    },
    battle: {
        boss_max_health_phases: [] // Array of {name: "phase1", health: 100000}
    },
    BossHealth: {
        current_ocr_region: [549, 45, 656, 60],
        max_ocr_region: [666, 45, 775, 60],
        ocr_region: [549, 45, 775, 60],
        ocr_model_name: "en-us"
    },
    yolo_setting: {
        model: "best.onnx",
        update_interval: 100
    },
    start_state: null,
    states: {},
    actions: {},
    conditions: {}
});

export const useFormDataStore = defineStore('formData', () => {
  const formData = reactive(JSON.parse(JSON.stringify(initialFormDataInternal())))

  // Meta objects for managing UI representation of renameable keys
  const statesMeta = reactive({}) // { stateName: { newName: 'stateName' } }
  const actionsMeta = reactive({})
  const conditionsMeta = reactive({})

  // --- Helper to re-initialize meta objects after loading data ---
  function reinitializeMeta() {
    Object.keys(statesMeta).forEach(key => delete statesMeta[key]);
    Object.keys(actionsMeta).forEach(key => delete actionsMeta[key]);
    Object.keys(conditionsMeta).forEach(key => delete conditionsMeta[key]);

    Object.keys(formData.states).forEach(name => { statesMeta[name] = { newName: name }; });
    Object.keys(formData.actions).forEach(name => { actionsMeta[name] = { newName: name }; });
    Object.keys(formData.conditions).forEach(name => { conditionsMeta[name] = { newName: name, definition_str: JSON.stringify(formData.conditions[name], null, 2) || '{}'}; });
  }


  // --- Computed properties for string arrays (examples) ---
  const formation_front_str = computed({
    get: () => formData.formation.front.join(', '),
    set: (val) => { formData.formation.front = val.split(',').map(s => s.trim()).filter(s => s); }
  });
  const formation_back_str = computed({
    get: () => formData.formation.back.join(', '),
    set: (val) => { formData.formation.back = val.split(',').map(s => s.trim()).filter(s => s); }
  });
  const formation_all_appeared_skills_str = computed({
    get: () => formData.formation.all_appeared_skills.join(', '),
    set: (val) => { formData.formation.all_appeared_skills = val.split(',').map(s => s.trim()).filter(s => s); }
  });
  const formation_initial_skills_str = computed({
    get: () => (formData.formation.initial_skills || []).join(', '),
    set: (val) => { formData.formation.initial_skills = val.split(',').map(s => s.trim()).filter(s => s); }
  });
  const bosshealth_current_ocr_region_str = computed({
    get: () => formData.BossHealth.current_ocr_region.join(','),
    set: (val) => { formData.BossHealth.current_ocr_region = val.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)); }
  });
  const bosshealth_max_ocr_region_str = computed({
      get: () => formData.BossHealth.max_ocr_region.join(','),
      set: (val) => { formData.BossHealth.max_ocr_region = val.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)); }
  });
  const bosshealth_ocr_region_str = computed({
      get: () => formData.BossHealth.ocr_region.join(','),
      set: (val) => { formData.BossHealth.ocr_region = val.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)); }
  });


  // --- Computed for dropdowns ---
  const stateNames = computed(() => Object.keys(formData.states));
  const actionNames = computed(() => Object.keys(formData.actions));
  const conditionNames = computed(() => Object.keys(formData.conditions));

  // --- STATES ---
  function addState() {
    const baseName = "NewState";
    let name = baseName;
    let counter = 1;
    while (formData.states[name]) {
      name = `${baseName}${counter++}`;
    }
    formData.states[name] = { action: null, transitions: [], default_transition: null };
    statesMeta[name] = { newName: name };
    if (!formData.start_state && Object.keys(formData.states).length === 1) {
        formData.start_state = name; // Set first added state as start
    }
  }
  function removeState(name) {
    if (formData.start_state === name) formData.start_state = null;
    Object.values(formData.states).forEach(s => {
        if (s.default_transition === name) s.default_transition = null;
        s.transitions = s.transitions.filter(t => t.next !== name);
    });
    delete formData.states[name];
    delete statesMeta[name];
  }
  function updateStateName(oldName, newName) {
    newName = newName.trim();
    if (oldName === newName || !newName) {
        statesMeta[oldName].newName = oldName; return;
    }
    if (formData.states[newName]) {
        ElMessage.error(`State name "${newName}" already exists!`);
        statesMeta[oldName].newName = oldName; return;
    }
    const stateData = formData.states[oldName];
    delete formData.states[oldName];
    formData.states[newName] = stateData;

    delete statesMeta[oldName];
    statesMeta[newName] = { newName: newName };

    if (formData.start_state === oldName) formData.start_state = newName;
    Object.values(formData.states).forEach(s => {
        if (s.default_transition === oldName) s.default_transition = newName;
        s.transitions.forEach(t => { if (t.next === oldName) t.next = newName; });
    });
    ElMessage.success(`State "${oldName}" renamed to "${newName}". References updated.`);
  }
  function addTransition(stateName) {
    if (formData.states[stateName]) {
      formData.states[stateName].transitions.push({ condition: null, next: null });
    }
  }
  function removeTransition(stateName, transIndex) {
    if (formData.states[stateName]) {
      formData.states[stateName].transitions.splice(transIndex, 1);
    }
  }

  // --- ACTIONS ---
  function addAction() {
    const baseName = "NewAction";
    let name = baseName;
    let counter = 1;
    while (formData.actions[name]) {
      name = `${baseName}${counter++}`;
    }
    formData.actions[name] = [];
    actionsMeta[name] = { newName: name };
  }
  function removeAction(name) {
     Object.values(formData.states).forEach(s => {
        if (s.action === name) s.action = null;
    });
    delete formData.actions[name];
    delete actionsMeta[name];
  }
  function updateActionName(oldName, newName) {
    newName = newName.trim();
    if (oldName === newName || !newName) {
        actionsMeta[oldName].newName = oldName; return;
    }
    if (formData.actions[newName]) {
        ElMessage.error(`Action name "${newName}" already exists!`);
        actionsMeta[oldName].newName = oldName; return;
    }
    formData.actions[newName] = formData.actions[oldName];
    delete formData.actions[oldName];

    delete actionsMeta[oldName];
    actionsMeta[newName] = { newName: newName };

    Object.values(formData.states).forEach(s => {
        if (s.action === oldName) s.action = newName;
    });
    ElMessage.success(`Action "${oldName}" renamed to "${newName}". References updated.`);
  }
  function addActionStep(actionName) {
    if (formData.actions[actionName]) {
      formData.actions[actionName].push({ t: 'skill', desc: 'New step' }); // Default to skill
    }
  }
  function removeActionStep(actionName, stepIndex) {
    if (formData.actions[actionName]) {
      formData.actions[actionName].splice(stepIndex, 1);
    }
  }

  // --- CONDITIONS ---
  function addCondition() {
    const baseName = "NewCondition";
    let name = baseName;
    let counter = 1;
    while (formData.conditions[name]) {
      name = `${baseName}${counter++}`;
    }
    formData.conditions[name] = { }; // Will be parsed from definition_str
    conditionsMeta[name] = { newName: name, definition_str: '{}' };
  }
  function removeCondition(name) {
    Object.values(formData.states).forEach(s => {
        s.transitions = s.transitions.filter(t => t.condition !== name);
    });
    delete formData.conditions[name];
    delete conditionsMeta[name];
  }
  function updateConditionName(oldName, newName, newDefinitionStr) {
    newName = newName.trim();
    // Update definition first, even if name doesn't change
    try {
        formData.conditions[oldName] = JSON.parse(newDefinitionStr || '{}');
        conditionsMeta[oldName].definition_str = newDefinitionStr || '{}';
    } catch (e) {
        ElMessage.error(`Invalid JSON for condition "${oldName}": ${e.message}`);
        // Potentially revert conditionsMeta[oldName].definition_str if needed
        return; // Don't proceed with rename if definition is bad
    }

    if (oldName === newName || !newName) {
        if (newName) conditionsMeta[oldName].newName = oldName; // Keep old name if new is empty
        return;
    }

    if (formData.conditions[newName] && oldName !== newName) { // Check if newName already exists and it's not the same item
        ElMessage.error(`Condition name "${newName}" already exists!`);
        conditionsMeta[oldName].newName = oldName; // Revert UI for name
        return;
    }

    // Perform the rename
    formData.conditions[newName] = formData.conditions[oldName]; // Definition already updated above
    if (oldName !== newName) {
        delete formData.conditions[oldName];
    }


    delete conditionsMeta[oldName];
    conditionsMeta[newName] = { newName: newName, definition_str: newDefinitionStr || '{}' };


    Object.values(formData.states).forEach(s => {
        s.transitions.forEach(t => { if (t.condition === oldName) t.condition = newName; });
    });
    if (oldName !== newName) {
        ElMessage.success(`Condition "${oldName}" renamed to "${newName}". References updated.`);
    } else {
        ElMessage.success(`Condition "${oldName}" definition updated.`);
    }
  }

  // --- BATTLE PHASES ---
    function addBattlePhase() {
        formData.battle.boss_max_health_phases.push({ name: `phase${formData.battle.boss_max_health_phases.length + 1}`, health: 0 });
    }
    function removeBattlePhase(index) {
        formData.battle.boss_max_health_phases.splice(index, 1);
    }


  // --- Form Actions ---
  function resetForm() {
    Object.assign(formData, JSON.parse(JSON.stringify(initialFormDataInternal())));
    reinitializeMeta();
    ElMessage.info('Form has been reset.');
  }

  function loadExampleData() {
    resetForm(); // Start clean
    // --- PASTE YOUR WIKI EXAMPLE DATA LOADING LOGIC HERE ---
    // Adapted from your static HTML's loadExampleData
    // Ensure you call reinitializeMeta() after populating formData
    formData.name = "Special-Task-L Aris Maid Workflow";
    formData.formation = {
        front: ["Aris (Maid)", "Wakamo", "Kayoko (New Year)", "Ui"],
        back: ["Ako", "Himari"],
        initial_skills: ["Wakamo", "Ako", "Himari"],
        all_appeared_skills: ["Aris (Maid)", "Wakamo", "Kayoko (New Year)", "Ui", "Ako", "Himari"],
        borrow: "",
        slot_count: 3,
    };
    formData.battle.boss_max_health_phases = [
        { name: "phase1", health: 188796 }, { name: "phase2", health: 224756 },
        { name: "phase3", health: 260729 }, { name: "phase4", health: 287696 },
        { name: "phase5", health: 323657 }
    ];
    formData.BossHealth = {
        current_ocr_region: [549, 45, 656, 60], max_ocr_region: [666, 45, 775, 60],
        ocr_region: [549, 45, 775, 60], ocr_model_name: "en-us"
    };
    formData.yolo_setting = { model: "best.onnx", update_interval: 100 };
    formData.start_state = "自动战斗开始";
    formData.actions = {
        "释放技能1": [{ t: "skill", skill_name: "Mika", desc: "释放Mika技能" }],
        "释放技能2": [{ t: "skill", skill_name: "Ako", desc: "释放Ako技能" }],
        "重新开始": [{ t: "restart", desc: "重开战斗" }]
    };
    formData.conditions = { // Definitions will be parsed from strings in meta
        "血量 > 500w": { type: "boss_health_above", value: 5000000, timeout: 1000 },
        "血量 < 500w": { type: "boss_health_below", value: 5000000, timeout: 1000 },
        "boss血量 < 0": { type: "boss_health_below", value: 0, timeout: 1000 }
    };
    formData.states = {
        "自动战斗开始": { action: null, transitions: [], default_transition: "释放技能1" },
        "释放技能1": { action: "释放技能1", transitions: [{ condition: "血量 > 500w", next: "释放技能2" }], default_transition: "重开" },
        "释放技能2": { action: "释放技能2", transitions: [{ condition: "boss血量 < 0", next: "结束战斗" }], default_transition: "重新开始" },
        "重开": { action: "重新开始", transitions: [], default_transition: "释放技能1" },
        "结束战斗": { action: null, transitions: [], default_transition: null }
    };
    reinitializeMeta(); // Crucial after loading data
    ElMessage.success('WIKI example data loaded!');
  }

  function loadDataFromFile(data) {
    if (typeof data !== 'object' || data === null) {
      ElMessage.error('Invalid file content: Not a valid JSON object.');
      return;
    }
    Object.assign(formData, JSON.parse(JSON.stringify(initialFormDataInternal()))); // Reset first
    // Deep merge or assign specific keys carefully
    for (const key in data) {
        if (formData.hasOwnProperty(key)) {
            if (typeof formData[key] === 'object' && formData[key] !== null && !Array.isArray(formData[key])) {
                 // For objects, merge deeply to avoid losing structure for subsections not in file
                Object.assign(formData[key], data[key]);
            } else {
                formData[key] = data[key];
            }
        }
    }

    reinitializeMeta(); // Crucial after loading data
    ElMessage.success('Configuration loaded from file.');
  }

  const generatedJson = computed(() => {
    const output = JSON.parse(JSON.stringify(formData));

    // States: Use newName from meta if available, clean up
    const finalStates = {};
    for (const oldName in output.states) {
        const stateData = output.states[oldName];
        const newName = statesMeta[oldName]?.newName || oldName;
        finalStates[newName] = {
            action: stateData.action || undefined,
            transitions: (stateData.transitions || []).map(t => ({
                condition: t.condition, next: t.next
            })).filter(t => t.condition && t.next),
            default_transition: stateData.default_transition || undefined
        };
        if (!finalStates[newName].action) delete finalStates[newName].action;
        if (finalStates[newName].transitions.length === 0) delete finalStates[newName].transitions;
        if (!finalStates[newName].default_transition) delete finalStates[newName].default_transition;
    }
    output.states = finalStates;

    // Actions: Use newName from meta, clean up steps
    const finalActions = {};
    for (const oldName in output.actions) {
        const actionSteps = output.actions[oldName];
        const newName = actionsMeta[oldName]?.newName || oldName;
        finalActions[newName] = (actionSteps || []).map(step => {
            const cleanStep = {...step};
            if (cleanStep.t !== 'acc' && cleanStep.hasOwnProperty('acc')) delete cleanStep.acc;
            if (cleanStep.t !== 'auto' && cleanStep.hasOwnProperty('auto_state')) delete cleanStep.auto_state;
            if (cleanStep.t !== 'skill') {
                 if(cleanStep.hasOwnProperty('skill_name')) delete cleanStep.skill_name;
                 if(cleanStep.hasOwnProperty('target')) delete cleanStep.target;
            }
            if (!cleanStep.desc) delete cleanStep.desc;
            return cleanStep;
        });
    }
    output.actions = finalActions;

    // Conditions: Use newName from meta, definition is already parsed from definition_str in store.
    const finalConditions = {};
    for (const oldName in output.conditions) {
        const newName = conditionsMeta[oldName]?.newName || oldName;
        finalConditions[newName] = JSON.parse(conditionsMeta[oldName]?.definition_str || '{}');
    }
    output.conditions = finalConditions;


    // Battle phases
    if (output.battle && output.battle.boss_max_health_phases) {
        output.battle.boss_max_health = {};
        output.battle.boss_max_health_phases.forEach(phase => {
            if(phase.name && typeof phase.health === 'number') {
                output.battle.boss_max_health[phase.name] = phase.health;
            }
        });
        delete output.battle.boss_max_health_phases;
        if (Object.keys(output.battle.boss_max_health).length === 0) delete output.battle.boss_max_health;
        if (Object.keys(output.battle).length === 0) delete output.battle;
    } else {
       delete output.battle;
    }

    // Optional formation fields
    if (output.formation.initial_skills && output.formation.initial_skills.length === 0) delete output.formation.initial_skills;
    if (!output.formation.borrow) delete output.formation.borrow;

    return output;
  });

  const generatedJsonString = computed(() => JSON.stringify(generatedJson.value, null, 2));

  // Initialize meta on store creation
  reinitializeMeta();

  return {
    formData,
    statesMeta, actionsMeta, conditionsMeta,
    formation_front_str, formation_back_str, formation_all_appeared_skills_str, formation_initial_skills_str,
    bosshealth_current_ocr_region_str, bosshealth_max_ocr_region_str, bosshealth_ocr_region_str,
    stateNames, actionNames, conditionNames,
    addState, removeState, updateStateName, addTransition, removeTransition,
    addAction, removeAction, updateActionName, addActionStep, removeActionStep,
    addCondition, removeCondition, updateConditionName,
    addBattlePhase, removeBattlePhase,
    resetForm, loadExampleData, loadDataFromFile,
    generatedJson, generatedJsonString
  }
})