import {
  ensureVisitorSession,
  generateItinerary,
  getAttraction,
  getBootstrap,
  getLocalVoices,
  recordEvent,
  recordFavorite,
  recordFootprint,
} from '../api.js'

export function createBijiangSite(app, toast) {
const villageMapUrl = new URL('./assets/village-map.png', import.meta.url).href;
const ancestralHallUrl = new URL('./assets/ancestral-hall.png', import.meta.url).href;
const pendantImg = new URL('./assets/挂件.png', import.meta.url).href;
const sensorImg = new URL('./assets/感应装置.png', import.meta.url).href;
const langImg = new URL('./assets/多语言支持.png', import.meta.url).href;
const navImg = new URL('./assets/路线智能导航.png', import.meta.url).href;
const storyBgImg = new URL('./assets/碧江故事.png', import.meta.url).href;
const bridgeStoryImg = new URL('./assets/一座古桥，连起几代人的时光.png', import.meta.url).href;
const oldPierImg = new URL('./assets/老码头记忆.png', import.meta.url).href;
const overviewImg = new URL('./assets/村落概览.png', import.meta.url).href;
const clanImg = new URL('./assets/宗祠家风.png', import.meta.url).href;
const watersideImg = new URL('./assets/古桥与水流.png', import.meta.url).href;
const poetryImg = new URL('./assets/诗词与巷道.png', import.meta.url).href;
const placeImgUrls = {
  "huang-ancestral-hall": new URL('./assets/黄氏宗祠.png', import.meta.url).href,
  "village-history-museum": new URL('./assets/村史馆.png', import.meta.url).href,
  "bixi-scholar-hall": new URL('./assets/碧溪书公祠.png', import.meta.url).href,
  "dong-ancestral-hall": new URL('./assets/东氏宗祠.png', import.meta.url).href,
  "ancient-bridge": new URL('./assets/古桥.png', import.meta.url).href,
  "poetry-lane": new URL('./assets/诗词巷.png', import.meta.url).href,
  "xiuxi-peng-ancestral-hall": new URL('./assets/绣西彭公祠.png', import.meta.url).href,
  "old-wharf": new URL('./assets/老码头.png', import.meta.url).href,
  "waterside-ancient-tree": new URL('./assets/水岸古树.png', import.meta.url).href,
};
const walkImg = new URL('./assets/今日已步行(1)(1).png', import.meta.url).href;
const unlockImg = new URL('./assets/今日已步行(1)(2).png', import.meta.url).href;
const moduleIconUrls = {
  "module-interest": new URL('./assets/module-interest.png', import.meta.url).href,
  "module-map": new URL('./assets/module-map.png', import.meta.url).href,
  "module-stamp": new URL('./assets/module-stamp.png', import.meta.url).href,
  "module-story": new URL('./assets/module-story.png', import.meta.url).href,
};
const profileAvatarImg = new URL('./assets/游客.png', import.meta.url).href;
const profileBgImg = new URL('./assets/游客背景图.png', import.meta.url).href;
const footprintIconImg = new URL('./assets/足迹.png', import.meta.url).href;
const footprintBgImg = new URL('./assets/足迹背景图.png', import.meta.url).href;
const storyIconImg = new URL('./assets/收藏故事.png', import.meta.url).href;
const collectStoryBgImg = new URL('./assets/收藏故事背景图.png', import.meta.url).href;
const deviceIconImg = new URL('./assets/设备管理.png', import.meta.url).href;
const historyIconImg = new URL('./assets/历史路线.png', import.meta.url).href;
const historyBgImg = new URL('./assets/历史路线背景图.png', import.meta.url).href;

const interestBgImg = new URL('./assets/兴趣路线背景图.png', import.meta.url).href;
const routePreviewImg = new URL('./assets/路线预览.png', import.meta.url).href;

const interestIconMap = {
  "古建筑": new URL('./assets/古建筑.png', import.meta.url).href,
  "宗族故事": new URL('./assets/宗族故事.png', import.meta.url).href,
  "人物旧居": new URL('./assets/人物旧居.png', import.meta.url).href,
  "诗词记忆": new URL('./assets/诗词记忆.png', import.meta.url).href,
  "巷道漫游": new URL('./assets/巷道漫游.png', import.meta.url).href,
  "民俗生活": new URL('./assets/民俗生活.png', import.meta.url).href,
  "水岸风景": new URL('./assets/水岸风景.png', import.meta.url).href,
  "亲子体验": new URL('./assets/亲子体验.png', import.meta.url).href,
};

const icon = (name, className = "") =>
  `<svg class="icon ${className}" aria-hidden="true"><use href="#i-${name}"></use></svg>`;

let interests = [];
let places = [];

const DEMO_STORAGE_KEY = 'bijiang_indoor_demo_state';
const DEMO_STORAGE_VERSION = 2;

function readDemoState() {
  try {
    const saved = JSON.parse(localStorage.getItem(DEMO_STORAGE_KEY) || '{}');
    return saved.version === DEMO_STORAGE_VERSION
      ? saved
      : { ...saved, route: null };
  } catch {
    return {};
  }
}

const savedDemoState = readDemoState();

const state = {
  view: location.hash.slice(1) || "home",
  interests: new Set(savedDemoState.interests || ["岭南建筑", "诗书文脉"]),
  duration: savedDemoState.duration || 60,
  mode: savedDemoState.mode || "relaxed",
  route: savedDemoState.route || null,
  generating: false,
  pendingArrival: null,
  unlockedStampSlug: null,
  currentSimulatedSlug: savedDemoState.currentSimulatedSlug || null,
  visitedSlugs: new Set(savedDemoState.visitedSlugs || []),
  locationStatus: "idle",
  locationMessage: "",
  realLocation: null,
  selectedAttraction: null,
  attractionDetail: null,
  detailLoading: false,
  bootstrapReady: false,
  localVoices: [],
  localVoicesLoading: true,
  localVoicesError: "",
  activeLocalVoiceId: null,
  localVoicePlaying: false,
  localVoiceCurrentTime: 0,
  audioPlaying: false,
  audioProgress: 28,
};

function persistDemoState() {
  localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify({
    version: DEMO_STORAGE_VERSION,
    interests: Array.from(state.interests),
    duration: state.duration,
    mode: state.mode,
    route: state.route,
    currentSimulatedSlug: state.currentSimulatedSlug,
    visitedSlugs: Array.from(state.visitedSlugs),
  }));
}

const validViews = new Set(["home", "stamps", "stories", "profile", "interests", "route", "attraction", "ancestral", "overview", "clan", "waterside", "poetry"]);
if (!validViews.has(state.view)) state.view = "home";

function shell(content, options = {}) {
  const active = options.active || ({
    home: "home", stamps: "explore", interests: "explore", route: "explore",
    stories: "stories", ancestral: "stories", overview: "stories", clan: "stories", waterside: "stories", poetry: "stories", profile: "profile",
  })[state.view];
  const back = options.back ? `<button class="icon-button back-button" data-action="back" aria-label="返回上一页">${icon("back")}</button>` : "";
  const nav = options.nav === false ? "" : `
    <nav class="bottom-nav" aria-label="主导航">
      ${navItem("home", "home", "首页", active)}
      ${navItem("stamps", "compass", "探索", active, "explore")}
      ${navItem("stories", "book", "故事", active)}
      ${navItem("profile", "user", "我的", active)}
    </nav>`;
  return `<div class="app-shell ${options.className || ""}">${back}<main class="page">${content}</main>${nav}</div>`;
}

function navItem(route, iconName, label, active, key = route) {
  return `<button class="nav-item ${active === key ? "is-active" : ""}" data-route="${route}" aria-label="${label}" ${active === key ? 'aria-current="page"' : ""}>${icon(iconName)}<span>${label}</span></button>`;
}

function sectionTitle(title, action = "") {
  return `<div class="section-heading"><h2>${title}</h2>${action}</div>`;
}

