from datetime import date
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "GardenBuddy API" in data["message"]


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ==========================================
# Phase 3.1 — Garden CRUD Tests
# ==========================================

def test_garden_crud_flow(client: TestClient):
    # 1. Create a user first
    user_resp = client.post("/api/v1/users/", json={"username": "alice", "email": "alice@example.com"})
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]

    # 2. Create Garden
    garden_payload = {
        "user_id": user_id,
        "name": "Sunny Balcony Garden",
        "location": "San Francisco",
        "garden_type": "Balcony",
        "sunlight": "Full Sun",
        "notes": "Pots on the south-facing balcony"
    }
    create_resp = client.post("/api/v1/gardens/", json=garden_payload)
    assert create_resp.status_code == 201
    garden = create_resp.json()
    garden_id = garden["id"]
    assert garden["name"] == "Sunny Balcony Garden"
    assert garden["location"] == "San Francisco"

    # 3. Read Garden
    get_resp = client.get(f"/api/v1/gardens/{garden_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == garden_id

    # 4. List Gardens
    list_resp = client.get(f"/api/v1/gardens/?user_id={user_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 5. Update Garden
    update_payload = {"name": "Sunny Rooftop Garden", "sunlight": "Partial Shade"}
    update_resp = client.put(f"/api/v1/gardens/{garden_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Sunny Rooftop Garden"
    assert update_resp.json()["sunlight"] == "Partial Shade"

    # 6. Delete Garden
    del_resp = client.delete(f"/api/v1/gardens/{garden_id}")
    assert del_resp.status_code == 204

    # 7. Verify deletion
    not_found_resp = client.get(f"/api/v1/gardens/{garden_id}")
    assert not_found_resp.status_code == 404


def test_create_garden_invalid_user(client: TestClient):
    resp = client.post("/api/v1/gardens/", json={"user_id": 9999, "name": "Orphan Garden"})
    assert resp.status_code == 404


# ==========================================
# Phase 3.2 — Plant CRUD Tests
# ==========================================

def test_plant_crud_flow(client: TestClient):
    # Setup user and garden
    user_resp = client.post("/api/v1/users/", json={"username": "bob"})
    user_id = user_resp.json()["id"]
    garden_resp = client.post("/api/v1/gardens/", json={"user_id": user_id, "name": "Backyard Plot"})
    garden_id = garden_resp.json()["id"]

    # 1. Add Plant
    plant_payload = {
        "garden_id": garden_id,
        "name": "Roma Tomato",
        "species": "Solanum lycopersicum",
        "date_planted": "2026-04-15",
        "location_in_garden": "Bed 1",
        "notes": "Needs daily checking for moisture"
    }
    create_resp = client.post("/api/v1/plants/", json=plant_payload)
    assert create_resp.status_code == 201
    plant = create_resp.json()
    plant_id = plant["id"]
    assert plant["name"] == "Roma Tomato"

    # 2. Retrieve Plants
    list_resp = client.get(f"/api/v1/plants/?garden_id={garden_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Retrieve Plant by ID
    get_resp = client.get(f"/api/v1/plants/{plant_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["species"] == "Solanum lycopersicum"

    # 4. Update Plant
    update_payload = {"notes": "Flowering stage reached"}
    update_resp = client.put(f"/api/v1/plants/{plant_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["notes"] == "Flowering stage reached"

    # 5. Remove Plant
    del_resp = client.delete(f"/api/v1/plants/{plant_id}")
    assert del_resp.status_code == 204

    # 6. Verify removed
    assert client.get(f"/api/v1/plants/{plant_id}").status_code == 404


def test_add_plant_invalid_garden(client: TestClient):
    resp = client.post("/api/v1/plants/", json={"garden_id": 9999, "name": "Ghost Plant"})
    assert resp.status_code == 404


# ==========================================
# Phase 3.3 — Task APIs Tests
# ==========================================

def test_task_apis_flow(client: TestClient):
    # Setup user, garden, and plant
    user = client.post("/api/v1/users/", json={"username": "charlie"}).json()
    garden = client.post("/api/v1/gardens/", json={"user_id": user["id"], "name": "Herbal Haven"}).json()
    plant = client.post("/api/v1/plants/", json={"garden_id": garden["id"], "name": "Coriander"}).json()

    today_str = date.today().isoformat()

    # 1. Create Tasks (one for today, one for tomorrow)
    task1_payload = {
        "garden_id": garden["id"],
        "plant_id": plant["id"],
        "title": "Harvest mature coriander leaves",
        "description": "Cut stems about 1 inch above soil level",
        "category": "harvest",
        "task_date": today_str,
        "source": "ai_generated"
    }
    t1_resp = client.post("/api/v1/tasks/", json=task1_payload)
    assert t1_resp.status_code == 201
    task1 = t1_resp.json()
    assert task1["is_completed"] is False

    task2_payload = {
        "garden_id": garden["id"],
        "title": "Check soil moisture before rain",
        "category": "watering",
        "task_date": "2099-01-01",
        "source": "ai_generated"
    }
    t2_resp = client.post("/api/v1/tasks/", json=task2_payload)
    assert t2_resp.status_code == 201

    # 2. Retrieve Today's Tasks
    today_resp = client.get(f"/api/v1/tasks/today?garden_id={garden['id']}")
    assert today_resp.status_code == 200
    today_tasks = today_resp.json()
    assert len(today_tasks) == 1
    assert today_tasks[0]["title"] == "Harvest mature coriander leaves"

    # 3. Mark Task Complete & Record Relevant Observation Result
    complete_payload = {
        "is_completed": True,
        "result_notes": "Harvested a small bunch, leaves are healthy and vibrant"
    }
    complete_resp = client.patch(f"/api/v1/tasks/{task1['id']}/complete", json=complete_payload)
    assert complete_resp.status_code == 200
    completed_task = complete_resp.json()
    assert completed_task["is_completed"] is True
    assert completed_task["completed_at"] is not None
    assert completed_task["result_notes"] == "Harvested a small bunch, leaves are healthy and vibrant"

    # 4. List Tasks with filter (completed=True)
    completed_list = client.get(f"/api/v1/tasks/?garden_id={garden['id']}&is_completed=true")
    assert completed_list.status_code == 200
    assert len(completed_list.json()) == 1

    # 5. Update Task
    update_resp = client.put(f"/api/v1/tasks/{task1['id']}", json={"description": "Updated instructions"})
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated instructions"

    # 6. Delete Task
    del_resp = client.delete(f"/api/v1/tasks/{task1['id']}")
    assert del_resp.status_code == 204
    assert client.get(f"/api/v1/tasks/{task1['id']}").status_code == 404

