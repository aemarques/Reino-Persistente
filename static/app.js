const $ = (id) => document.getElementById(id);
let gameState = null;
let toastTimer = null;

function toast(message) {
  const el = $("toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  }[c]));
}

function fmtTime(seconds) {
  seconds = Math.max(0, Math.ceil(seconds));
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${String(s).padStart(2,'0')}s` : `${s}s`;
}

function costsText(cost) {
  return Object.entries(cost)
    .map(([k,v]) => `${v} ${gameState.resource_catalog[k].name}`)
    .join(" · ");
}

async function api(path, body={}) {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Não foi possível concluir a ação.");
    }

    gameState = data;
    render();

    toast(data.notice || (
      path === "/api/gather/cancel"
        ? "Pedido(s) cancelado(s)."
        : "Ação registrada no reino."
    ));
  } catch (err) {
    toast(err.message || "Erro de comunicação com o servidor.");
  }
}

const pickerSelections = {};

// Barra compacta do cabeçalho.
// Exibe somente os ícones e os saldos reais recebidos do servidor.
function renderHeaderResources() {
  const container = $("header-resources");

  if (!container || !gameState) return;

  const order = [
    "wood",
    "stone",
    "ore",
    "food",
    "leather",
    "herbs",
    "plank",
    "iron"
  ];

  container.innerHTML = order
    .filter(key =>
      gameState.resource_catalog?.[key] &&
      gameState.resources?.[key]
    )
    .map(key => {
      const meta = gameState.resource_catalog[key];
      const quantity = Number(
        gameState.resources[key].quantity || 0
      ).toLocaleString("pt-BR");

      return `
        <div
          class="header-resource-item"
          title="${esc(meta.name)}: ${quantity}"
          aria-label="${esc(meta.name)}: ${quantity}"
        >
          <span class="header-resource-icon" aria-hidden="true">${meta.icon}</span>
          <span class="header-resource-quantity">${quantity}</span>
        </div>
      `;
    })
    .join("");
}

function renderResources() {
  const order = [
    "wood",
    "stone",
    "ore",
    "food",
    "leather",
    "herbs",
    "plank",
    "iron"
  ];

  $("resources").innerHTML = order.map(key => {
    const item = gameState.resources[key] || {
      quantity: 0,
      quality: 25
    };

    const meta = gameState.resource_catalog[key];
    const gather = (gameState.gather_catalog || {})[key];

    let picker = "";

    if (gather) {
      const tiers = Object.entries(gather.tiers);
      const selectedTier = pickerSelections[key]?.tier || "common";
      const selectedQty = pickerSelections[key]?.qty || "1";

      picker = `
        <div class="resource-picker">
          <label>
            Qualidade
            <select id="tier-${key}" onchange="savePicker('${key}')">
              ${tiers.map(([tier,spec]) => `
                <option
                  value="${tier}"
                  ${tier === selectedTier ? 'selected' : ''}
                >${esc(spec.name)}</option>
              `).join("")}
            </select>
          </label>

          <label>
            Quantidade de explorações
            <select id="qty-${key}" onchange="savePicker('${key}')">
              ${[1,5,10,20,50].map(n => `
                <option
                  value="${n}"
                  ${String(n) === String(selectedQty) ? 'selected' : ''}
                >
                  ${n} ${n === 1 ? 'exploração' : 'explorações'}
                </option>
              `).join("")}
            </select>
          </label>

          <div class="resource-gather-info" id="info-${key}"></div>

          <button
            class="resource-gather-button"
            onclick="reviewGather('${key}')"
          >Revisar pedido</button>

          <div
            class="gather-confirm-box"
            id="preview-${key}"
            hidden
          ></div>
        </div>
      `;
    }

    const professionKey = gameState.gather_catalog?.[key]?.profession;
    const profession = professionKey
      ? gameState.profession_catalog?.[professionKey]
      : null;
    const worker = professionKey
      ? gameState.professions?.[professionKey]
      : null;

    const workerBadge =
      worker?.specialist_hired && profession?.portrait_image
        ? `
          <img
            class="resource-worker-portrait"
            src="${esc(profession.portrait_image)}"
            alt="${esc(worker.hired_specialist_name || "Especialista contratado")}"
            title="Responsável: ${esc(worker.hired_specialist_name || profession.specialist_name)} · ${esc(worker.specialist_level_name || "Especialista")}"
          >
        `
        : "";

    return `
      <div class="resource-card">
        <div class="resource-top">
          <div class="resource-title">
            <span class="resource-icon">${meta.icon}</span>
            <span>${esc(meta.name)}</span>
          </div>
          ${workerBadge}
        </div>

        <div class="resource-qty">
          ${item.quantity.toLocaleString("pt-BR")}
        </div>

        <div class="quality">
          Qualidade média: ${item.quality}
        </div>

        ${picker}
      </div>
    `;
  }).join("");

  order.forEach(key => updateGatherInfo(key));
}

function savePicker(key) {
  pickerSelections[key] = {
    tier: $("tier-" + key)?.value || "common",
    qty: $("qty-" + key)?.value || "1"
  };

  updateGatherInfo(key);
}

function effectiveGatherValues(key, tier) {
  const gather = gameState?.gather_catalog?.[key];

  if (!gather) {
    return {
      duration: 0,
      quality: 0,
      speedBonus: 0,
      qualityBonus: 0
    };
  }

  const spec = gather.tiers[tier];
  const profession = gameState.professions?.[gather.profession] || {};

  const speedBonus = profession.specialist_hired
    ? Number(profession.speed_bonus || 0)
    : 0;

  const qualityBonus = profession.specialist_hired
    ? Number(profession.quality_bonus || 0)
    : 0;

  return {
    duration: Math.max(
      1,
      Math.round(spec.duration * (1 - speedBonus / 100))
    ),
    quality: Math.min(100, spec.quality + qualityBonus),
    speedBonus,
    qualityBonus
  };
}

function updateGatherInfo(key) {
  const target = $("info-" + key);
  const gather = gameState?.gather_catalog?.[key];

  if (!target || !gather) return;

  const tier = $("tier-" + key)?.value || "common";
  const qty = Number($("qty-" + key)?.value || 1);
  const spec = gather.tiers[tier];
  const effective = effectiveGatherValues(key, tier);

  const bonusText = effective.speedBonus
    ? ` · ${effective.speedBonus}% mais rápido · qualidade ${effective.quality}`
    : ` · qualidade ${effective.quality}`;

  target.textContent =
    `${qty} lote(s) · ${qty * spec.amount} unidades · ` +
    `${fmtTime(qty * effective.duration)} de trabalho${bonusText}`;
}

function gatherXpForTier(tier) {
  return tier === "common" ? 10 : tier === "fine" ? 20 : 35;
}

function reviewGather(key) {
  const tierKey = $("tier-" + key)?.value || "common";

  const quantity = Math.max(
    1,
    Math.min(50, Number($("qty-" + key)?.value || 1))
  );

  const resource = gameState.gather_catalog[key];
  const spec = resource.tiers[tierKey];
  const effective = effectiveGatherValues(key, tierKey);
  const xp = gatherXpForTier(tierKey) * quantity;
  const box = $("preview-" + key);

  if (!box) return;

  box.hidden = false;

  box.innerHTML = `
    <div class="gather-confirm-title">Confirmar exploração</div>

    <div class="gather-confirm-grid">
      <div>
        <span>Recurso</span>
        <b>${esc(resource.name)} — ${esc(spec.name)}</b>
      </div>

      <div>
        <span>Quantidade</span>
        <b>${quantity} exploração(ões)</b>
      </div>

      <div>
        <span>Montante total</span>
        <b>${(quantity * spec.amount).toLocaleString("pt-BR")} unidades</b>
      </div>

      <div>
        <span>Tempo total de trabalho</span>
        <b>${fmtTime(quantity * effective.duration)}</b>
      </div>

      <div>
        <span>Qualidade de coleta</span>
        <b>
          ${effective.quality}/100
          ${effective.qualityBonus ? ` (+${effective.qualityBonus} do especialista)` : ""}
        </b>
      </div>

      <div>
        <span>XP total previsto</span>
        <b>${xp} XP</b>
      </div>
    </div>

    <div class="gather-confirm-actions">
      <button onclick="confirmGatherBatch('${key}')">
        Confirmar pedido
      </button>

      <button
        class="secondary-button"
        onclick="closeGatherPreview('${key}')"
      >Voltar</button>
    </div>
  `;
}

function closeGatherPreview(key) {
  const box = $("preview-" + key);

  if (box) {
    box.hidden = true;
    box.innerHTML = "";
  }
}

async function confirmGatherBatch(key) {
  const tier = $("tier-" + key)?.value || "common";

  const quantity = Math.max(
    1,
    Math.min(50, Number($("qty-" + key)?.value || 1))
  );

  const box = $("preview-" + key);
  const buttons = box ? box.querySelectorAll("button") : [];

  buttons.forEach(button => button.disabled = true);

  try {
    const response = await fetch("/api/gather/batch", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        resource: key,
        tier,
        quantity
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Não foi possível confirmar o lote.");
    }

    gameState = data;
    render();
    toast(data.notice || "Lote de exploração confirmado.");
  } catch (err) {
    await refresh();
    toast(err.message || "Não foi possível confirmar o lote.");
  }
}

function renderGather() {
  const el = $("gather-actions");
  if (el) el.innerHTML = "";
}

function renderGatherJobs() {
  const jobs = gameState.gather_jobs || [];
  const el = $("gather-jobs");

  if (!el) return;

  if (!jobs.length) {
    el.innerHTML = `
      <div class="small">
        Nenhuma coleta ativa ou aguardando.
        Escolha o material acima para montar um pedido.
      </div>
    `;
    return;
  }

  const groups = {};

  jobs.forEach(job => {
    const k = `${job.resource_key}|${job.tier_key}`;

    if (!groups[k]) {
      groups[k] = {
        resource_key: job.resource_key,
        tier_key: job.tier_key,
        jobs: [],
        work: 0,
        remaining: 0,
        queued: 0,
        running: 0,
        xp: 0
      };
    }

    const g = groups[k];
    g.jobs.push(job);

    const resource = gameState.gather_catalog[job.resource_key];
    const tier = resource.tiers[job.tier_key];

    g.work += tier.duration;
    g.xp += gatherXpForTier(job.tier_key);

    if (job.status === "running") {
      g.running++;
      g.remaining += Math.max(0, job.finish_at - gameState.server_time);
    } else {
      g.queued++;
      g.remaining += tier.duration;
    }
  });

  const values = Object.values(groups);

  el.innerHTML = `
    <div class="gather-queue-tools">
      <span class="small">
        ${jobs.length} exploração(ões) ativa(s) ou aguardando
      </span>
      <button class="cancel-all-button" onclick="cancelAllGather()">
        Cancelar todos
      </button>
    </div>
  ` + values.map(g => {
    const resource = gameState.gather_catalog[g.resource_key];
    const tier = resource.tiers[g.tier_key];
    const workers = Math.max(
      1,
      gameState.professions?.[resource.profession]?.workers || 1
    );

    const totalUnits = g.jobs.reduce((n, x) => n + x.amount, 0);
    const runningJobs = g.jobs.filter(j => j.status === "running");
    const queuedJobs = g.jobs.filter(j => j.status !== "running");
    const remainingRunning = runningJobs.reduce(
      (n, j) => n + Math.max(0, j.finish_at - gameState.server_time),
      0
    );

    const estimated = Math.ceil(
      (remainingRunning + queuedJobs.length * tier.duration) / workers
    );

    const pct = g.jobs.length
      ? Math.min(100, Math.round((g.running / g.jobs.length) * 100))
      : 0;

    return `
      <div class="gather-batch">
        <div class="gather-batch-head">
          <div>
            <b>${esc(resource.name)} — ${esc(tier.name)}</b>
            <div class="small">
              ${g.running} em andamento · ${g.queued} aguardando
            </div>
          </div>
          <span class="tag">${totalUnits.toLocaleString("pt-BR")} unidades</span>
        </div>

        <div class="progress">
          <span style="width:${pct}%"></span>
        </div>

        <div class="gather-total-summary">
          <span>Trabalho acumulado: <b>${fmtTime(g.work)}</b></span>
          <span>XP total previsto: <b>${g.xp} XP</b></span>
          <span>
            Estimativa com ${workers} trabalhador(es):
            <b>${fmtTime(estimated)}</b>
          </span>
        </div>

        <div class="gather-batch-bottom">
          <span>${workers} trabalhador(es) nesta profissão</span>
          <button
            class="cancel-job-button"
            onclick="cancelGatherGroup('${g.resource_key}','${g.tier_key}')"
          >Cancelar este grupo</button>
        </div>
      </div>
    `;
  }).join("");
}

async function cancelGatherGroup(resource, tier) {
  const matching = (gameState.gather_jobs || []).filter(
    j => j.resource_key === resource && j.tier_key === tier
  );

  if (
    !matching.length ||
    !confirm(`Cancelar os ${matching.length} lote(s) deste material e qualidade?`)
  ) return;

  await api("/api/gather/cancel-group", {resource, tier});
}

async function cancelAllGather() {
  const count = (gameState.gather_jobs || []).length;

  if (
    !count ||
    !confirm(`Cancelar todos os ${count} lotes ativos ou aguardando?`)
  ) return;

  await api("/api/gather/cancel", {all:true});
}

function renderTavern() {
  const el = $("tavern-specialists");
  if (!el) return;

  const catalog = gameState.profession_catalog || {};

  const remaining = Math.max(
    0,
    (gameState.tavern_next_rotation || gameState.server_time) -
      gameState.server_time
  );

  const timer = $("tavern-rotation-timer");

  if (timer) {
    timer.textContent = `Próxima renovação em ${fmtTime(remaining)}`;
  }

  el.innerHTML = Object.entries(catalog).map(([key, profession]) => {
    const status = gameState.professions?.[key] || {};
    const hired = Boolean(status.specialist_hired);
    const offer = profession.offer || {};

    const levelName = hired
      ? (status.specialist_level_name || "Básico")
      : (offer.level_name || "Básico");

    const speed = hired
      ? Number(status.speed_bonus || 0)
      : Number(offer.speed_bonus || 0);

    const quality = hired
      ? Number(status.quality_bonus || 0)
      : Number(offer.quality_bonus || 0);

    const costsObj = hired
      ? {}
      : (offer.hire_cost || profession.hire_cost || {});

    const costs = Object.entries(costsObj)
      .map(([resource, amount]) =>
        `${amount} ${gameState.resource_catalog[resource]?.name || resource}`
      )
      .join(" · ");

    const portrait = `
      <div
        class="portrait-art ${hired ? "" : "portrait-empty"}"
        aria-label="Retrato do especialista"
      >
        ${hired
          ? `
            <img
              src="${esc(profession.portrait_image || "")}"
              alt="Retrato de ${esc(status.hired_specialist_name || profession.specialist_name)}"
            >
          `
          : `
            <img
              src="${esc(profession.portrait_image || "")}"
              alt="Retrato ilustrativo do especialista"
            >
            <span class="portrait-overlay">Oferta</span>
          `
        }
      </div>
      <span class="portrait-caption">
        ${hired ? "Especialista contratado" : "Retrato do candidato"}
      </span>
    `;

    const levelClass =
      `specialist-level level-${hired ? status.specialist_level : offer.level}`;

    return `
      <article class="specialist-card ${hired ? "specialist-hired" : ""}">
        <div class="specialist-card-head">
          <div class="specialist-portrait">${portrait}</div>

          <div class="specialist-heading">
            <span class="specialist-profession">
              ${esc(profession.name)}
            </span>

            <h3>
              ${esc(
                hired
                  ? (status.hired_specialist_name || profession.specialist_name)
                  : (offer.specialist_name || profession.specialist_name)
              )}
            </h3>

            <span class="specialist-title">
              ${esc(profession.specialty)}
            </span>

            <span class="${levelClass}">
              ${esc(levelName)}${hired ? " · contratado" : " · oferta atual"}
            </span>
          </div>
        </div>

        <p class="specialist-description">
          ${esc(profession.description)}
        </p>

        <div class="specialist-skill">
          <span class="skill-mark">✦</span>
          <div>
            <b>${esc(profession.skill)}</b>
            <span>
              Coleta ${speed}% mais rápida · +${quality} de qualidade
            </span>
            <small>
              Multiplicador:
              ${hired ? status.specialist_level : offer.multiplier || 1}x
            </small>
          </div>
        </div>

        ${hired
          ? `
            <div class="specialist-hired-note">
              ✓ Trabalhando nesta profissão
            </div>
          `
          : `
            <div class="specialist-cost">
              <span>Custo de contratação · ${esc(levelName)}</span>
              <b>${esc(costs)}</b>
            </div>

            <button
              class="specialist-hire-button"
              onclick="hireSpecialist('${key}',${gameState.tavern_rotation_id})"
            >Contratar especialista</button>
          `
        }
      </article>
    `;
  }).join("");
}

async function hireSpecialist(profession, rotation_id) {
  await api("/api/tavern/hire-specialist", {profession, rotation_id});
}

function renderBuildings() {
  const catalog = gameState.building_catalog;

  $("buildings").innerHTML = Object.entries(catalog).map(([key,b]) => {
    const count = gameState.buildings[key] || 0;

    return `
      <div class="item-card">
        <div class="item-title">
          <span>${esc(b.name)}</span>
          <span class="tag">Construídas: ${count}</span>
        </div>

        <p>${esc(b.description)}</p>
        <div class="cost">Custo: ${costsText(b.cost)}</div>

        <button onclick="api('/api/build',{building:'${key}'})">
          Construir instalação
        </button>
      </div>
    `;
  }).join("");
}

function renderProduction() {
  $("production").innerHTML = Object.entries(gameState.building_catalog).map(([key,b]) => {
    const output = Object.entries(b.output)
      .map(([k,v]) => `${v} ${gameState.resource_catalog[k].name}`)
      .join(", ");

    const recipe = Object.entries(b.recipe)
      .map(([k,v]) => `${v} ${gameState.resource_catalog[k].name}`)
      .join(", ");

    return `
      <div class="item-card">
        <div class="item-title">
          ${esc(b.name)}
          <span class="tag">${fmtTime(b.duration)}</span>
        </div>

        <p>Consome: ${recipe}<br>Produz: ${output}</p>

        <button onclick="api('/api/produce',{building:'${key}'})">
          Adicionar à fila
        </button>
      </div>
    `;
  }).join("");
}

function renderJobs() {
  const jobs = gameState.jobs;

  if (!jobs.length) {
    $("jobs").innerHTML = `
      <div class="small">
        Nenhum trabalho em andamento.
        Construa uma instalação e inicie uma produção.
      </div>
    `;
    return;
  }

  const now = gameState.server_time;

  $("jobs").innerHTML = jobs.map(job => {
    const spec = gameState.building_catalog[job.building_key];
    const remaining = job.finish_at - now;
    const total = job.finish_at - job.start_at;

    const pct = Math.max(
      0,
      Math.min(100, 100 - (remaining / total * 100))
    );

    return `
      <div class="list-row">
        <div>
          <b>${esc(spec.name)}</b>
          <div class="progress">
            <span style="width:${pct}%"></span>
          </div>
        </div>
        <span class="timer" data-finish="${job.finish_at}">
          ${fmtTime(remaining)}
        </span>
      </div>
    `;
  }).join("");
}

function renderHunting() {
  const icons = {
    grove: "🦌",
    deep_forest: "🐺",
    highlands: "🐗"
  };

  $("hunting").innerHTML = Object.entries(gameState.areas).map(([key,area]) => {
    const unlocked =
      gameState.character.hunting_level >= area.required_level;

    const rewards = Object.keys(area.rewards)
      .map(k => gameState.resource_catalog[k].name)
      .join(", ");

    return `
      <div class="hunt-card">
        <div class="hunt-art">${icons[key] || "🌲"}</div>

        <div class="item-title">
          ${esc(area.name)}
          <span class="tag">Perigo ${area.danger}/5</span>
        </div>

        <p>
          ${esc(area.description)}<br>
          Tempo estimado: ${fmtTime(area.duration)}<br>
          Espólios possíveis: ${esc(rewards)}
        </p>

        <button
          ${unlocked ? "" : "disabled"}
          onclick="api('/api/hunt',{area:'${key}'})"
        >
          ${unlocked ? "Iniciar expedição" : `Requer nível ${area.required_level}`}
        </button>
      </div>
    `;
  }).join("");
}

function renderExpeditions() {
  const exps = gameState.expeditions;

  if (!exps.length) {
    $("expeditions").innerHTML = `
      <div class="small" style="margin-top:14px">
        Nenhuma expedição registrada.
      </div>
    `;
    return;
  }

  $("expeditions").innerHTML = exps.map(e => {
    const area = gameState.areas[e.area_key];
    const running = e.status === "running";

    let status = running
      ? `Em andamento · <span class="timer" data-finish="${e.finish_at}">${fmtTime(e.finish_at-gameState.server_time)}</span>`
      : e.status === "success"
        ? "Concluída com sucesso"
        : "Expedição fracassada — sem perda de itens";

    let result = "";

    if (e.result_json) {
      try {
        const r = JSON.parse(e.result_json);

        if (r.success) {
          result = `
            <div class="small">
              Recompensas:
              ${Object.entries(r.rewards)
                .map(([k,v]) => `${v} ${gameState.resource_catalog[k].name}`)
                .join(" · ")}
              · +${r.xp} XP
            </div>
          `;
        }
      } catch (_) {}
    }

    return `
      <div class="list-row">
        <div>
          <b>${esc(area.name)}</b>
          <div class="small">${status}</div>
          ${result}
        </div>
      </div>
    `;
  }).join("");
}

function renderCharacter() {
  const c = gameState.character;
  const recovery = Math.max(0, c.recovery_until - gameState.server_time);

  $("character").innerHTML = `
    <div class="char-stats">
      <div class="char-stat">
        <span class="small">Nível de caça</span>
        <b>${c.hunting_level}</b>
      </div>

      <div class="char-stat">
        <span class="small">Nível de ofícios</span>
        <b>${c.crafting_level}</b>
      </div>

      <div class="char-stat">
        <span class="small">Experiência de caça</span>
        <b>${c.xp} XP</b>
      </div>

      <div class="char-stat">
        <span class="small">Recuperação</span>
        <b style="font-size:17px">
          ${recovery > 0 ? fmtTime(recovery) : "Pronto"}
        </b>
      </div>
    </div>

    <p class="small" style="margin-top:12px">
      A cada 100 XP, o personagem sobe um nível de caça.
      Os valores são provisórios para teste.
    </p>
  `;
}

function renderEvents() {
  $("events").innerHTML = gameState.events.map(e => {
    const d = new Date(e.created_at * 1000);

    return `
      <div class="event">
        ${esc(e.message)}
        <time>${d.toLocaleString("pt-BR")}</time>
      </div>
    `;
  }).join("");
}

function render() {
  if (!gameState) return;

  renderHeaderResources();
  renderResources();
  renderGather();
  renderGatherJobs();
  renderTavern();
  renderBuildings();
  renderProduction();
  renderJobs();
  renderHunting();
  renderExpeditions();
  renderCharacter();
  renderEvents();
}

async function refresh() {
  try {
    const response = await fetch("/api/state");
    gameState = await response.json();
    render();
  } catch (_) {
    toast("Não foi possível conectar ao servidor local.");
  }
}

setInterval(() => {
  if (!gameState) return;

  const now = Date.now() / 1000;

  document.querySelectorAll("[data-finish]").forEach(el => {
    el.textContent = fmtTime(Number(el.dataset.finish) - now);
  });

  // Reconsulta o servidor periodicamente para finalizar filas e expedições.
}, 1000);

setInterval(refresh, 5000);
refresh();