function renderHome() {
  const modules = [
    ["兴趣路线", "主题路线推荐", moduleIconUrls["module-interest"], "interests"],
    ["村落地图", "手绘地图导览", moduleIconUrls["module-map"], "route"],
    ["集章寻迹", "打卡集章留念", moduleIconUrls["module-stamp"], "stamps"],
    ["碧江故事", "聆听村落记忆", moduleIconUrls["module-story"], "stories"],
  ];
  return shell(`
    <header class="brand-bar reveal"><a class="brand" href="#home" data-route="home" aria-label="碧江寻迹首页"><span class="brand-mark">碧</span><span>碧江寻迹</span></a></header>
    <section class="hero reveal">
      <div class="hero-copy"><h1>你好，<small>欢迎来到碧江村</small></h1><p>半导航 · 半探索 · 半陪伴式讲解</p></div>
      <img src="${villageMapUrl}" alt="碧江村水乡手绘地图" />
      <div class="hero-pins" aria-hidden="true"><span style="--x:61%;--y:34%">村史馆</span><span style="--x:72%;--y:48%">古桥</span><span style="--x:82%;--y:66%">老码头</span></div>
    </section>
    <section class="module-grid reveal" aria-label="主要功能">
      ${modules.map(([title, sub, imgUrl, route], index) => `<button class="module-card" data-route="${route}" style="--delay:${index * 60}ms"><span class="module-icon"><img src="${imgUrl}" alt="" /></span><strong>${title}</strong><small>${sub}</small><span class="circle-arrow">${icon("arrow")}</span></button>`).join("")}
    </section>
    <section class="device-banner reveal">
  <div class="device-info">
    <h2>租用寻迹挂件 · 解锁沉浸体验</h2>
    <p class="sub-desc">佩戴挂件，开启智能讲解与互动体验</p>
    <div class="feature-grid">
      <span class="feature-item">
        <img class="fi-icon" src="${sensorImg}" alt="自动感应讲解" />
        <span>自动感应讲解</span>
      </span>
      <span class="feature-item">
        <img class="fi-icon" src="${langImg}" alt="多语言支持" />
        <span>多语言支持</span>
      </span>
      <span class="feature-item">
        <span class="fi-icon icon-svg">${icon("stamp")}</span>
        <span>集章互动</span>
      </span>
      <span class="feature-item">
        <img class="fi-icon" src="${navImg}" alt="路线智能导航" />
        <span>路线智能导航</span>
      </span>
    </div>
    <button class="secondary-button" data-action="toast" data-message="挂件租用服务即将开放">
      查看挂件 ${icon("arrow")}
    </button>
  </div>
  <div class="device-pendant" aria-hidden="true">
    <img src="${pendantImg}" alt="碧江寻迹挂件" />
  </div>
</section>
  `, { className: "home-view" });
}

function renderStamps() {
  const litCount = places.filter(place => state.visitedSlugs.has(place.slug)).length;
  return shell(`
    <header class="page-hero reveal"><div><h1>集章寻迹</h1><p>步履所至，皆为故事；印章点亮，记一方水岸。</p></div></header>
    <section class="stamp-progress reveal"><strong>已点亮 <b>${litCount}</b> / ${places.length} 个印章点</strong><div>${places.map(place => {
      const isLit = state.visitedSlugs.has(place.slug);
      return `<span class="mini-stamp ${isLit ? "lit" : ""}" aria-label="${place.name}${isLit ? "已点亮" : "待解锁"}">${isLit ? "碧" : ""}</span>`;
    }).join("")}</div></section>
    <section class="stamp-grid reveal" aria-label="印章点列表">
      ${places.map((place, i) => {
        const isLit = state.visitedSlugs.has(place.slug);
        return `
        <button class="stamp-card ${isLit ? "is-lit" : "is-locked"}" data-action="stamp" data-index="${i}" aria-label="${place.name}${isLit ? "已点亮" : "待解锁"}">
          <div class="stamp-scene" style="background-image: url('${placeImgUrls[place.slug] || place.cover_image_url}'); background-size: cover; background-position: center; background-repeat: no-repeat;"></div>
          <strong>${place.name}</strong>
          ${isLit ? `<span class="stamp-seal">已点亮</span>` : icon("lock", "lock-icon")}
        </button>
      `;
      }).join("")}
    </section>
    <section class="unlock-card reveal">
  <div>
    <img src="${walkImg}" alt="今日已步行" style="width:48px; height:48px; object-fit:contain; display:inline-block; vertical-align:middle; margin-right:12px;" />
    <small style="display:inline-block; vertical-align:middle;">今日已步行</small>
    <strong>2.3<em>km</em></strong>
  </div>
  <div>
    <img src="${unlockImg}" alt="解锁水岸记忆" style="width:48px; height:48px; object-fit:contain; display:inline-block; vertical-align:middle; margin-right:12px;" />
    <small style="display:inline-block; vertical-align:middle;">解锁：水岸记忆</small>
    <p>再点亮 3 个印章点，解锁专属卡片</p>
  </div>
  </section>
    <button class="primary-button wide reveal" data-route="interests">继续集章 ${icon("arrow")}</button>
  `);
}

function renderStories() {
  const categories = [
    ["村落概览", "了解碧江的历史沿革、自然环境与人文底蕴。", overviewImg, "overview"],
    ["宗祠与家风", "走进宗祠，探寻家族传承与世代相守的家风故事。", clanImg, "clan"],
    ["古桥与水岸", "古桥横跨碧波，水岸人家诉说着岁月的温柔。", watersideImg, "waterside"],
    ["诗词与巷道", "诗书传世，巷道深深，文人墨客留下足迹。", poetryImg, "poetry"],
  ];
  return shell(`
    <section class="story-hero reveal"><img src="${storyBgImg}" alt="碧江故事" /><div><h1>碧江故事</h1><p>一方水土　千年文脉</p><small>碧江村枕水而居，文脉绵长。宗祠巍峨，古桥横波，巷弄深幽，诗书传家。</small></div></section>
    
    <section class="story-category-grid reveal">
      ${categories.map(([title, copy, imgUrl, route]) => `<button class="story-category" ${route ? `data-route="${route}"` : `data-action="toast" data-message="${title}故事正在整理中"`}><span><img src="${imgUrl}" alt="${title}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" /></span><div><strong>${title}</strong><p>${copy}</p></div>${icon("arrow", "card-arrow")}</button>`).join("")}
    </section>

    <section class="story-category-grid reveal" style="grid-template-columns: 1fr;">
      <button class="story-category" data-action="toast" data-message="老码头记忆故事即将开放">
        <span><img src="${oldPierImg}" alt="老码头记忆" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" /></span>
        <div>
          <strong>老码头记忆</strong>
          <p>昔日舟往来，商贸兴旺，老码头承载着碧江的繁华记忆。</p>
        </div>
        ${icon("arrow", "card-arrow")}
      </button>
    </section>

    <section class="recommended reveal">${sectionTitle("今日推荐故事", `<button data-action="toast" data-message="更多故事正在整理中">查看全部 ${icon("arrow")}</button>`)}<article><img src="${bridgeStoryImg}" alt="一座古桥，连起几代人的时光" /><div><small>精选故事</small><h3>一座古桥，连起几代人的时光</h3><p>古桥静卧碧波之上，见证了船来人往，也见证了家族的团圆与离别。</p><span>${icon("clock")} 8 分钟阅读　|　${icon("pin")} 古桥</span></div><button class="round-button" data-action="toast" data-message="故事阅读模式即将开放" aria-label="阅读推荐故事">${icon("arrow")}</button></article></section>
  `);
}

