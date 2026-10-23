from flask import Flask, jsonify, request, render_template
import sqlite3
import time
import random
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "game.db"
app = Flask(__name__)

RESOURCES = {
    "wood": {"name": "Madeira", "icon": "🪵"},
    "stone": {"name": "Pedra", "icon": "🪨"},
    "ore": {"name": "Minério de ferro", "icon": "⛏️"},
    "food": {"name": "Alimentos", "icon": "🍲"},
    "leather": {"name": "Couro", "icon": "🦬"},
    "herbs": {"name": "Ervas", "icon": "🌿"},
    "plank": {"name": "Tábuas", "icon": "🪚"},
    "iron": {"name": "Barras de ferro", "icon": "🔩"},
}

BUILDINGS = {
    "sawmill": {"name": "Serraria", "description": "Transforma madeira em tábuas.", "cost": {"wood": 25, "stone": 8}, "duration": 120, "recipe": {"wood": 5}, "output": {"plank": 10}},
    "furnace": {"name": "Forno de fundição", "description": "Funde minério em barras de ferro.", "cost": {"wood": 20, "stone": 20}, "duration": 300, "recipe": {"ore": 3, "wood": 4}, "output": {"iron": 2}},
}

PROFESSIONS = {
    "lumberjack": {
        "name": "Lenhador", "resources": ["wood"],
        "specialist_name": "Borin Machado-de-Carvalho", "specialty": "Mestre lenhador",
        "skill": "Corte preciso", "speed_bonus": 30, "quality_bonus": 18,
        "description": "Encontra árvores melhores e prepara a madeira com menos desperdício.",
        "hire_cost": {"wood": 150, "food": 75}, "portrait": "🪓", "portrait_image": "/static/portraits/lumberjack.png",
    },
    "miner": {
        "name": "Minerador", "resources": ["stone", "ore"],
        "specialist_name": "Dagna Pedra-Funda", "specialty": "Mestra mineradora",
        "skill": "Olho para veios", "speed_bonus": 26, "quality_bonus": 22,
        "description": "Localiza veios promissores e extrai pedra e minério de melhor qualidade.",
        "hire_cost": {"stone": 120, "ore": 40, "food": 75}, "portrait": "⛏️", "portrait_image": "/static/portraits/miner.png",
    },
    "herbalist": {
        "name": "Líria Folha-Prateada", "resources": ["herbs"],
        "specialist_name": "Líria Folha-Prateada", "specialty": "Mestra herbalista",
        "skill": "Colheita cuidadosa", "speed_bonus": 22, "quality_bonus": 28,
        "description": "Reconhece plantas raras e colhe ervas sem danificar suas propriedades.",
        "hire_cost": {"herbs": 80, "food": 100, "wood": 50}, "portrait": "🌿", "portrait_image": "/static/portraits/herbalist.png",
    },
    "forager": {
        "name": "Coletor de alimentos", "resources": ["food"],
        "specialist_name": "Tomas Campo-Verde", "specialty": "Batedor de provisões",
        "skill": "Busca eficiente", "speed_bonus": 26, "quality_bonus": 22,
        "description": "Encontra alimentos mais frescos e identifica locais ricos em provisões.",
        "hire_cost": {"food": 150, "herbs": 30, "wood": 50}, "portrait": "🍎", "portrait_image": "/static/portraits/forager.png",
    },
}

GATHER_CATALOG = {
    "wood": {"name": "Madeira", "icon": "🪵", "profession": "lumberjack", "tiers": {
        "common": {"name": "Comum", "amount": 100, "duration": 120, "quality": 25, "required_level": 1},
        "fine": {"name": "Selecionada", "amount": 100, "duration": 150, "quality": 40, "required_level": 5},
        "rare": {"name": "Rara", "amount": 100, "duration": 180, "quality": 55, "required_level": 10}}},
    "stone": {"name": "Pedra", "icon": "🪨", "profession": "miner", "tiers": {
        "common": {"name": "Comum", "amount": 60, "duration": 180, "quality": 25, "required_level": 1},
        "fine": {"name": "Selecionada", "amount": 60, "duration": 240, "quality": 40, "required_level": 5},
        "rare": {"name": "Rara", "amount": 60, "duration": 300, "quality": 55, "required_level": 10}}},
    "ore": {"name": "Minério de ferro", "icon": "⛏️", "profession": "miner", "tiers": {
        "common": {"name": "Comum", "amount": 25, "duration": 300, "quality": 25, "required_level": 1},
        "fine": {"name": "Selecionado", "amount": 25, "duration": 420, "quality": 40, "required_level": 5},
        "rare": {"name": "Raro", "amount": 25, "duration": 540, "quality": 55, "required_level": 10}}},
    "herbs": {"name": "Ervas", "icon": "🌿", "profession": "herbalist", "tiers": {
        "common": {"name": "Comuns", "amount": 30, "duration": 120, "quality": 25, "required_level": 1},
        "fine": {"name": "Selecionadas", "amount": 30, "duration": 180, "quality": 40, "required_level": 5},
        "rare": {"name": "Raras", "amount": 30, "duration": 240, "quality": 55, "required_level": 10}}},
    "food": {"name": "Alimentos", "icon": "🍲", "profession": "forager", "tiers": {
        "common": {"name": "Comuns", "amount": 40, "duration": 90, "quality": 25, "required_level": 1},
        "fine": {"name": "Selecionados", "amount": 40, "duration": 120, "quality": 40, "required_level": 5},
        "rare": {"name": "Raros", "amount": 40, "duration": 180, "quality": 55, "required_level": 10}}},
}

