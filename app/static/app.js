// GardenBuddy Frontend Application Logic

let currentUserId = 1;
let currentGardenId = null;
let currentGarden = null;
let plantsList = [];
let todaysTasks = [];

document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await initializeUserAndGardens();
});

function setupEventListeners() {
  // Garden selection
  const gardenSelect = document.getElementById("gardenSelect");
  gardenSelect.addEventListener("change", async (e) => {
    currentGardenId = parseInt(e.target.value);
    if (currentGardenId) {
      await loadGardenData(currentGardenId);
    }
  });

  // Garden modals
  document.getElementById("btnNewGarden").addEventListener("click", () => openGardenDialog());
  document.getElementById("btnEditGarden").addEventListener("click", () => openGardenDialog(currentGarden));
  document.getElementById("btnCancelGarden").addEventListener("click", () => document.getElementById("gardenDialog").close());
  document.getElementById("gardenForm").addEventListener("submit", handleGardenFormSubmit);

  // Plant modals
  document.getElementById("btnAddPlant").addEventListener("click", () => openPlantDialog());
  document.getElementById("btnCancelPlant").addEventListener("click", () => document.getElementById("plantDialog").close());
  document.getElementById("plantForm").addEventListener("submit", handlePlantFormSubmit);

  // Task completion modal
  document.getElementById("btnCancelComplete").addEventListener("click", () => document.getElementById("taskCompleteDialog").close());
  document.getElementById("taskCompleteForm").addEventListener("submit", handleTaskCompleteSubmit);

  // Refresh plan button
  document.getElementById("btnRegeneratePlan").addEventListener("click", async () => {
    if (currentGardenId) {
      await generateDailyPlan(currentGardenId);
    }
  });
}

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
async function initializeUserAndGardens() {
  try {
    // 1. Fetch or create a default user
    let userRes = await fetch("/api/v1/users/");
    let users = await userRes.json();
    if (!users || users.length === 0) {
      const createRes = await fetch("/api/v1/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "gardener", email: "gardener@example.com" })
      });
      const newUser = await createRes.json();
      currentUserId = newUser.id;
    } else {
      currentUserId = users[0].id;
    }

    // 2. Load gardens for user
    await refreshGardenDropdown();
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

async function refreshGardenDropdown() {
  const gardenSelect = document.getElementById("gardenSelect");
  gardenSelect.innerHTML = "";

  const res = await fetch(`/api/v1/gardens/?user_id=${currentUserId}`);
  const gardens = await res.json();

  if (gardens.length === 0) {
    // Create an initial starter garden if none exist
    const createRes = await fetch("/api/v1/gardens/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        name: "My Home Garden",
        location: "San Francisco",
        garden_type: "Backyard",
        sunlight: "Full Sun (6+ hours)",
        notes: "Initial garden bed"
      })
    });
    const newGarden = await createRes.json();
    gardens.push(newGarden);
  }

  gardens.forEach(g => {
    const opt = document.createElement("option");
    opt.value = g.id;
    opt.textContent = `${g.name} (${g.location || 'No location'})`;
    gardenSelect.appendChild(opt);
  });

  currentGardenId = gardens[0].id;
  gardenSelect.value = currentGardenId;
  await loadGardenData(currentGardenId);
}

// -------------------------------------------------------------
// Load Garden Data (Plants & Plan)
// -------------------------------------------------------------
async function loadGardenData(gardenId) {
  try {
    // Fetch garden info
    const gRes = await fetch(`/api/v1/gardens/${gardenId}`);
    currentGarden = await gRes.json();

    document.getElementById("gardenNameDisplay").textContent = currentGarden.name;
    document.getElementById("gardenLocationDisplay").textContent = currentGarden.location || "Not specified";
    document.getElementById("gardenTypeDisplay").textContent = currentGarden.garden_type || "General";
    document.getElementById("gardenSunlightDisplay").textContent = currentGarden.sunlight || "Full Sun";

    // Load Plants
    await loadPlants(gardenId);

    // Load Plan
    await generateDailyPlan(gardenId);
  } catch (err) {
    console.error("Error loading garden data:", err);
  }
}