function renderProfile() {
  const items = [
  ["我的足迹", "记录你在碧江村的探索轨迹", "已探索 8 个地点", footprintIconImg, footprintBgImg, "足迹", "查看完整足迹"],
  ["已收藏故事", "你收藏的声音与故事", "共 5 个故事", storyIconImg, collectStoryBgImg, "收藏故事", null], // 改这里
  ["历史路线", "回顾你走过的探索路线", "共 3 条路线", historyIconImg, historyBgImg, "历史路线", null],
];
  return shell(`
    <header class="simple-header reveal"><h1>我的</h1></header>
    
    <!-- ========== 顶部：游客卡片 ========== -->
    <section class="profile-card reveal" style="position:relative; overflow:hidden; min-height:200px; padding:34px; border-radius:28px; background:#edf3f5; border:1px solid #d8dde0;">
      <div style="position:relative; z-index:2; display:flex; align-items:center; gap:28px;">
        <div style="display:grid; place-items:center; width:112px; aspect-ratio:1; border-radius:50%; border:7px solid rgba(255,255,255,0.7); background:#dce7ec; overflow:hidden;">
          <img src="${profileAvatarImg}" alt="游客" style="width:100%; height:100%; object-fit:cover;" />
        </div>
        <div>
          <h2 style="margin:0; font:700 36px var(--serif);">游客</h2>
          <p style="margin-bottom:0; color:var(--muted);">今日正在探索碧江村</p>
        </div>
      </div>
      <img src="${profileBgImg}" alt="" style="position:absolute; inset:0 0 0 42%; width:58%; height:100%; object-fit:cover; opacity:0.45; mask-image:linear-gradient(90deg, transparent, #000 40%);" />
    </section>
    
    <!-- ========== 我的足迹 + 已收藏故事 ========== -->
    <section class="profile-list reveal">
      ${items.slice(0, 2).map(([title, copy, meta, iconImg, bgImg, alt, extra]) => `
        <button class="profile-item" data-action="toast" data-message="${title}详情即将开放" style="position:relative; overflow:hidden; padding:24px 30px; min-height:150px; border-radius:24px; border:1px solid var(--line); background:rgb(255 252 246 / 82%); cursor:pointer; display:grid; grid-template-columns:auto 1fr auto; gap:22px; align-items:center; text-align:left;">
          <span class="profile-icon" style="display:grid; place-items:center; width:74px; height:74px; border-radius:50%; background:#f0ebdf; overflow:hidden; flex-shrink:0; position:relative; z-index:2;">
            <img src="${iconImg}" alt="${alt}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />
          </span>
          <div style="position:relative; z-index:2;">
            <strong style="font:700 27px var(--serif); display:block;">${title}</strong>
            <p style="margin:7px 0 5px; color:var(--muted);">${copy}</p>
            ${extra ? `<small style="display:block; color:var(--gold-dark); font-weight:500; margin-bottom:6px;">${extra}</small>` : ''}
            <small style="padding:5px 13px; color:var(--blue); border-radius:999px; background:#e8f0f4;">${meta}</small>
          </div>
          <span style="position:relative; z-index:2; color:#958b7e;">${icon("arrow", "card-arrow")}</span>
          <img src="${bgImg}" alt="" style="position:absolute; inset:0 0 0 55%; width:55%; height:100%; object-fit:cover; opacity:0.3; mask-image:linear-gradient(90deg, transparent, #000 30%);" />
        </button>
      `).join("")}
    </section>
    
    <!-- ========== 设备管理 ========== -->
    <section class="device-card reveal" style="padding:28px; border:1px solid var(--line); border-radius:24px; background:#fffaf4; position:relative; overflow:hidden;">
      <div style="position:relative; z-index:2; display:flex; align-items:center; gap:16px; margin-bottom:16px;">
        <div style="display:grid; place-items:center; width:48px; height:48px; border-radius:14px; background:#eee7d8; overflow:hidden; flex-shrink:0;">
          <img src="${deviceIconImg}" alt="设备管理" style="width:100%; height:100%; object-fit:cover;" />
        </div>
        <h2 style="margin:0; font:700 27px var(--serif);">设备管理</h2>
      </div>
      <div class="device-body" style="display:grid; grid-template-columns:auto 1fr; gap:42px; align-items:center; position:relative; z-index:2;">
        <div class="pendant small" style="display:grid; place-items:center; width:100px; aspect-ratio:1; border:9px double #bdb3a3; border-radius:50%; background:linear-gradient(145deg, #f0eee7, #b6b3aa); box-shadow:0 12px 18px rgba(37,43,44,0.2); margin:0;">
          <span style="font:700 20px var(--serif);">碧江</span>
        </div>
        <div>
          <h3 style="margin:0 0 12px; font:700 24px var(--serif);">碧江寻声 · 挂件</h3>
          <p class="connected" style="padding:15px; color:#567b50; border:1px solid #d9d3c9; border-radius:16px;">已连接　电量82%　骨传导模式开启</p>
          <button data-action="toast" data-message="挂件使用指引即将开放" style="display:flex; align-items:center; justify-content:space-between; width:100%; padding:13px 18px; border:0; border-radius:14px; background:#eee8dc; cursor:pointer; font:inherit; color:inherit;">
            归还挂件指引 ${icon("arrow")}
          </button>
        </div>
      </div>
    </section>
    
    <!-- ========== 历史路线 ========== -->
    <section class="profile-list reveal">
      ${(() => {
        const [title, copy, meta, iconImg, bgImg, alt, extra] = items[2];
        return `
          <button class="profile-item" data-action="toast" data-message="${title}详情即将开放" style="position:relative; overflow:hidden; padding:24px 30px; min-height:150px; border-radius:24px; border:1px solid var(--line); background:rgb(255 252 246 / 82%); cursor:pointer; display:grid; grid-template-columns:auto 1fr auto; gap:22px; align-items:center; text-align:left;">
            <span class="profile-icon" style="display:grid; place-items:center; width:74px; height:74px; border-radius:50%; background:#f0ebdf; overflow:hidden; flex-shrink:0; position:relative; z-index:2;">
              <img src="${iconImg}" alt="${alt}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;" />
            </span>
            <div style="position:relative; z-index:2;">
              <strong style="font:700 27px var(--serif); display:block;">${title}</strong>
              <p style="margin:7px 0 5px; color:var(--muted);">${copy}</p>
              ${extra ? `<small style="display:block; color:var(--gold-dark); font-weight:500; margin-bottom:6px;">${extra}</small>` : ''}
              <small style="padding:5px 13px; color:var(--blue); border-radius:999px; background:#e8f0f4;">${meta}</small>
            </div>
            <span style="position:relative; z-index:2; color:#958b7e;">${icon("arrow", "card-arrow")}</span>
            <img src="${bgImg}" alt="" style="position:absolute; inset:0 0 0 55%; width:55%; height:100%; object-fit:cover; opacity:0.3; mask-image:linear-gradient(90deg, transparent, #000 30%);" />
          </button>
        `;
      })()}
    </section>
  `);
}

function profileItem(title, copy, meta, ico) {
  return `<button class="profile-item" data-action="toast" data-message="${title}详情即将开放"><span class="profile-icon">${icon(ico)}</span><div><strong>${title}</strong><p>${copy}</p><small>${meta}</small></div>${icon("arrow", "card-arrow")}</button>`;
}

function renderInterests() {
  const modeOptions = [
    ["relaxed", "轻松逛", "慢步游览，轻松自在"],
    ["deep", "深度走读", "深度讲解，全面了解"],
  ];
  return shell(`
    <header class="subpage-header reveal"><h1>兴趣路线</h1><p>根据你的兴趣规划游览路线</p></header>
    
    <!-- 配置面板（添加背景图） -->
    <section class="config-panel reveal" style="background-image: url('${interestBgImg}'); background-size: cover; background-position: center; background-blend-mode: overlay;">
      ${sectionTitle("选择你的兴趣")}
      <div class="interest-grid">
        ${interests.map(([name]) => `
          <button class="interest-card ${state.interests.has(name) ? "selected" : ""}" data-interest="${name}" aria-pressed="${state.interests.has(name)}">
            <span style="display:grid; place-items:center; width:64px; height:64px; border-radius:50%; background:#efe7d8; overflow:hidden;">
              <img src="${interestIconMap[name]}" alt="${name}" style="width:100%; height:100%; object-fit:cover;" />
            </span>
            <strong>${name}</strong>
            <i>${icon("check")}</i>
          </button>
        `).join("")}
      </div>
      
      ${sectionTitle("路线设置")}
      <div class="setting-block">
        <label>${icon("clock")} 游览时长</label>
        <div class="segmented">
          ${[30, 60, 90].map(n => `<button class="${state.duration === n ? "selected" : ""}" data-duration="${n}">${n}分钟</button>`).join("")}
        </div>
      </div>
      <div class="setting-block">
        <label>${icon("walk")} 探索方式</label>
        <div class="mode-grid">
          ${modeOptions.map(([value, label, sub]) => `
            <button class="${state.mode === value ? "selected" : ""}" data-mode="${value}">
              <strong>${label}</strong>
              <small>${sub}</small>
            </button>
          `).join("")}
        </div>
      </div>
      
      ${sectionTitle("路线预览")}
      <p class="preview-copy">将从碧江村 <b>${places.length}</b> 处景点中为你规划专属路线</p>
      <div class="route-preview" style="display:flex; align-items:center; gap:8px; padding:12px 16px; border:1px solid var(--line); border-radius:17px; background:#f9f4eb;">
        ${Array.from(state.interests).map(name => `<span style="font-weight:700; font-size:16px;">${name}</span>`).join(icon("arrow")) || "均衡探索"}
        <img src="${routePreviewImg}" alt="路线预览" style="width:32px; height:32px; object-fit:contain; margin-left:auto;" />
      </div>
      
      <button class="primary-button wide" data-action="generate-route" ${state.generating ? "disabled" : ""}>
        ${state.generating ? "正在规划…" : "生成我的路线"}
      </button>
    </section>
  `, { back: true, nav: false, className: "subpage" });
}