HUNT_AREAS = {
    "grove": {"name": "Bosque próximo", "danger": 1, "duration": 180, "description": "Animais pequenos e recursos comuns.", "required_level": 1, "rewards": {"food": (4, 9), "leather": (1, 3), "herbs": (1, 4)}},
    "deep_forest": {"name": "Floresta profunda", "danger": 3, "duration": 600, "description": "Caça mais perigosa, com couro de melhor qualidade.", "required_level": 3, "rewards": {"food": (8, 15), "leather": (2, 5), "herbs": (2, 5)}},
    "highlands": {"name": "Terras altas", "danger": 5, "duration": 1200, "description": "Uma região difícil com possibilidade de encontrar minério.", "required_level": 5, "rewards": {"food": (10, 18), "leather": (3, 6), "ore": (1, 4)}},
}

# O custo de contratação aumenta conforme a quantidade de trabalhadores da profissão.
HIRE_BASE_COST = {"wood": 50, "food": 25}
SPECIALIST_LEVELS = {
    1: {"name": "Básico", "multiplier": 1, "cost_multiplier": 1, "chance": 45},
    2: {"name": "Intermediário", "multiplier": 2, "cost_multiplier": 4, "chance": 30},
    3: {"name": "Avançado", "multiplier": 3, "cost_multiplier": 16, "chance": 18},
    4: {"name": "Expert", "multiplier": 4, "cost_multiplier": 64, "chance": 7},
}
TAVERN_ROTATION_SECONDS = 30 * 60


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_columns(db, table):
    return {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS world_state (id INTEGER PRIMARY KEY CHECK (id=1), world_name TEXT NOT NULL, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS resources (key TEXT PRIMARY KEY, quantity INTEGER NOT NULL DEFAULT 0, quality REAL NOT NULL DEFAULT 25);
        CREATE TABLE IF NOT EXISTS buildings (key TEXT PRIMARY KEY, quantity INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS gather_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, resource_key TEXT NOT NULL, tier_key TEXT NOT NULL, amount INTEGER NOT NULL, quality REAL NOT NULL, start_at REAL NOT NULL DEFAULT 0, finish_at REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'running');
        CREATE TABLE IF NOT EXISTS production_jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, building_key TEXT NOT NULL, start_at REAL NOT NULL, finish_at REAL NOT NULL, status TEXT NOT NULL DEFAULT 'running');
        CREATE TABLE IF NOT EXISTS character_state (id INTEGER PRIMARY KEY CHECK (id=1), hunting_level INTEGER NOT NULL DEFAULT 1, crafting_level INTEGER NOT NULL DEFAULT 1, xp INTEGER NOT NULL DEFAULT 0, recovery_until REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS expeditions (id INTEGER PRIMARY KEY AUTOINCREMENT, area_key TEXT NOT NULL, start_at REAL NOT NULL, finish_at REAL NOT NULL, status TEXT NOT NULL DEFAULT 'running', result_json TEXT);
        CREATE TABLE IF NOT EXISTS event_log (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at REAL NOT NULL, message TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS profession_state (profession_key TEXT PRIMARY KEY, xp INTEGER NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS profession_workers (profession_key TEXT PRIMARY KEY, workers INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS profession_specialists (profession_key TEXT PRIMARY KEY, hired_at REAL NOT NULL);
        """)

        # Migração segura: guarda o nível e os bônus do especialista já contratado.
        specialist_cols = table_columns(db, "profession_specialists")
        for column, definition in (("level", "INTEGER NOT NULL DEFAULT 1"), ("speed_bonus", "INTEGER NOT NULL DEFAULT 0"), ("quality_bonus", "INTEGER NOT NULL DEFAULT 0"), ("specialist_name", "TEXT NOT NULL DEFAULT ''"), ("skill", "TEXT NOT NULL DEFAULT ''")):
            if column not in specialist_cols:
                db.execute(f"ALTER TABLE profession_specialists ADD COLUMN {column} {definition}")
        for key, spec in PROFESSIONS.items():
            # Recalcula os bônus dos contratados existentes com a nova escala, sem apagar o progresso.
            existing = db.execute("SELECT level FROM profession_specialists WHERE profession_key=?", (key,)).fetchone()
            if existing:
                level = max(1, min(4, int(existing["level"] or 1)))
                mult = SPECIALIST_LEVELS[level]["multiplier"]
                db.execute("UPDATE profession_specialists SET speed_bonus=?, quality_bonus=?, specialist_name=CASE WHEN specialist_name='' THEN ? ELSE specialist_name END, skill=CASE WHEN skill='' THEN ? ELSE skill END WHERE profession_key=?", (min(70, spec["speed_bonus"] * mult), min(60, spec["quality_bonus"] * mult), spec["specialist_name"], spec["skill"], key))

        # Migração segura para bancos antigos: adiciona apenas a coluna ausente.
        gather_cols = table_columns(db, "gather_jobs")
        if "status" not in gather_cols:
            db.execute("ALTER TABLE gather_jobs ADD COLUMN status TEXT NOT NULL DEFAULT 'running'")
        if not db.execute("SELECT id FROM world_state WHERE id=1").fetchone():
            db.execute("INSERT INTO world_state (id, world_name, created_at) VALUES (1, ?, ?)", ("Reino Persistente", time.time()))
            starting = {"wood": 80, "stone": 50, "ore": 12, "food": 25, "leather": 0, "herbs": 5, "plank": 0, "iron": 0}
            for key, qty in starting.items():
                db.execute("INSERT OR IGNORE INTO resources (key, quantity, quality) VALUES (?, ?, ?)", (key, qty, random.randint(20, 35)))
            for key in BUILDINGS:
                db.execute("INSERT OR IGNORE INTO buildings (key, quantity) VALUES (?, 0)", (key,))
            db.execute("INSERT OR IGNORE INTO character_state (id) VALUES (1)")
            db.execute("INSERT INTO event_log (created_at, message) VALUES (?, ?)", (time.time(), "Sua propriedade foi fundada. O trabalho começa agora."))

        # Garante recursos e edifícios faltantes sem zerar o progresso existente.
        for key in RESOURCES:
            db.execute("INSERT OR IGNORE INTO resources (key, quantity, quality) VALUES (?, 0, 25)", (key,))
        for key in BUILDINGS:
            db.execute("INSERT OR IGNORE INTO buildings (key, quantity) VALUES (?, 0)", (key,))
        db.execute("INSERT OR IGNORE INTO character_state (id) VALUES (1)")
        for key in PROFESSIONS:
            db.execute("INSERT OR IGNORE INTO profession_state (profession_key, xp, level) VALUES (?, 0, 1)", (key,))
            db.execute("INSERT OR IGNORE INTO profession_workers (profession_key, workers) VALUES (?, 1)", (key,))


def log(db, message):
    db.execute("INSERT INTO event_log (created_at, message) VALUES (?, ?)", (time.time(), message))


def get_resource(db, key):
    row = db.execute("SELECT quantity FROM resources WHERE key=?", (key,)).fetchone()
    return row["quantity"] if row else 0


def specialist_is_hired(db, profession_key):
    return db.execute("SELECT profession_key FROM profession_specialists WHERE profession_key=?", (profession_key,)).fetchone() is not None


def tavern_rotation_id(now=None):
    return int((time.time() if now is None else now) // TAVERN_ROTATION_SECONDS)


def tavern_offers(now=None):
    """Gera ofertas estáveis durante 30 minutos e troca a lista no próximo ciclo."""
    rotation_id = tavern_rotation_id(now)
    offers = {}
    name_variants = {
        "lumberjack": ["Borin Machado-de-Carvalho", "Rurik Tronco-Forte", "Hilda Serra-Veloz", "Oren Galho-de-Ferro", "Mira Folha-Cortante"],
        "miner": ["Dagna Pedra-Funda", "Bruna Veio-Prateado", "Keld Rocha-Negra", "Tora Pico-de-Bronze", "Edrik Martelo-Pesado"],
        "herbalist": ["Líria Folha-Prateada", "Nara Raiz-Dourada", "Elwen Erva-Clara", "Sira Flor-da-Lua", "Maelis Orvalho-Verde"],
        "forager": ["Tomas Campo-Verde", "Bento Trilha-Farta", "Ivo Pão-de-Mel", "Rosa Fruto-do-Bosque", "Cael Passo-Leve"],
    }
    for key, spec in PROFESSIONS.items():
        rng = random.Random(f"{rotation_id}:{key}:reino-persistente")
        roll = rng.randint(1, 100)
        cumulative = 0
        level = 1
        for candidate_level, data in SPECIALIST_LEVELS.items():
            cumulative += data["chance"]
            if roll <= cumulative:
                level = candidate_level
                break
        mult = SPECIALIST_LEVELS[level]["multiplier"]
        # Mantém os bônus proporcionais ao nível, com teto de velocidade para evitar instantaneidade.
        speed = min(70, spec["speed_bonus"] * mult)
        quality = min(60, spec["quality_bonus"] * mult)
        cost_mult = SPECIALIST_LEVELS[level]["cost_multiplier"]
        costs = {resource: amount * cost_mult for resource, amount in spec["hire_cost"].items()}
        names = name_variants.get(key, [spec["specialist_name"]])
        candidate_name = names[(rotation_id + rng.randrange(len(names))) % len(names)]
        offers[key] = {"level": level, "level_name": SPECIALIST_LEVELS[level]["name"], "multiplier": mult,
                       "specialist_name": candidate_name, "speed_bonus": speed, "quality_bonus": quality, "hire_cost": costs,
                       "rotation_id": rotation_id}
    return offers


def specialist_bonus(db, profession_key):
    row = db.execute("SELECT level, speed_bonus, quality_bonus, specialist_name, skill FROM profession_specialists WHERE profession_key=?", (profession_key,)).fetchone()
    if not row:
        return {"hired": False, "level": 0, "level_name": "", "speed_bonus": 0, "quality_bonus": 0, "specialist_name": "", "skill": ""}
    level = row["level"] if "level" in row.keys() else 1
    return {"hired": True, "level": level, "level_name": SPECIALIST_LEVELS.get(level, SPECIALIST_LEVELS[1])["name"],
            "speed_bonus": row["speed_bonus"], "quality_bonus": row["quality_bonus"],
            "specialist_name": row["specialist_name"], "skill": row["skill"]}


def effective_gather_values(db, resource_key, tier_key):
    base = GATHER_CATALOG[resource_key]["tiers"][tier_key]
    profession_key = GATHER_CATALOG[resource_key]["profession"]
    bonus = specialist_bonus(db, profession_key)
    duration = max(1, round(base["duration"] * (1 - bonus["speed_bonus"] / 100)))
    quality = min(100, base["quality"] + bonus["quality_bonus"])
    return duration, quality


def change_resource(db, key, amount, quality=None):
    db.execute("INSERT OR IGNORE INTO resources (key, quantity, quality) VALUES (?, 0, 25)", (key,))
    if amount > 0 and quality is not None:
        current = db.execute("SELECT quantity, quality FROM resources WHERE key=?", (key,)).fetchone()
        old_qty = current["quantity"]
        new_quality = ((old_qty * current["quality"]) + (amount * quality)) / (old_qty + amount) if old_qty + amount else quality
        db.execute("UPDATE resources SET quantity=quantity+?, quality=? WHERE key=?", (amount, new_quality, key))
    else:
        db.execute("UPDATE resources SET quantity=quantity+? WHERE key=?", (amount, key))


def add_profession_xp(db, profession_key, xp):
    row = db.execute("SELECT xp, level FROM profession_state WHERE profession_key=?", (profession_key,)).fetchone()
    if not row:
        return
    new_xp = row["xp"] + xp
    new_level = 1 + new_xp // 100
    db.execute("UPDATE profession_state SET xp=?, level=? WHERE profession_key=?", (new_xp, new_level, profession_key))
    if new_level > row["level"]:
        log(db, f"Profissão {PROFESSIONS[profession_key]['name']} avançou para o nível {new_level}.")


def start_queued_gathers(db):
    """Inicia tarefas em fila até preencher as vagas de cada profissão."""
    now = time.time()
    for profession_key in PROFESSIONS:
        worker_row = db.execute("SELECT workers FROM profession_workers WHERE profession_key=?", (profession_key,)).fetchone()
        worker_count = worker_row["workers"] if worker_row else 1
        resource_keys = PROFESSIONS[profession_key]["resources"]
        placeholders = ",".join("?" for _ in resource_keys)
        running = db.execute(
            f"SELECT COUNT(*) n FROM gather_jobs WHERE status='running' AND resource_key IN ({placeholders})",
            tuple(resource_keys),
        ).fetchone()["n"]
        slots = max(0, worker_count - running)
        if slots:
            queued = db.execute("SELECT * FROM gather_jobs WHERE status='queued' AND resource_key IN (%s) ORDER BY id ASC LIMIT ?" % ",".join("?" for _ in PROFESSIONS[profession_key]["resources"]), (*PROFESSIONS[profession_key]["resources"], slots)).fetchall()
            for job in queued:
                duration, _quality = effective_gather_values(db, job["resource_key"], job["tier_key"])
                db.execute("UPDATE gather_jobs SET status='running', start_at=?, finish_at=? WHERE id=?", (now, now + duration, job["id"]))
                log(db, f"Coleta iniciada: {GATHER_CATALOG[job['resource_key']]['name']}.")


def process_due_jobs(db):
    now = time.time()
    due = db.execute("SELECT * FROM gather_jobs WHERE status='running' AND finish_at<=? ORDER BY finish_at", (now,)).fetchall()
    for job in due:
        catalog = GATHER_CATALOG.get(job["resource_key"])
        if not catalog:
            db.execute("UPDATE gather_jobs SET status='failed' WHERE id=?", (job["id"],))
            continue
        change_resource(db, job["resource_key"], job["amount"], job["quality"])
        profession_key = catalog["profession"]
        add_profession_xp(db, profession_key, 10 if job["tier_key"] == "common" else 20 if job["tier_key"] == "fine" else 35)
        db.execute("UPDATE gather_jobs SET status='completed' WHERE id=?", (job["id"],))
        log(db, f"Coleta concluída: +{job['amount']} {catalog['name'].lower()}.")
    start_queued_gathers(db)

    production = db.execute("SELECT * FROM production_jobs WHERE status='running' AND finish_at<=?", (now,)).fetchall()
    for job in production:
        spec = BUILDINGS.get(job["building_key"])
        if spec:
            for key, amount in spec["output"].items():
                change_resource(db, key, amount)
            log(db, f"Produção concluída: {spec['name']}.")
        db.execute("UPDATE production_jobs SET status='completed' WHERE id=?", (job["id"],))

    expeditions = db.execute("SELECT * FROM expeditions WHERE status='running' AND finish_at<=?", (now,)).fetchall()
    for expedition in expeditions:
        area = HUNT_AREAS[expedition["area_key"]]
        char = db.execute("SELECT * FROM character_state WHERE id=1").fetchone()
        chance = min(0.92, max(0.25, 0.78 + (char["hunting_level"] - area["danger"]) * 0.055))
        success = random.random() < chance
        rewards = {}
        if success:
            for key, (low, high) in area["rewards"].items():
                amount = random.randint(low, high)
                rewards[key] = amount
                change_resource(db, key, amount)
            xp_gain = 12 + area["danger"] * 8
            new_xp = char["xp"] + xp_gain
            db.execute("UPDATE character_state SET xp=?, hunting_level=? WHERE id=1", (new_xp, 1 + new_xp // 100))
            result = {"success": True, "rewards": rewards, "xp": xp_gain}
            log(db, f"Caça concluída em {area['name']}: sucesso! Você ganhou {xp_gain} XP.")
            status = "success"
        else:
            db.execute("UPDATE character_state SET recovery_until=? WHERE id=1", (now + 120,))
            result = {"success": False, "rewards": {}, "xp": 0}
            log(db, f"Caça em {area['name']} fracassou. Nenhum item foi perdido.")
            status = "failed"
        db.execute("UPDATE expeditions SET status=?, result_json=? WHERE id=?", (status, json.dumps(result), expedition["id"]))


def state():
    with connect() as db:
        process_due_jobs(db)
        resources = {r["key"]: {"quantity": r["quantity"], "quality": round(r["quality"], 1)} for r in db.execute("SELECT * FROM resources")}
        buildings = {r["key"]: r["quantity"] for r in db.execute("SELECT * FROM buildings")}
        jobs = [dict(r) for r in db.execute("SELECT id, building_key, start_at, finish_at, status FROM production_jobs WHERE status='running' ORDER BY finish_at")]
        gather_jobs = [dict(r) for r in db.execute("SELECT id, resource_key, tier_key, amount, quality, start_at, finish_at, status FROM gather_jobs WHERE status IN ('running','queued') ORDER BY CASE status WHEN 'running' THEN 0 ELSE 1 END, id")]
        expeditions = [dict(r) for r in db.execute("SELECT id, area_key, start_at, finish_at, status, result_json FROM expeditions ORDER BY id DESC LIMIT 8")]
        char_row = db.execute("SELECT * FROM character_state WHERE id=1").fetchone()
        professions = {}
        for row in db.execute("SELECT profession_key, xp, level FROM profession_state"):
            worker = db.execute("SELECT workers FROM profession_workers WHERE profession_key=?", (row["profession_key"],)).fetchone()
            xp_in_level = row["xp"] % 100
            pkey = row["profession_key"]
            specialist = specialist_bonus(db, pkey)
            professions[pkey] = {"xp": row["xp"], "level": row["level"], "xp_into_level": xp_in_level, "xp_needed": 100 - xp_in_level, "workers": worker["workers"] if worker else 1, "specialist_hired": specialist["hired"], "speed_bonus": specialist["speed_bonus"], "quality_bonus": specialist["quality_bonus"], "specialist_level": specialist["level"], "specialist_level_name": specialist["level_name"], "hired_specialist_name": specialist["specialist_name"], "hired_skill": specialist["skill"]}
        events = [dict(r) for r in db.execute("SELECT created_at, message FROM event_log ORDER BY id DESC LIMIT 10")]
        now = time.time()
        rotation_id = tavern_rotation_id(now)
        next_rotation = (rotation_id + 1) * TAVERN_ROTATION_SECONDS
        profession_catalog = {}
        offers = tavern_offers(now)
        for key, spec in PROFESSIONS.items():
            profession_catalog[key] = {**spec, "offer": offers[key]}
        return {"world": dict(db.execute("SELECT * FROM world_state WHERE id=1").fetchone()), "resources": resources, "resource_catalog": RESOURCES,
                "buildings": buildings, "building_catalog": BUILDINGS, "jobs": jobs, "gather_jobs": gather_jobs,
                "gather_catalog": GATHER_CATALOG, "professions": professions, "profession_catalog": profession_catalog,
                "tavern_rotation_id": rotation_id, "tavern_next_rotation": next_rotation,
                "character": dict(char_row), "areas": HUNT_AREAS, "expeditions": expeditions, "events": events, "server_time": now}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def api_state():
    return jsonify(state())


@app.route("/api/gather", methods=["POST"])
def gather():
    data = request.get_json(silent=True) or {}
    key = data.get("resource")
    tier_key = data.get("tier", "common")
    if key not in GATHER_CATALOG or tier_key not in GATHER_CATALOG[key]["tiers"]:
        return jsonify({"error": "Material ou qualidade de coleta inválidos."}), 400
    spec = GATHER_CATALOG[key]["tiers"][tier_key]
    profession_key = GATHER_CATALOG[key]["profession"]
    with connect() as db:
        process_due_jobs(db)
        profession = db.execute("SELECT level FROM profession_state WHERE profession_key=?", (profession_key,)).fetchone()
        if not profession or profession["level"] < spec["required_level"]:
            return jsonify({"error": f"Esta coleta exige nível {spec['required_level']} na profissão {PROFESSIONS[profession_key]['name']}."}), 400
        queued_count = db.execute("SELECT COUNT(*) n FROM gather_jobs WHERE status IN ('running','queued')").fetchone()["n"]
        if queued_count >= 50:
            return jsonify({"error": "A fila de coleta está cheia (limite de 50 tarefas)."}), 400
        now = time.time()
        _duration, effective_quality = effective_gather_values(db, key, tier_key)
        db.execute("INSERT INTO gather_jobs (resource_key, tier_key, amount, quality, start_at, finish_at, status) VALUES (?, ?, ?, ?, ?, ?, 'queued')",
                   (key, tier_key, spec["amount"], effective_quality, now, now))
        start_queued_gathers(db)
        log(db, f"Adicionada à fila: {spec['amount']} de {GATHER_CATALOG[key]['name'].lower()} ({spec['name'].lower()}).")
    return jsonify(state())


@app.route("/api/gather/batch", methods=["POST"])
def gather_batch():
    """Cria um lote de várias explorações com uma única confirmação do usuário."""
    data = request.get_json(silent=True) or {}
    key = data.get("resource")
    tier_key = data.get("tier", "common")
    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "Informe uma quantidade válida de explorações."}), 400
    if key not in GATHER_CATALOG or tier_key not in GATHER_CATALOG[key]["tiers"]:
        return jsonify({"error": "Material ou qualidade de coleta inválidos."}), 400
    if quantity < 1 or quantity > 50:
        return jsonify({"error": "A quantidade deve ficar entre 1 e 50 explorações."}), 400
    spec = GATHER_CATALOG[key]["tiers"][tier_key]
    profession_key = GATHER_CATALOG[key]["profession"]
    xp_each = 10 if tier_key == "common" else 20 if tier_key == "fine" else 35
    with connect() as db:
        process_due_jobs(db)
        profession = db.execute("SELECT level FROM profession_state WHERE profession_key=?", (profession_key,)).fetchone()
        if not profession or profession["level"] < spec["required_level"]:
            return jsonify({"error": f"Esta coleta exige nível {spec['required_level']} na profissão {PROFESSIONS[profession_key]['name']}."}), 400
        queued_count = db.execute("SELECT COUNT(*) n FROM gather_jobs WHERE status IN ('running','queued')").fetchone()["n"]
        if queued_count + quantity > 50:
            return jsonify({"error": f"A fila comporta até 50 tarefas. Há {queued_count} tarefa(s) ativa(s); você pode adicionar no máximo {50 - queued_count}."}), 400
        now = time.time()
        effective_duration, effective_quality = effective_gather_values(db, key, tier_key)
        db.executemany(
            "INSERT INTO gather_jobs (resource_key, tier_key, amount, quality, start_at, finish_at, status) VALUES (?, ?, ?, ?, ?, ?, 'queued')",
            [(key, tier_key, spec["amount"], effective_quality, now, now) for _ in range(quantity)]
        )
        start_queued_gathers(db)
        total_units = quantity * spec["amount"]
        total_work = quantity * effective_duration
        total_xp = quantity * xp_each
        log(db, f"Lote confirmado: {quantity} exploração(ões) de {GATHER_CATALOG[key]['name'].lower()} ({spec['name'].lower()}), {total_units} unidades previstas, {total_work} segundos de trabalho acumulado e {total_xp} XP previsto.")
    result = state()
    result["notice"] = f"Lote confirmado: {quantity} exploração(ões), {total_units} unidades e {total_xp} XP previsto."
    return jsonify(result)


@app.route("/api/gather/cancel", methods=["POST"])
def cancel_gather():
    """Cancela uma coleta específica ou todas as coletas ainda ativas."""
    data = request.get_json(silent=True) or {}
    job_id = data.get("id")
    cancel_all = bool(data.get("all", False))
    with connect() as db:
        process_due_jobs(db)
        if cancel_all:
            rows = db.execute("SELECT id FROM gather_jobs WHERE status IN ('running','queued')").fetchall()
            db.execute("UPDATE gather_jobs SET status='cancelled' WHERE status IN ('running','queued')")
        elif job_id is not None:
            row = db.execute("SELECT id, status FROM gather_jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return jsonify({"error": "Pedido de coleta não encontrado."}), 404
            if row["status"] not in ("running", "queued"):
                return jsonify({"error": "Este pedido já foi concluído ou não pode ser cancelado."}), 400
            rows = [row]
            db.execute("UPDATE gather_jobs SET status='cancelled' WHERE id=?", (job_id,))
        else:
            return jsonify({"error": "Informe o ID do pedido ou solicite o cancelamento de todos."}), 400
        cancelled = len(rows)
        if cancelled:
            log(db, f"Cancelamento de coleta: {cancelled} pedido(s) removido(s) da fila.")
        start_queued_gathers(db)
    result = state()
    result["notice"] = f"{cancelled} pedido(s) de coleta cancelado(s)."
    return jsonify(result)


@app.route("/api/gather/cancel-group", methods=["POST"])
def cancel_gather_group():
    data = request.get_json(silent=True) or {}
    resource = data.get("resource")
    tier = data.get("tier")
    if resource not in GATHER_CATALOG or tier not in GATHER_CATALOG[resource]["tiers"]:
        return jsonify({"error": "Grupo de coleta inválido."}), 400
    with connect() as db:
        process_due_jobs(db)
        rows = db.execute("SELECT id FROM gather_jobs WHERE resource_key=? AND tier_key=? AND status IN ('running','queued')", (resource, tier)).fetchall()
        db.execute("UPDATE gather_jobs SET status='cancelled' WHERE resource_key=? AND tier_key=? AND status IN ('running','queued')", (resource, tier))
        if rows:
            log(db, f"Cancelados {len(rows)} pedidos de coleta de {GATHER_CATALOG[resource]['name'].lower()}.")
        start_queued_gathers(db)
    result = state()
    result["notice"] = f"{len(rows)} pedido(s) de coleta cancelado(s)."
    return jsonify(result)


@app.route("/api/tavern/hire-specialist", methods=["POST"])
def hire_specialist():
    data = request.get_json(silent=True) or {}
    key = data.get("profession")
    if key not in PROFESSIONS:
        return jsonify({"error": "Profissão inválida para contratação."}), 400
    with connect() as db:
        process_due_jobs(db)
        current_rotation = tavern_rotation_id()
        if data.get("rotation_id") != current_rotation:
            return jsonify({"error": "A lista da taverna acabou de mudar. Confira a nova oferta antes de contratar."}), 409
        if specialist_is_hired(db, key):
            return jsonify({"error": f"Já existe um especialista contratado para {PROFESSIONS[key]['name']}."}), 400
        offer = tavern_offers().get(key)
        if not offer:
            return jsonify({"error": "Oferta não encontrada. Atualize a taverna."}), 400
        costs = offer["hire_cost"]
        missing = [(resource, amount) for resource, amount in costs.items() if get_resource(db, resource) < amount]
        if missing:
            needed = ", ".join(f"{amount} {RESOURCES[resource]['name']}" for resource, amount in missing)
            return jsonify({"error": f"Recursos insuficientes. Você precisa de: {needed}."}), 400
        for resource, amount in costs.items():
            change_resource(db, resource, -amount)
        base = PROFESSIONS[key]
        db.execute("INSERT INTO profession_specialists (profession_key, hired_at, level, speed_bonus, quality_bonus, specialist_name, skill) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (key, time.time(), offer["level"], offer["speed_bonus"], offer["quality_bonus"], offer["specialist_name"], base["skill"]))
        log(db, f"{offer['specialist_name']} ({offer['level_name']}) foi contratado(a) na taverna para {base['name']}; bônus de velocidade +{offer['speed_bonus']}% e qualidade +{offer['quality_bonus']}.")
        start_queued_gathers(db)
    result = state()
    result["notice"] = f"{offer['specialist_name']} ({offer['level_name']}) contratado(a)! Bônus: +{offer['speed_bonus']}% de velocidade e +{offer['quality_bonus']} de qualidade."
    return jsonify(result)


@app.route("/api/hire", methods=["POST"])
def hire():
    data = request.get_json(silent=True) or {}
    key = data.get("profession")
    if key not in PROFESSIONS:
        return jsonify({"error": "Profissão inválida para contratação."}), 400
    with connect() as db:
        process_due_jobs(db)
        row = db.execute("SELECT workers FROM profession_workers WHERE profession_key=?", (key,)).fetchone()
        current = row["workers"] if row else 1
        if current >= 10:
            return jsonify({"error": "Limite de 10 coletores por profissão atingido."}), 400
        multiplier = current
        costs = {resource: amount * multiplier for resource, amount in HIRE_BASE_COST.items()}
        for resource, amount in costs.items():
            if get_resource(db, resource) < amount:
                return jsonify({"error": f"Recursos insuficientes para contratar. Custo: {amount} {RESOURCES[resource]['name']}."}), 400
        for resource, amount in costs.items():
            change_resource(db, resource, -amount)
        db.execute("UPDATE profession_workers SET workers=workers+1 WHERE profession_key=?", (key,))
        log(db, f"Novo coletor contratado para a profissão {PROFESSIONS[key]['name']}.")
        start_queued_gathers(db)
    return jsonify(state())


@app.route("/api/build", methods=["POST"])
def build():
    data = request.get_json(silent=True) or {}
    key = data.get("building")
    if key not in BUILDINGS:
        return jsonify({"error": "Construção inválida."}), 400
    spec = BUILDINGS[key]
    with connect() as db:
        process_due_jobs(db)
        for resource, amount in spec["cost"].items():
            if get_resource(db, resource) < amount:
                return jsonify({"error": f"Recursos insuficientes: precisa de {amount} {RESOURCES[resource]['name']}."}), 400
        for resource, amount in spec["cost"].items():
            change_resource(db, resource, -amount)
        db.execute("UPDATE buildings SET quantity=quantity+1 WHERE key=?", (key,))
        log(db, f"Construção concluída: {spec['name']}.")
    return jsonify(state())


@app.route("/api/produce", methods=["POST"])
def produce():
    data = request.get_json(silent=True) or {}
    key = data.get("building")
    if key not in BUILDINGS:
        return jsonify({"error": "Receita inválida."}), 400
    spec = BUILDINGS[key]
    with connect() as db:
        process_due_jobs(db)
        row = db.execute("SELECT quantity FROM buildings WHERE key=?", (key,)).fetchone()
        if not row or row["quantity"] < 1:
            return jsonify({"error": f"Você precisa construir uma instalação: {spec['name']}."}), 400
        if db.execute("SELECT COUNT(*) n FROM production_jobs WHERE status='running'").fetchone()["n"] >= 3:
            return jsonify({"error": "Limite inicial de 3 tarefas simultâneas atingido."}), 400
        for resource, amount in spec["recipe"].items():
            if get_resource(db, resource) < amount:
                return jsonify({"error": f"Recursos insuficientes: precisa de {amount} {RESOURCES[resource]['name']}."}), 400
        for resource, amount in spec["recipe"].items():
            change_resource(db, resource, -amount)
        now = time.time()
        db.execute("INSERT INTO production_jobs (building_key, start_at, finish_at) VALUES (?, ?, ?)", (key, now, now + spec["duration"]))
        log(db, f"Iniciada produção na instalação: {spec['name']}.")
    return jsonify(state())


@app.route("/api/hunt", methods=["POST"])
def hunt():
    data = request.get_json(silent=True) or {}
    key = data.get("area")
    if key not in HUNT_AREAS:
        return jsonify({"error": "Área de caça inválida."}), 400
    with connect() as db:
        process_due_jobs(db)
        area = HUNT_AREAS[key]
        char = db.execute("SELECT * FROM character_state WHERE id=1").fetchone()
        if char["hunting_level"] < area["required_level"]:
            return jsonify({"error": f"Caça bloqueada: requer nível {area['required_level']}."}), 400
        if char["recovery_until"] > time.time():
            return jsonify({"error": f"Personagem em recuperação por mais {int(char['recovery_until'] - time.time())} segundos."}), 400
        if db.execute("SELECT COUNT(*) n FROM expeditions WHERE status='running'").fetchone()["n"]:
            return jsonify({"error": "Você já tem uma expedição em andamento."}), 400
        now = time.time()
        db.execute("INSERT INTO expeditions (area_key, start_at, finish_at) VALUES (?, ?, ?)", (key, now, now + area["duration"]))
        log(db, f"Expedição iniciada: {area['name']}. O combate será resolvido automaticamente.")
    return jsonify(state())


@app.route("/api/reset", methods=["POST"])
def reset():
    with connect() as db:
        for table in ("gather_jobs", "production_jobs", "expeditions", "event_log", "resources", "buildings", "character_state", "world_state", "profession_state", "profession_workers", "profession_specialists"):
            db.execute(f"DELETE FROM {table}")
    init_db()
    return jsonify(state())


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
