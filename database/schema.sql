-- Esquema documental do SQLite. app.py cria as tabelas automaticamente.
CREATE TABLE world_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  world_name TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE resources (
  key TEXT PRIMARY KEY,
  quantity INTEGER NOT NULL DEFAULT 0,
  quality REAL NOT NULL DEFAULT 25
);
CREATE TABLE buildings (
  key TEXT PRIMARY KEY,
  quantity INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE production_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  building_key TEXT NOT NULL,
  start_at REAL NOT NULL,
  finish_at REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'running'
);
CREATE TABLE character_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  hunting_level INTEGER NOT NULL DEFAULT 1,
  crafting_level INTEGER NOT NULL DEFAULT 1,
  xp INTEGER NOT NULL DEFAULT 0,
  recovery_until REAL NOT NULL DEFAULT 0
);
CREATE TABLE expeditions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  area_key TEXT NOT NULL,
  start_at REAL NOT NULL,
  finish_at REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  result_json TEXT
);
CREATE TABLE event_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at REAL NOT NULL,
  message TEXT NOT NULL
);
CREATE TABLE gather_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resource_key TEXT NOT NULL,
  tier_key TEXT NOT NULL,
  amount INTEGER NOT NULL,
  quality REAL NOT NULL,
  start_at REAL NOT NULL,
  finish_at REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'running'
);