function renderRoute() {
  if (!state.route) {
    return shell(`
      <header class="subpage-header reveal"><h1>我的路线</h1><p>尚未生成专属路线</p></header>
      <button class="primary-button wide" data-route="interests">选择兴趣</button>
    `, { back: true, nav: false, className: "subpage route-view" });
  }
  const route = state.route;
  const narrationMinutes = route.stops.reduce(
    (sum, stop) => sum + Number(stop.visit_minutes || 0),
    0,
  );
  const walkingMinutes = route.legs.reduce(
    (sum, leg) => {
      const estimatedMinutes = Number(leg.estimated_minutes);
      if (estimatedMinutes > 0) return sum + estimatedMinutes;
      const distance = Number(leg.distance_meters || 0);
      return sum + (distance > 0 ? Math.max(1, Math.ceil(distance / 75)) : 0);
    },
    0,
  );
  const walkingDistance = route.legs.reduce(
    (sum, leg) => sum + Number(leg.distance_meters || 0),
    0,
  );
  const totalMinutes = narrationMinutes + walkingMinutes;
  const line = route.stops.map((stop, index) => `${index === 0 ? "M" : "L"}${stop.map_position.x} ${stop.map_position.y}`).join(" ");
  const modeLabel = route.mode === "deep" ? "深度走读" : "轻松逛";
  const routeIndex = new Map(route.stops.map((stop, index) => [stop.slug, index + 1]));
  const selectedPlace = places.find(place => place.slug === state.pendingArrival);
  const unlockedStamp = places.find(place => place.slug === state.unlockedStampSlug);
  const unlockedStampName = unlockedStamp ? escapeHtml(unlockedStamp.name) : "";
  const unlockedStampImage = unlockedStamp
    ? placeImgUrls[unlockedStamp.slug] || unlockedStamp.cover_image_url
    : "";
  const locationContent = state.realLocation
    ? `<strong>定位成功</strong><span>纬度 ${state.realLocation.latitude.toFixed(6)} · 经度 ${state.realLocation.longitude.toFixed(6)} · 误差约 ${Math.round(state.realLocation.accuracy)} 米</span>`
    : `<strong>${state.locationStatus === "loading" ? "正在获取位置" : "真实位置"}</strong><span>${state.locationMessage || "仅在本机显示，不会上传后台"}</span>`;
  return shell(`
    <header class="subpage-header reveal"><h1>我的路线</h1><p>根据您的兴趣生成的专属路线</p></header>
    <section class="location-panel reveal" data-location-status="${state.locationStatus}">
      <div>${icon("pin")}<span>${locationContent}<small>室内定位可能存在较大误差，九点游览使用下方模拟地图。</small></span></div>
      <button class="secondary-button" data-action="request-location" ${state.locationStatus === "loading" ? "disabled" : ""}>${state.realLocation ? "重新定位" : "获取我的位置"}</button>
    </section>
    <section class="route-map reveal">
  <img
    src="${villageMapUrl}"
    alt="碧江村总地图"
  />

  <svg
    class="route-line"
    viewBox="0 0 100 100"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <path d="${line}" />
  </svg>

  ${places.map(place => `
    <button
      class="map-marker ${routeIndex.has(place.slug) ? "is-route" : ""} ${state.visitedSlugs.has(place.slug) ? "is-visited" : ""} ${state.currentSimulatedSlug === place.slug ? "is-current" : ""} ${state.pendingArrival === place.slug ? "is-pending" : ""}"
      data-map-slug="${place.slug}"
      style="--x:${place.map_position.x}%; --y:${place.map_position.y}%"
      aria-label="选择${place.name}作为模拟位置"
      aria-pressed="${state.pendingArrival === place.slug}"
    >
      ${routeIndex.get(place.slug) || ""}
    </button>
  `).join("")}
</section>
    ${selectedPlace ? `<section class="arrival-confirm reveal" aria-live="polite"><div><small>${selectedPlace.zone?.name || "碧江村"}</small><strong>${selectedPlace.name}</strong><p>${selectedPlace.subtitle || "确认后将这里设为你的模拟位置。"}</p></div><div><button class="secondary-button" data-action="cancel-arrival">取消</button><button class="primary-button" data-action="confirm-arrival">模拟到达此处</button></div></section>` : ""}
    <section class="route-stats reveal"><div>${icon("clock")}<span><strong>总时长 ${totalMinutes}分钟</strong><small>${modeLabel}</small></span></div><div>${icon("book")}<span><strong>讲解 ${narrationMinutes}分钟</strong><small>${route.stops.length}个故事点 · 评分 ${route.score}</small></span></div><div>${icon("walk")}<span><strong>步行 ${walkingMinutes}分钟</strong><small>${walkingDistance}米</small></span></div></section>
    <section class="route-stop-list reveal">
      ${route.stops.map((stop, index) => `<article class="route-stop"><span>${index + 1}</span><div><strong>${stop.name}</strong><small>${stop.zone.name} · ${stop.visit_minutes}分钟讲解</small><p>${stop.recommendation}</p></div></article>${route.legs[index] ? `<p class="route-bridge">${route.legs[index].narrative_bridge}</p>` : ""}`).join("")}
    </section>
    <p class="route-note reveal">点击地图上的任意景点，确认后即可更新模拟位置；偏离推荐路线时会从新位置重新规划。</p>
    ${unlockedStamp ? `
      <div class="stamp-unlock-backdrop" data-dismiss-stamp-unlock>
        <section class="stamp-unlock-dialog" role="dialog" aria-modal="true" aria-labelledby="stamp-unlock-title">
          <button class="stamp-unlock-close" data-action="close-stamp-unlock" aria-label="关闭邮章提示">&times;</button>
          <div class="stamp-unlock-art">
            <img src="${escapeHtml(unlockedStampImage)}" alt="${unlockedStampName}邮章" />
            <span>已点亮</span>
          </div>
          <small>集章寻迹</small>
          <h2 id="stamp-unlock-title">恭喜你已点亮</h2>
          <strong>「${unlockedStampName}」邮章</strong>
          <p>这枚邮章已收入你的集章册。</p>
        </section>
      </div>
    ` : ""}
  `, { back: true, nav: false, className: "subpage route-view" });
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function renderAttractionDetail() {
  if (state.detailLoading || !state.attractionDetail) {
    return shell(`<section class="detail-loading"><strong>正在读取故事…</strong></section>`, { back: true, nav: false, className: "subpage" });
  }
  const attraction = state.attractionDetail;
  const story = attraction.story;
  const paragraphs = story?.full_text?.split(/\n\s*\n/).filter(Boolean) || [];
  return shell(`
    <section class="dynamic-story-hero reveal">
      <img src="${attraction.cover_image_url}" alt="${escapeHtml(attraction.name)}" />
      <div><small>${escapeHtml(attraction.zone.name)}</small><h1>${escapeHtml(attraction.name)}</h1><p>${escapeHtml(attraction.subtitle)}</p></div>
    </section>
    <button class="primary-button wide reveal" data-action="favorite-current">收藏这个故事</button>
    ${story ? `<article class="dynamic-story-body reveal"><blockquote>${escapeHtml(story.fun_fact)}</blockquote>${paragraphs.map(paragraph => `<p>${escapeHtml(paragraph)}</p>`).join("")}</article>` : `<p class="route-note">故事内容正在整理</p>`}
  `, { back: true, nav: false, className: "story-detail-page dynamic-story-page" });
}

function renderOverview() {
  const labels = [
    ["1", "村史馆", 42, 13], ["2", "碧溪书公祠", 69, 17], ["3", "黄氏宗祠", 14, 31],
    ["4", "东氏宗祠", 77, 40], ["5", "古桥", 50, 45], ["6", "诗词巷", 21, 54],
    ["7", "绣西彭公祠", 27, 73], ["8", "老码头", 68, 62], ["9", "水岸古树", 79, 79],
  ];
  const features = [
    ["宗祠文化", "多座宗祠保存完好，木雕、砖雕与石雕工艺精湛，承载家族记忆。", "building", 58],
    ["诗礼传家", "诗词巷书香氤氲，文风鼎盛，代代重教崇文，耕读传家。", "book", 22],
    ["水乡风貌", "河涌环绕，古桥相连，舟楫往来，尽显岭南水乡灵动之美。", "route", 48],
    ["古树成荫", "古树临水而立，岁月静好，见证古村生生不息。", "leaf", 76],
  ];
  return shell(`
    <section class="content-hero overview-content-hero reveal">
      <div class="content-hero-copy"><h1>村落概览</h1><p>水网古村，诗礼人家</p><small>依水而生，因水而兴，千年文脉绵延，古祠流芳，诗礼传家。</small></div>
      <img src="${villageMapUrl}" alt="碧江村水网古村风貌" />
    </section>
    <section class="overview-stat-grid reveal">
      <article>${icon("pin")}<h2>村落位置</h2><p>广东省佛山市顺德区<br>北滘镇碧江社区</p><div class="mini-map-mark">${icon("pin")}</div></article>
      <article>${icon("building")}<h2>历史脉络</h2><p>始建千宋，兴于明清。书香门第，耕读传家；古祠、古桥、古巷与水岸相依。</p></article>
      <article>${icon("leaf")}<h2>村落特色</h2><p>宗祠文化深厚，诗礼传统悠久，水网交织，古树成荫，岭南风格建筑错落有致。</p></article>
    </section>
    <section class="detail-section village-layout reveal">
      <div class="detail-heading"><h2>村落格局</h2><p>九点点缀古村，水脉串联人文，一步一景，皆是故事。</p></div>
      <div class="overview-map"><img src="${villageMapUrl}" alt="碧江村九处人文景点地图" />${labels.map(([n, name, x, y]) => `<button data-action="toast" data-message="${name}导览已定位" style="--x:${x}%;--y:${y}%"><b>${n}</b>${name}</button>`).join("")}</div>
    </section>
    <section class="heritage-grid reveal">${features.map(([title, copy, ico, pos]) => `<article><div class="heritage-image" style="--pos:${pos}%"><span>${icon(ico)}</span></div><h2>${title}</h2><p>${copy}</p></article>`).join("")}</section>
  `, { back: true, className: "story-detail-page overview-page" });
}

function renderClan() {
  const keywords = [["敬祖", "梅"], ["睦族", "竹"], ["崇文", "书"], ["勤学", "兰"], ["诚信", "石"], ["仁厚", "荷"]];
  const halls = [
    ["黄氏宗祠", "始建于清乾隆年间，坐北朝南，三进两天井。祠内保存完好，堂号“德馨堂”。", 50, "ancestral"],
    ["东氏宗祠", "建于清嘉庆年间，气势庄重，厅堂宽敞。重视家训传承，历代族人耕读传家。", 42],
    ["碧溪书公祠", "为纪念开村先贤碧溪书公而建，寄托后人饮水思源之情。", 66],
  ];
  return shell(`
    <section class="content-hero clan-content-hero reveal">
      <div class="content-hero-copy"><h1>宗祠与家风</h1><p>宗祠立村，家训传世</p></div>
      <img src="${ancestralHallUrl}" alt="碧江村临水宗祠" />
    </section>
    <section class="detail-section intro-split reveal">
      <div><div class="detail-heading"><h2>宗祠与家风简介</h2></div><p>碧江村依水而居，宗祠文化源远流长。黄氏、东氏等宗族在此建祠立堂，敬祖睦族、崇文重教，形成了独具特色的家风传统。</p><p>祠堂不仅是祭祀先祖、凝聚族人的精神家园，更是传承家训、涵养品德的重要载体，滋养了一代又一代碧江人。</p></div>
      <img src="${villageMapUrl}" alt="古桥与水乡村落" />
    </section>
    <section class="detail-section reveal">${sectionTitle("家风关键词")}<div class="keyword-grid">${keywords.map(([word, art]) => `<article><strong>${word}</strong><span>${art}</span></article>`).join("")}</div></section>
    <section class="detail-section reveal">${sectionTitle("宗祠风采")}<div class="shrine-grid">${halls.map(([title, copy, pos, route]) => `<button ${route ? `data-route="${route}"` : `data-action="toast" data-message="${title}详情正在整理中"`}><div class="shrine-image" style="--pos:${pos}%"></div><h3>${title}</h3><p>${copy}</p>${icon("arrow", "card-arrow")}</button>`).join("")}</div></section>
    <blockquote class="family-quote reveal"><strong>家训摘录</strong><p>敬祖如在，睦族如家；崇文尚德，勤学立身；<br>诚信守己，仁厚待人；清白传家，世代荣昌。</p><cite>—— 碧江村历代家训</cite></blockquote>
  `, { back: true, className: "story-detail-page clan-page" });
}

function renderWaterside() {
  const topics = [
    ["古桥", "碧江古桥多建于明清，石拱如虹，连接两岸村落与市集。", 47],
    ["老码头", "昔日商船停靠之地，货物在此装卸，人流在此集散。", 67],
    ["水岸古树", "古树扎根水岸，枝叶荫护村落，陪伴柳畔人家。", 74],
    ["水岸生活", "浣衣、洗菜、摇橹、闲聊，水岸生活质朴悠然。", 28],
    ["水路交通", "碧江水系纵横，舟楫往来不绝，沟通乡里与远方。", 12],
  ];
  return shell(`
    <section class="waterside-title reveal"><h1>古桥与水岸</h1><p>桥连两岸，水养村落</p></section>
    <section class="waterside-scene reveal"><img src="${villageMapUrl}" alt="碧江古桥与水岸风貌" /></section>
    <p class="lead-copy reveal">碧江因水而兴，依水而居。古桥横跨碧江，老码头连通四方，水岸古树见证岁月，水岸生活烟火绵长，水路交通贯通千年。</p>
    <section class="waterside-topic-grid reveal">${topics.map(([title, copy, pos]) => `<article><h2>${title}</h2><div style="--pos:${pos}%"></div><p>${copy}</p></article>`).join("")}</section>
    <section class="detail-section waterside-clue reveal"><div><div class="detail-heading"><h2>水岸线索</h2></div><div class="clue-map"><img src="${villageMapUrl}" alt="古桥至码头的水岸探索线索" /><svg viewBox="0 0 100 45" preserveAspectRatio="none" aria-hidden="true"><path d="M12 15 C25 5 36 34 50 24 S73 10 88 31"/></svg><span style="--x:12%;--y:32%">古桥</span><span style="--x:36%;--y:65%">老码头</span><span style="--x:55%;--y:54%">水岸古树</span><span style="--x:74%;--y:34%">水岸生活</span><span style="--x:88%;--y:68%">水路交通</span></div></div><p>沿着碧江的水脉行走，从一座桥到一处码头，从一棵古树到一段生活，串联起水乡的历史与日常。</p></section>
    <section class="fact-panel reveal"><h2>你知道吗</h2><ul><li>碧江古桥多为石拱结构，既坚固又美观，桥洞弧度有助于洪水通行。</li><li>老码头曾是水上丝绸之路的支点，来自各地的商船在此停泊交易。</li><li>水岸古树根系发达，能稳固岸土、防风护岸。</li><li>水路交通是碧江人世代的出行方式，也是连接外界的重要通道。</li></ul></section>
  `, { back: true, className: "story-detail-page waterside-page" });
}

function renderPoetry() {
  const details = [
    ["门楼风韵", "门楼高耸，匾额楹联诉说家风与荣耀。", "building", 46],
    ["灰塑匠心", "灰塑人物栩栩如生，岭南风俗跃然墙头。", "user", 56],
    ["砖雕寄意", "花鸟虫鱼、吉祥纹样，寓情于物，匠心独运。", "stamp", 35],
    ["水巷转角", "转角处水波轻漾，见证岁月与人家的故事。", "route", 18],
  ];
  return shell(`
    <section class="content-hero poetry-content-hero reveal">
      <div class="content-hero-copy"><h1>诗词与巷道</h1><p>巷陌深深，文脉悠悠</p><small>碧江村，水绕古巷，文风绵长。一砖一瓦皆故事，一巷一诗总关情。</small></div>
      <img src="${ancestralHallUrl}" alt="碧江古巷与门楼" />
    </section>
    <section class="poetry-band reveal"><div class="poetry-object">${icon("book")}</div><div><h2>碧江村的诗词记忆</h2><p>自古文风鼎盛，村中书院、私塾林立，文人墨客往来不绝，留下大量诗词题咏。</p><p>从门楼楹联到巷道题刻，诗意早已融入村落的每一寸肌理。</p></div><div class="band-image" style="--pos:65%"></div></section>
    <section class="poetry-band reverse reveal"><div class="band-image" style="--pos:16%"></div><div><h2>巷道漫游</h2><p>从碧水桥起，沿青石板路徐行，曲巷通幽，水巷相依。</p><p>每一次转角，都是时光的低语；每一条小巷，都藏着一首旧诗。</p></div></section>
    <section class="detail-section reveal">${sectionTitle("可留意的细节")}<div class="poetry-detail-grid">${details.map(([title, copy, ico, pos]) => `<article><div style="--pos:${pos}%"><span>${icon(ico)}</span></div><h3>${title}</h3><p>${copy}</p></article>`).join("")}</div></section>
    <section class="today-story reveal"><div><h2>今日小故事</h2><h3>一副对联的守望</h3><p>据说村中某门楼的对联，乃一位归乡秀才所题。上联“诗书继世长”，下联“孝悌传家远”，百年来风雨不改，仍静静守护着这户人家的门庭。</p></div><div class="story-door" aria-hidden="true">诗礼传家</div></section>
  `, { back: true, className: "story-detail-page poetry-page" });
}

function renderAncestral() {
  return shell(`
    <header class="detail-brand reveal"><span class="brand-mark">碧</span><span>碧溪古村<small>探索版</small></span><h1>黄氏宗祠</h1></header>
    <section class="ancestral-hero reveal"><img src="${ancestralHallUrl}" alt="黄氏宗祠水墨画" /><span>宗祠 · 黄氏宗祠</span></section>
    <section class="audio-card reveal"><div><h2>正在聆听：宗祠的来历</h2><button class="voice-switch" data-action="toast" data-message="已切换为温柔女声讲解">${icon("volume")} 切换语音讲解</button></div><div class="waveform ${state.audioPlaying ? "playing" : ""}" aria-hidden="true">${Array.from({length: 32}, (_, i) => `<i style="--h:${20 + (i * 17) % 62}%"></i>`).join("")}</div><div class="audio-controls"><span>${formatTime(Math.round(298 * state.audioProgress / 100))}</span><input type="range" min="0" max="100" value="${state.audioProgress}" aria-label="讲解进度" data-audio-range><span>04:58</span><button class="play-button" data-action="toggle-audio" aria-label="${state.audioPlaying ? "暂停" : "播放"}">${icon(state.audioPlaying ? "pause" : "play")}</button></div></section>
    <section class="detail-list reveal">
      ${[["建筑细节", "探索宗祠的结构布局与精美工艺", "building"], ["人物故事", "聆听黄氏家族的传承与往事", "user"], ["继续寻找下一个线索", "前往下一处地点，解锁更多故事", "pin"]].map(([title, sub, ico]) => `<button data-action="toast" data-message="${title}内容即将展开"><span>${icon(ico)}</span><div><strong>${title}</strong><small>${sub}</small></div>${icon("arrow", "card-arrow")}</button>`).join("")}
    </section>
    <p class="sensor-note reveal">${icon("volume")} 靠近音频点或触碰感应点，故事将自动为您开启</p>
  `, { back: true, nav: false, className: "subpage ancestral-view" });
}

function formatTime(seconds) {
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

const renders = { home: renderHome, stamps: renderStamps, stories: renderStories, profile: renderProfile, interests: renderInterests, route: renderRoute, attraction: renderAttractionDetail, ancestral: renderAncestral, overview: renderOverview, clan: renderClan, waterside: renderWaterside, poetry: renderPoetry };
let toastTimer;
let audioTimer;
let destroyed = false;

function render() {
  app.innerHTML = renders[state.view]();
  const attractionTitle = state.attractionDetail?.name || "景点故事";
  document.title = `${({home:"首页",stamps:"集章寻迹",stories:"碧江故事",profile:"我的",interests:"兴趣路线",route:"我的路线",attraction:attractionTitle,ancestral:"黄氏宗祠",overview:"村落概览",clan:"宗祠与家风",waterside:"古桥与水岸",poetry:"诗词与巷道"})[state.view]} · 碧江寻迹`;
  const stampBackdrop = app.querySelector("[data-dismiss-stamp-unlock]");
  if (stampBackdrop) {
    const main = stampBackdrop.closest("main");
    const shell = stampBackdrop.closest(".app-shell");
    for (const child of main?.children || []) {
      if (child !== stampBackdrop) child.setAttribute("inert", "");
    }
    for (const child of shell?.children || []) {
      if (child !== main) child.setAttribute("inert", "");
    }
    queueMicrotask(() => {
      if (state.unlockedStampSlug) {
        stampBackdrop.querySelector("[data-action='close-stamp-unlock']")?.focus();
      }
    });
  }
}

function transition(update) {
  if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(update);
  else update();
}

function navigate(view, replace = false) {
  if (!validViews.has(view) || view === state.view) return;
  state.view = view;
  history[replace ? "replaceState" : "pushState"]({ view }, "", `#${view}`);
  transition(() => { render(); scrollTo({ top: 0, behavior: "instant" }); });
}

function showToast(message) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("show");
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2200);
}