// -------------------------------------------------------------
// Plant Management (Phase 10.2)
// -------------------------------------------------------------
async function loadPlants(gardenId) {
  const grid = document.getElementById("plantsGrid");
  grid.innerHTML = "<div class='empty-state'>Loading plants...</div>";

  try {
    const res = await fetch(`/api/v1/plants/?garden_id=${gardenId}`);
    plantsList = await res.json();

    if (plantsList.length === 0) {
      grid.innerHTML = "<div class='empty-state'>No plants added to this garden yet. Click '+ Add Plant' to start growing! 🌱</div>";
      return;
    }

    grid.innerHTML = "";
    plantsList.forEach(plant => {
      const card = document.createElement("div");
      card.className = "plant-card";

      const plantedText = plant.date_planted ? `Planted: ${plant.date_planted}` : "Planted date not set";
      const locationText = plant.location_in_garden ? `📍 ${plant.location_in_garden}` : "";

      card.innerHTML = `
        <div>
          <div class="plant-name">${escapeHtml(plant.name)}</div>
          <div class="plant-species">${escapeHtml(plant.species || '')}</div>
          <div class="plant-details">
            <div>${plantedText}</div>
            <div>${escapeHtml(locationText)}</div>
            ${plant.notes ? `<div style="font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem;">"${escapeHtml(plant.notes)}"</div>` : ''}
          </div>
        </div>
        <div class="plant-actions">
          <button class="btn btn-secondary btn-sm" onclick="editPlant(${plant.id})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deletePlant(${plant.id})">Remove</button>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = "<div class='empty-state'>Failed to load plants.</div>";
  }
}

function openPlantDialog(plant = null) {
  const dialog = document.getElementById("plantDialog");
  const title = document.getElementById("plantDialogTitle");
  const idInput = document.getElementById("plantIdInput");
  const nameInput = document.getElementById("plantNameInput");
  const speciesInput = document.getElementById("plantSpeciesInput");
  const dateInput = document.getElementById("plantDateInput");
  const locInput = document.getElementById("plantLocationInput");
  const notesInput = document.getElementById("plantNotesInput");

  if (plant) {
    title.textContent = "Edit Plant";
    idInput.value = plant.id;
    nameInput.value = plant.name;
    speciesInput.value = plant.species || "";
    dateInput.value = plant.date_planted || "";
    locInput.value = plant.location_in_garden || "";
    notesInput.value = plant.notes || "";
  } else {
    title.textContent = "Add Plant";
    idInput.value = "";
    nameInput.value = "";
    speciesInput.value = "";
    dateInput.value = "";
    locInput.value = "";
    notesInput.value = "";
  }
  dialog.showModal();
}

window.editPlant = function(plantId) {
  const plant = plantsList.find(p => p.id === plantId);
  if (plant) {
    openPlantDialog(plant);
  }
};

window.deletePlant = async function(plantId) {
  if (confirm("Are you sure you want to remove this plant?")) {
    try {
      const res = await fetch(`/api/v1/plants/${plantId}`, { method: "DELETE" });
      if (res.ok) {
        await loadPlants(currentGardenId);
      }
    } catch (err) {
      alert("Failed to delete plant: " + err);
    }
  }
};

async function handlePlantFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById("plantIdInput").value;
  const payload = {
    name: document.getElementById("plantNameInput").value.trim(),
    species: document.getElementById("plantSpeciesInput").value.trim() || null,
    date_planted: document.getElementById("plantDateInput").value || null,
    location_in_garden: document.getElementById("plantLocationInput").value.trim() || null,
    notes: document.getElementById("plantNotesInput").value.trim() || null,
  };

  try {
    if (id) {
      await fetch(`/api/v1/plants/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } else {
      payload.garden_id = currentGardenId;
      await fetch("/api/v1/plants/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }
    document.getElementById("plantDialog").close();
    await loadPlants(currentGardenId);
  } catch (err) {
    alert("Error saving plant: " + err);
  }
}

// -------------------------------------------------------------
// Garden Management
// -------------------------------------------------------------
function openGardenDialog(garden = null) {
  const dialog = document.getElementById("gardenDialog");
  const title = document.getElementById("gardenDialogTitle");
  const idInput = document.getElementById("gardenIdInput");
  const nameInput = document.getElementById("gardenNameInput");
  const locInput = document.getElementById("gardenLocationInput");
  const typeInput = document.getElementById("gardenTypeInput");
  const sunInput = document.getElementById("gardenSunlightInput");

  if (garden) {
    title.textContent = "Edit Garden Details";
    idInput.value = garden.id;
    nameInput.value = garden.name;
    locInput.value = garden.location || "";
    typeInput.value = garden.garden_type || "Backyard";
    sunInput.value = garden.sunlight || "Full Sun (6+ hours)";
  } else {
    title.textContent = "Create New Garden";
    idInput.value = "";
    nameInput.value = "";
    locInput.value = "";
    typeInput.value = "Backyard";
    sunInput.value = "Full Sun (6+ hours)";
  }
  dialog.showModal();
}

async function handleGardenFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById("gardenIdInput").value;
  const payload = {
    name: document.getElementById("gardenNameInput").value.trim(),
    location: document.getElementById("gardenLocationInput").value.trim() || null,
    garden_type: document.getElementById("gardenTypeInput").value,
    sunlight: document.getElementById("gardenSunlightInput").value,
  };

  try {
    if (id) {
      await fetch(`/api/v1/gardens/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      document.getElementById("gardenDialog").close();
      await loadGardenData(currentGardenId);
    } else {
      payload.user_id = currentUserId;
      const res = await fetch("/api/v1/gardens/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const newG = await res.json();
      document.getElementById("gardenDialog").close();
      await refreshGardenDropdown();
    }
  } catch (err) {
    alert("Error saving garden: " + err);
  }
}

// -------------------------------------------------------------
// Daily Garden Plan & Tasks (Phase 10.3 & Phase 11)
// -------------------------------------------------------------
async function generateDailyPlan(gardenId) {
  const taskList = document.getElementById("planTaskList");
  taskList.innerHTML = "<li class='empty-state'>🌱 Consulting weather & plants to build your daily plan...</li>";

  try {
    const res = await fetch(`/api/v1/agent/plan/${gardenId}?save_tasks=true`);
    const plan = await res.json();

    document.getElementById("planDate").textContent = plan.plan_date;
    document.getElementById("weatherText").textContent = plan.weather_summary;
    document.getElementById("motivationText").textContent = plan.outdoor_motivation;
    document.getElementById("reasoningText").textContent = plan.reasoning_notes;

    // Load actual tasks from database to get accurate completion status
    const tasksRes = await fetch(`/api/v1/tasks/today?garden_id=${gardenId}`);
    todaysTasks = await tasksRes.json();

    renderTaskList(todaysTasks, plan.action_items);
  } catch (err) {
    taskList.innerHTML = "<li class='empty-state'>Failed to generate plan. Please try again.</li>";
  }
}

function renderTaskList(dbTasks, planActionItems) {
  const taskList = document.getElementById("planTaskList");
  taskList.innerHTML = "";

  if (dbTasks.length === 0 && planActionItems.length === 0) {
    taskList.innerHTML = "<li class='empty-state'>No tasks scheduled for today. Go enjoy your garden! 🌿</li>";
    return;
  }

  // Render database tasks (which sync with Phase 11 completion)
  const itemsToRender = dbTasks.length > 0 ? dbTasks : planActionItems;

  itemsToRender.forEach((task, index) => {
    const li = document.createElement("li");
    const isCompleted = Boolean(task.is_completed);
    li.className = `task-item ${isCompleted ? 'completed' : ''}`;

    const catClass = `category-${(task.category || 'care').toLowerCase()}`;
    const plantName = task.plant_name ? ` (${escapeHtml(task.plant_name)})` : '';

    li.innerHTML = `
      <input type="checkbox" class="task-checkbox" ${isCompleted ? 'checked' : ''} onchange="toggleTaskCompletion(${task.id || index}, this.checked, '${escapeHtml(task.title)}')">
      <div class="task-body">
        <div class="task-title">
          <span>${escapeHtml(task.title)}${plantName}</span>
          <span class="task-category ${catClass}">${escapeHtml(task.category || 'care')}</span>
        </div>
        <div class="task-desc">${escapeHtml(task.description || '')}</div>
        ${task.result_notes ? `<div style="font-size: 0.8rem; color: #047857; margin-top: 0.3rem;">📝 Observation: "${escapeHtml(task.result_notes)}"</div>` : ''}
      </div>
    `;
    taskList.appendChild(li);
  });
}

window.toggleTaskCompletion = function(taskId, isChecked, taskTitle) {
  if (isChecked) {
    // Open observation prompt dialog
    document.getElementById("completeTaskId").value = taskId;
    document.getElementById("completeTaskTitle").textContent = taskTitle;
    document.getElementById("taskNotesInput").value = "";
    document.getElementById("taskCompleteDialog").showModal();
  } else {
    // Uncheck task
    updateTaskStatus(taskId, false, null);
  }
};

async function handleTaskCompleteSubmit(e) {
  e.preventDefault();
  const taskId = document.getElementById("completeTaskId").value;
  const notes = document.getElementById("taskNotesInput").value.trim() || null;
  document.getElementById("taskCompleteDialog").close();
  await updateTaskStatus(taskId, true, notes);
}

async function updateTaskStatus(taskId, isCompleted, notes) {
  try {
    await fetch(`/api/v1/tasks/${taskId}/complete`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        is_completed: isCompleted,
        result_notes: notes
      })
    });
    // Refresh tasks view
    const tasksRes = await fetch(`/api/v1/tasks/today?garden_id=${currentGardenId}`);
    todaysTasks = await tasksRes.json();
    renderTaskList(todaysTasks, []);
  } catch (err) {
    console.error("Error updating task status:", err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