function closeStampUnlock() {
  const unlockedSlug = state.unlockedStampSlug;
  if (!unlockedSlug) return;
  state.unlockedStampSlug = null;
  transition(() => {
    render();
    queueMicrotask(() => {
      const marker = Array.from(app.querySelectorAll("[data-map-slug]"))
        .find(item => item.dataset.mapSlug === unlockedSlug);
      marker?.focus();
    });
  });
}

async function initializeData() {
  try {
    await ensureVisitorSession();
    const data = await getBootstrap();
    if (destroyed) return;
    interests = data.themes.map(theme => [theme.name, theme.icon]);
    places = data.attractions;
    const validInterests = new Set(data.themes.map(theme => theme.name));
    state.interests = new Set(Array.from(state.interests).filter(name => validInterests.has(name)));
    if (!state.interests.size) data.themes.slice(0, 2).forEach(theme => state.interests.add(theme.name));
  } catch (error) {
    console.warn('API请求失败，使用模拟数据:', error.message);
    // ========== 模拟数据（兴趣路线） ==========
  interests = [
   ["古建筑", "building"],
   ["宗族故事", "book"],
   ["人物旧居", "home"],
   ["诗词记忆", "book"],
   ["巷道漫游", "route"],
   ["民俗生活", "leaf"],
   ["水岸风景", "map"],
   ["亲子体验", "user"]
  ];

 state.interests = new Set(["古建筑", "宗族故事"]);
        
    places = [
  { 
    slug: "village-history-museum", 
    name: "村史馆", 
    zone: { name: "村史区" },
    map_position: { x: 42, y: 13 },
    tags: ["民俗生活", "人物旧居"],
    cover_image_url: placeImgUrls["village-history-museum"]
  },
  { 
    slug: "bixi-scholar-hall", 
    name: "碧溪书公祠", 
    zone: { name: "宗祠区" },
    map_position: { x: 69, y: 17 },
    tags: ["古建筑", "诗词记忆"],
    cover_image_url: placeImgUrls["bixi-scholar-hall"]
  },
  { 
    slug: "huang-ancestral-hall", 
    name: "黄氏宗祠", 
    zone: { name: "宗祠区" },
    map_position: { x: 14, y: 31 },
    tags: ["古建筑", "宗族故事"],
    cover_image_url: placeImgUrls["huang-ancestral-hall"]
  },
  { 
    slug: "dong-ancestral-hall", 
    name: "东氏宗祠", 
    zone: { name: "宗祠区" },
    map_position: { x: 77, y: 40 },
    tags: ["古建筑", "宗族故事"],
    cover_image_url: placeImgUrls["dong-ancestral-hall"]
  },
  { 
    slug: "ancient-bridge", 
    name: "古桥", 
    zone: { name: "水岸区" },
    map_position: { x: 50, y: 45 },
    tags: ["水岸风景", "巷道漫游"],
    cover_image_url: placeImgUrls["ancient-bridge"]
  },
  { 
    slug: "poetry-lane", 
    name: "诗词巷", 
    zone: { name: "巷道区" },
    map_position: { x: 21, y: 54 },
    tags: ["诗词记忆", "巷道漫游"],
    cover_image_url: placeImgUrls["poetry-lane"]
  },
  { 
    slug: "xiuxi-peng-ancestral-hall", 
    name: "绣西彭公祠", 
    zone: { name: "宗祠区" },
    map_position: { x: 27, y: 73 },
    tags: ["古建筑", "人物旧居"],
    cover_image_url: placeImgUrls["xiuxi-peng-ancestral-hall"]
  },
  { 
    slug: "old-wharf", 
    name: "老码头", 
    zone: { name: "水岸区" },
    map_position: { x: 68, y: 62 },
    tags: ["水岸风景", "民俗生活"],
    cover_image_url: placeImgUrls["old-wharf"]
  },
  { 
    slug: "waterside-ancient-tree", 
    name: "水岸古树", 
    zone: { name: "水岸区" },
    map_position: { x: 79, y: 79 },
    tags: ["水岸风景", "亲子体验"],
    cover_image_url: placeImgUrls["waterside-ancient-tree"]
  }
];  

    // 确保兴趣选择有效
    const validNames = new Set(interests.map(([name]) => name));
    state.interests = new Set(Array.from(state.interests).filter(name => validNames.has(name)));
    if (!state.interests.size) {
      state.interests.add("岭南建筑");
      state.interests.add("诗书文脉");
    }
  } finally {
    state.bootstrapReady = true;
    if (!destroyed) transition(render);
  }
}

async function initializeLocalVoices() {
  try {
    state.localVoices = await getLocalVoices();
    state.localVoicesError = "";
  } catch (error) {
    console.warn("当地声音加载失败:", error.message);
    state.localVoices = [];
    state.localVoicesError = "当地声音暂时无法加载";
  } finally {
    state.localVoicesLoading = false;
    if (!destroyed && state.view === "stories") transition(render);
  }
}

function reportBehavior(promise) {
  promise.catch(error => console.warn('behavior record failed', error.message));
}

const routeCorridors = [
  ["ancient-bridge", "village-history-museum", "huang-ancestral-hall"],
  ["ancient-bridge", "poetry-lane", "xiuxi-peng-ancestral-hall"],
  ["ancient-bridge", "bixi-scholar-hall"],
  ["ancient-bridge", "dong-ancestral-hall", "old-wharf", "waterside-ancient-tree"],
];

const routeNeighbors = new Map();
for (const corridor of routeCorridors) {
  for (let index = 0; index < corridor.length - 1; index += 1) {
    const first = corridor[index];
    const second = corridor[index + 1];
    routeNeighbors.set(first, [...(routeNeighbors.get(first) || []), second]);
    routeNeighbors.set(second, [...(routeNeighbors.get(second) || []), first]);
  }
}

function itineraryReference(route = state.route) {
  return Number.isInteger(route?.id) ? { itinerary_id: route.id } : {};
}

function buildLocalRoute({
  startSlug = "village-history-museum",
  visitedSlugs = [],
} = {}) {
  const selectedInterests = Array.from(state.interests);
  const visitedSet = new Set(visitedSlugs);

  // 根据游览时间决定景点数量
  const stopCount =
    state.duration <= 30
      ? 3
      : state.duration <= 60
        ? 4
        : 5;

  const availablePlaces = new Map(
    places
      .filter(place => !visitedSet.has(place.slug) || place.slug === startSlug)
      .map(place => [place.slug, place]),
  );
  const startPlace = availablePlaces.get(startSlug);
  const placeScore = place => 1 + (place.tags || []).filter(
    tag => selectedInterests.includes(tag),
  ).length * 10;
  let bestRoute = startPlace ? [startPlace] : [];
  let bestScore = startPlace ? placeScore(startPlace) : 0;

  function searchLocalRoute(route, score) {
    if (
      score > bestScore ||
      (score === bestScore && route.length > bestRoute.length)
    ) {
      bestRoute = [...route];
      bestScore = score;
    }
    if (route.length >= stopCount) return;

    const usedSlugs = new Set(route.map(place => place.slug));
    for (const neighborSlug of routeNeighbors.get(route.at(-1).slug) || []) {
      const neighbor = availablePlaces.get(neighborSlug);
      if (!neighbor || usedSlugs.has(neighborSlug)) continue;
      searchLocalRoute([...route, neighbor], score + placeScore(neighbor));
    }
  }

  if (startPlace) searchLocalRoute([startPlace], placeScore(startPlace));
  const finalPlaces = bestRoute.length ? bestRoute : places.slice(0, 1);

  const visitMinutes = Math.max(
    12,
    Math.floor(state.duration / Math.max(finalPlaces.length, 1))
  );

  const stops = finalPlaces.map((place, index) => ({
    slug: place.slug,
    name: place.name,
    subtitle: place.subtitle || "",
    zone: {
      name: place.zone?.name || "碧江村",
    },
    visit_minutes: visitMinutes,
    map_position: place.map_position || {
      x: 18 + index * 15,
      y: 18 + index * 14,
    },
    recommendation:
      place.recommendation ||
      `探索「${place.name}」，感受 ${
        Array.isArray(place.tags) && place.tags.length
          ? place.tags.join("、")
          : "碧江古村文化"
      }的独特魅力。`,
  }));

  // legs 的数量应比 stops 少一个
  const legs = stops.slice(0, -1).map((stop, index) => {
    const nextStop = stops[index + 1];
    const dx = (Number(nextStop.map_position?.x || 0) - Number(stop.map_position?.x || 0)) * 7;
    const dy = (Number(nextStop.map_position?.y || 0) - Number(stop.map_position?.y || 0)) * 7;
    const distance = Math.max(80, Math.round(Math.hypot(dx, dy) / 10) * 10);
    return {
      distance_meters: distance,
      estimated_minutes: Math.max(1, Math.ceil(distance / 75)),
      narrative_bridge:
        index % 2 === 0
          ? "沿碧水前行，不远处便是下一处风景。"
          : "穿过古巷，下一段村落故事正在前方等待。",
    };
  });
  const walkingMinutes = legs.reduce((sum, leg) => sum + leg.estimated_minutes, 0);
  const narrationMinutes = stops.reduce((sum, stop) => sum + stop.visit_minutes, 0);

  return {
    id: `local-route-${Date.now()}`,
    stops,
    legs,
    total_estimated_minutes: narrationMinutes + walkingMinutes,
    score: 4.8,
    mode: state.mode,
    isLocalDemo: true,
  };
}

async function createRoute() {
  if (state.generating) return;

  if (!places.length) {
    showToast("景点数据尚未加载，请稍后再试");
    return;
  }

  state.generating = true;
  transition(render);

  const requestData = {
    preference_tags: Array.from(state.interests),
    duration_minutes: state.duration,
    mode: state.mode,
    start_attraction_slug: "village-history-museum",
  };

  try {
    // 优先请求真实后台
    state.route = await generateItinerary(requestData);

    reportBehavior(
      recordEvent("generate_route", {
        ...itineraryReference(state.route),
        metadata: {
          preference_tags: requestData.preference_tags,
          duration_minutes: requestData.duration_minutes,
          mode: requestData.mode,
          source: "api",
        },
      })
    );
  } catch (error) {
    console.warn("API生成路线失败，改用本地演示路线：", error);

    // 请求失败时生成本地路线，不再中断
    state.route = buildLocalRoute({
      startSlug: requestData.start_attraction_slug,
    });

    showToast("后台暂时无法连接，已生成本地演示路线");

    reportBehavior(
      recordEvent("generate_route", {
        ...itineraryReference(state.route),
        metadata: {
          preference_tags: requestData.preference_tags,
          duration_minutes: requestData.duration_minutes,
          mode: requestData.mode,
          source: "local_fallback",
          api_error: error?.message || "请求失败",
        },
      })
    );
  } finally {
    state.generating = false;
  }

  // 无论真实请求还是本地生成成功，都保存并跳转
  if (state.route?.stops?.length) {
    persistDemoState();
    navigate("route");
  } else {
    showToast("暂时无法生成路线，请重新选择兴趣");
    transition(render);
  }
}

function requestRealLocation() {
  if (!navigator.geolocation) {
    state.locationStatus = "error";
    state.locationMessage = "当前浏览器不支持定位";
    transition(render);
    return;
  }
  state.locationStatus = "loading";
  state.locationMessage = "请在系统提示中允许定位";
  transition(render);
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      state.realLocation = {
        latitude: coords.latitude,
        longitude: coords.longitude,
        accuracy: coords.accuracy,
      };
      state.locationStatus = "success";
      state.locationMessage = "";
      transition(render);
    },
    (error) => {
      const messages = {
        1: "你已拒绝定位权限，仍可使用模拟导览",
        2: "暂时无法获取位置，请检查系统定位开关",
        3: "定位请求超时，请稍后重试",
      };
      state.locationStatus = "error";
      state.locationMessage = messages[error.code] || "定位失败，请稍后重试";
      transition(render);
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
  );
}

async function confirmSimulatedArrival() {
  const slug = state.pendingArrival;
  if (!slug) return;
  const isOffRoute = !state.route?.stops.some(stop => stop.slug === slug);
  const isFirstVisit = !state.visitedSlugs.has(slug);
  const previousRoute = state.route;
  state.currentSimulatedSlug = slug;
  state.visitedSlugs.add(slug);
  if (isFirstVisit) state.unlockedStampSlug = slug;
  state.pendingArrival = null;
  persistDemoState();
  transition(render);

  let eventSynced = true;
  try {
    await recordEvent('simulated_arrival', {
      attraction_slug: slug,
      ...itineraryReference(),
      metadata: { source: 'manual_map' },
    });
  } catch (error) {
    eventSynced = false;
    console.warn("模拟到达事件同步失败：", error);
  }

  if (isOffRoute) {
    const requestData = {
      preference_tags: Array.from(state.interests),
      duration_minutes: state.duration,
      mode: state.mode,
      start_attraction_slug: slug,
      visited_attraction_slugs: Array.from(state.visitedSlugs),
    };

    try {
      const replannedRoute = await generateItinerary(requestData);
      if (!replannedRoute?.stops || replannedRoute.stops.length < 2) {
        throw new Error("暂无可用剩余路线");
      }
      state.route = replannedRoute;
      showToast(eventSynced ? "已从当前位置重新规划路线" : "已重新规划，足迹稍后同步");
    } catch (error) {
      console.warn("后台重新规划失败，使用本地路线：", error);
      const localRoute = buildLocalRoute({
        startSlug: slug,
        visitedSlugs: Array.from(state.visitedSlugs),
      });
      if (localRoute?.stops?.length > 1) {
        state.route = localRoute;
        showToast("后台暂时无法连接，已在本地重新规划");
      } else {
        state.route = previousRoute;
        showToast("当前位置已保留，暂无可用剩余路线，请调整时长或兴趣");
      }
    }
    persistDemoState();
    transition(render);
  } else {
    showToast(eventSynced ? "已记录模拟到达" : "位置已保留，足迹稍后同步");
  }
}

async function openAttraction(slug) {
  state.selectedAttraction = slug;
  state.attractionDetail = null;
  state.detailLoading = true;
  if (state.view === "attraction") transition(render);
  else navigate("attraction");
  try {
    state.attractionDetail = await getAttraction(slug);
    reportBehavior(recordEvent('view_attraction', {
      attraction_slug: slug,
      ...itineraryReference(),
    }));
  } catch (error) {
    showToast(`故事加载失败：${error.message}`);
  } finally {
    state.detailLoading = false;
    if (!destroyed && state.view === "attraction") transition(render);
  }
}

const handleClick = (event) => {
  const route = event.target.closest("[data-route]");
  if (route) { event.preventDefault(); navigate(route.dataset.route); return; }
  const stampBackdrop = event.target.closest("[data-dismiss-stamp-unlock]");
  if (stampBackdrop && event.target === stampBackdrop) {
    closeStampUnlock();
    return;
  }
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.mapSlug) {
    state.pendingArrival = button.dataset.mapSlug;
    transition(render);
    return;
  }
  if (button.dataset.attractionSlug) { void openAttraction(button.dataset.attractionSlug); return; }
  if (button.dataset.interest) {
    state.interests.has(button.dataset.interest) ? state.interests.delete(button.dataset.interest) : state.interests.add(button.dataset.interest);
    persistDemoState(); transition(render); return;
  }
  if (button.dataset.duration) { state.duration = Number(button.dataset.duration); persistDemoState(); transition(render); return; }
  if (button.dataset.mode) { state.mode = button.dataset.mode; persistDemoState(); transition(render); return; }
  if (button.dataset.action === "generate-route") { void createRoute(); return; }
  if (button.dataset.action === "request-location") { requestRealLocation(); return; }
  if (button.dataset.action === "cancel-arrival") { state.pendingArrival = null; transition(render); return; }
  if (button.dataset.action === "close-stamp-unlock") { closeStampUnlock(); return; }
  if (button.dataset.action === "confirm-arrival") { void confirmSimulatedArrival(); return; }
  if (button.dataset.action === "favorite-current") {
    const slug = state.attractionDetail?.slug || state.selectedAttraction;
    if (slug) {
      reportBehavior(recordFavorite(slug));
      reportBehavior(recordEvent('favorite_story', { attraction_slug: slug }));
      showToast("已收藏故事");
    }
    return;
  }
  if (button.dataset.action === "back") { history.length > 1 ? history.back() : navigate("home", true); return; }
  if (button.dataset.action === "toggle-audio") {
    state.audioPlaying = !state.audioPlaying;
    if (state.audioPlaying) {
      reportBehavior(recordEvent('audio_play', {
        attraction_slug: state.selectedAttraction || 'huang-ancestral-hall',
        ...itineraryReference(),
        metadata: { progress: state.audioProgress },
      }));
    }
    clearInterval(audioTimer);
    if (state.audioPlaying) audioTimer = setInterval(() => {
      state.audioProgress = Math.min(100, state.audioProgress + 0.34);
      const range = document.querySelector("[data-audio-range]");
      if (range) range.value = state.audioProgress;
      if (state.audioProgress >= 100) { state.audioPlaying = false; clearInterval(audioTimer); render(); }
    }, 1000);
    transition(render); return;
  }
  if (button.dataset.action === "stamp") {
    const place = places[Number(button.dataset.index)];
    if (place?.slug && Number.isInteger(state.route?.id)) {
      reportBehavior(recordFootprint({
        itinerary_id: state.route.id,
        attraction_slug: place.slug,
        audio_played: state.audioProgress >= 95,
      }));
    } else if (place?.slug) {
      reportBehavior(recordEvent('stamp_click', { attraction_slug: place.slug }));
    }
    showToast(button.classList.contains("is-lit") ? "这个印章已经点亮" : "到达景点后即可解锁");
    return;
  }
  if (button.dataset.action === "toast") showToast(button.dataset.message || "功能即将开放");
};

const handleInput = (event) => {
  if (event.target.matches("[data-audio-range]")) state.audioProgress = Number(event.target.value);
};

const handleKeydown = (event) => {
  if (!state.unlockedStampSlug) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeStampUnlock();
    return;
  }
  if (event.key === "Tab") {
    const closeButton = app.querySelector("[data-action='close-stamp-unlock']");
    if (closeButton) {
      event.preventDefault();
      closeButton.focus();
    }
  }
};

function syncLocation() {
  const next = location.hash.slice(1) || "home";
  const view = validViews.has(next) ? next : "home";
  if (view === state.view) return;
  state.view = view;
  transition(() => { render(); scrollTo({ top: 0, behavior: "instant" }); });
}

app.addEventListener("click", handleClick);
app.addEventListener("input", handleInput);
window.addEventListener("keydown", handleKeydown);
window.addEventListener("popstate", syncLocation);
window.addEventListener("hashchange", syncLocation);

render();
void initializeData();
void initializeLocalVoices();

return () => {
  destroyed = true;
  clearTimeout(toastTimer);
  clearInterval(audioTimer);
  app.removeEventListener("click", handleClick);
  app.removeEventListener("input", handleInput);
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("popstate", syncLocation);
  window.removeEventListener("hashchange", syncLocation);
};
}
