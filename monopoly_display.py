#!/usr/bin/env python3
"""涩涩大富翁棋盘展示服务

用法：
  python3 monopoly_display.py

环境变量：
  MONOPOLY_API_URL   游戏API地址（默认 http://127.0.0.1:8000）
  MONOPOLY_TOKEN     玩家token（默认 guiwan）
  PORT               监听端口（默认 8896）
"""

import os, json, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

API_URL = os.environ.get("MONOPOLY_API_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN   = os.environ.get("MONOPOLY_TOKEN", "guiwan")
PORT    = int(os.environ.get("PORT", 8896))

TILE_TYPES = {
    0:"start",1:"task",2:"task",3:"task",4:"truth",5:"chance",
    6:"task",7:"task",8:"mystery",9:"task",10:"jail",11:"task",
    12:"shop",13:"task",14:"truth",15:"chance",16:"task",
    17:"mystery",18:"task",19:"shop"
}
TILE_ICONS  = {"start":"🏁","task":"🎯","truth":"💬","chance":"🎴","mystery":"❓","jail":"🔒","shop":"🛒"}
TILE_LABELS = {"start":"出发","task":"任务","truth":"真心话","chance":"抽卡","mystery":"神秘","jail":"监狱","shop":"商店"}
GP = [[5,5],[5,4],[5,3],[5,2],[5,1],[5,0],[4,0],[3,0],[2,0],[1,0],
      [0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,5],[2,5],[3,5],[4,5]]

def api(path, **params):
    url = API_URL + path
    if params:
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k,v in params.items())
        url += "?" + qs
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None

import urllib.parse

def get_games():
    r = api("/games", player_token=TOKEN)
    if not r: return []
    return r.get("games", [])

def get_state(game_id):
    r = api(f"/game/{game_id}")
    if not r: return None
    return r

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涩涩大富翁 · 棋盘</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0B0913;--sur:#141028;--sur2:#1C1638;
  --rose:#C84F72;--rosedim:rgba(200,79,114,.13);
  --vio:#7B5BAD;--viodim:rgba(123,91,173,.13);
  --gold:#C9A450;
  --text:#EDE5EF;--muted:#7A6A8A;--border:#242038;
  --t-task:#18102E;--t-truth:#0B2030;--t-chance:#0B261A;
  --t-myst:#281608;--t-jail:#260808;--t-shop:#221C06;--t-start:#240A18;
}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--text);
  font-family:-apple-system,'Helvetica Neue',sans-serif;
  display:flex;flex-direction:row}

.sidebar{
  width:180px;min-width:180px;
  background:var(--sur);border-right:1px solid var(--border);
  display:flex;flex-direction:column;
  height:100vh;overflow-y:auto;
}
.sidebar::-webkit-scrollbar{width:3px}
.sidebar::-webkit-scrollbar-thumb{background:var(--border)}
.logo{
  padding:16px 14px 14px;border-bottom:1px solid var(--border);
  font-family:Georgia,serif;font-size:1rem;
  letter-spacing:.18em;color:var(--rose);text-align:center;
  text-shadow:0 0 20px rgba(200,79,114,.3);flex-shrink:0;
}
.logo small{display:block;font-family:sans-serif;font-size:.5rem;
  letter-spacing:.2em;color:var(--muted);margin-top:3px;text-transform:uppercase}
.sb-sec{padding:12px 14px;border-bottom:1px solid var(--border)}
.sb-lbl{font-size:.52rem;letter-spacing:.15em;text-transform:uppercase;
  color:var(--muted);margin-bottom:7px}
.session-card{
  background:var(--sur2);border:1px solid var(--border);
  border-radius:7px;padding:9px 10px;cursor:pointer;
  transition:border-color .2s;margin-bottom:6px;
}
.session-card:hover{border-color:rgba(200,79,114,.4)}
.session-card.active{border-color:var(--rose)}
.sc-id{font-size:.58rem;color:var(--muted);font-variant-numeric:tabular-nums;margin-bottom:3px}
.sc-players{font-size:.62rem;color:var(--text)}
.sc-meta{font-size:.56rem;color:var(--muted);margin-top:2px}
.sc-live{font-size:.6rem;margin-top:4px;padding:2px 6px;border-radius:3px;
  display:inline-block;background:rgba(91,200,122,.15);color:#5BC87A}
.sc-done{font-size:.6rem;margin-top:4px;padding:2px 6px;border-radius:3px;
  display:inline-block;background:var(--rosedim);color:var(--rose)}
.safety{padding:12px 14px;margin-top:auto;border-top:1px solid var(--border)}
.safety-txt{font-size:.6rem;color:var(--muted);text-align:center;line-height:1.6}
.safety-word{color:var(--rose);font-weight:700;letter-spacing:.1em}

.main{flex:1;display:flex;flex-direction:column;height:100vh;overflow:hidden;min-width:0}
.top{display:flex;flex-direction:row;flex-shrink:0;height:62vh;
  border-bottom:1px solid var(--border);overflow:hidden;}
.board-area{padding:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.board{
  background:#080611;border:1.5px solid var(--border);border-radius:10px;
  padding:3px;display:grid;
  grid-template-columns:repeat(6,1fr);grid-template-rows:repeat(6,1fr);
  gap:3px;aspect-ratio:1/1;
  height:100%;max-height:calc(62vh - 24px);
}
.tile{border-radius:4px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;position:relative;
  overflow:hidden;font-size:clamp(7px,1.1vw,11px);border:1px solid rgba(255,255,255,.04)}
.tile .ic{font-size:1.4em;line-height:1}
.tile .lb{font-size:.52em;color:rgba(255,255,255,.38);margin-top:1px;text-align:center;line-height:1.2}
.tile .nb{position:absolute;bottom:2px;right:2px;font-size:.44em;color:rgba(255,255,255,.2);font-variant-numeric:tabular-nums}
.tile-start{background:var(--t-start)}.tile-task{background:var(--t-task)}
.tile-truth{background:var(--t-truth)}.tile-chance{background:var(--t-chance)}
.tile-mystery{background:var(--t-myst)}.tile-jail{background:var(--t-jail)}
.tile-shop{background:var(--t-shop)}
.tile.hi-a{box-shadow:inset 0 0 0 1.5px var(--rose),0 0 8px rgba(200,79,114,.3)}
.tile.hi-b{box-shadow:inset 0 0 0 1.5px var(--vio),0 0 8px rgba(123,91,173,.3)}
.tile.hi-ab{box-shadow:inset 0 0 0 1.5px var(--gold),0 0 8px rgba(201,164,80,.3)}
.bcenter{grid-row:2/6;grid-column:2/6;background:rgba(0,0,0,.5);
  border-radius:6px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:4px;padding:6px}
.bc-t{font-family:Georgia,serif;font-size:.8em;color:var(--rose);
  letter-spacing:.1em;text-align:center;line-height:1.4;
  text-shadow:0 0 16px rgba(200,79,114,.35)}
.bc-r{font-size:.48em;color:var(--muted);letter-spacing:.07em}
.bc-turn{font-size:.5em;letter-spacing:.05em;padding:2px 8px;
  border-radius:10px;background:rgba(255,255,255,.05);text-align:center}
.tok{width:14px;height:14px;border-radius:50%;position:absolute;
  border:1.5px solid rgba(255,255,255,.3);display:flex;align-items:center;
  justify-content:center;font-size:6.5px;font-weight:700;z-index:3;
  pointer-events:none;box-shadow:0 1px 4px rgba(0,0,0,.6)}
.tok-a{background:var(--rose);top:3px;left:3px}
.tok-b{background:var(--vio);top:3px;right:3px}

.player-side{flex:1;min-width:0;padding:10px 12px 10px 4px;
  display:flex;flex-direction:column;gap:8px;overflow-y:auto;}
.player-side::-webkit-scrollbar{width:3px}
.player-side::-webkit-scrollbar-thumb{background:var(--border)}
.pcard{background:var(--sur);border:1px solid var(--border);
  border-radius:8px;padding:10px 12px;display:flex;flex-direction:column;gap:6px;}
.pcard.pa{border-left:2px solid var(--rose)}
.pcard.pb{border-left:2px solid var(--vio)}
.pc-top{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.pc-name{font-family:Georgia,serif;font-size:.85rem;font-weight:normal}
.pa .pc-name{color:var(--rose)}.pb .pc-name{color:var(--vio)}
.pc-role{font-size:.58rem;color:var(--muted)}
.pc-stats{display:flex;gap:12px;flex-wrap:wrap}
.pcs{font-size:.62rem}
.pcs-lbl{color:var(--muted)}
.pcs-val{font-weight:600;font-variant-numeric:tabular-nums}
.pcs-val.gold{color:var(--gold)}
.id-box{border-top:1px solid var(--border);padding-top:6px;
  font-size:.6rem;color:var(--muted);line-height:1.6}
.id-name{font-size:.65rem;margin-bottom:2px}
.pa .id-name{color:var(--rose)}.pb .id-name{color:var(--vio)}

.bottom{flex:1;overflow-y:auto;padding:0;display:flex;flex-direction:column;}
.bottom::-webkit-scrollbar{width:4px}
.bottom::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.log-hd{
  position:sticky;top:0;z-index:10;background:var(--sur);
  padding:8px 16px;font-size:.56rem;color:var(--muted);
  letter-spacing:.14em;text-transform:uppercase;
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:8px;
}
.log-raw{padding:10px 16px 20px;font-size:.65rem;color:var(--muted);
  line-height:1.8;white-space:pre-wrap;word-break:break-all;}
.refresh-dot{width:6px;height:6px;border-radius:50%;
  background:#5BC87A;display:inline-block;margin-right:4px;
  animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="logo">涩涩大富翁<small>Spicy Monopoly</small></div>
  <div class="sb-sec">
    <div class="sb-lbl">游戏记录</div>
    <div id="gameList">加载中…</div>
  </div>
  <div class="safety">
    <div class="safety-txt">说 <span class="safety-word">404</span><br>立即全停</div>
  </div>
</div>

<div class="main">
  <div class="top">
    <div class="board-area">
      <div class="board" id="board"></div>
    </div>
    <div class="player-side" id="playerSide">
      <div style="color:var(--muted);font-size:.7rem;padding:20px">从左侧选择对局</div>
    </div>
  </div>
  <div class="bottom" id="logWrap">
    <div class="log-hd">
      <span class="refresh-dot"></span>
      ▸ 游戏状态
      <span id="lastUpdate" style="margin-left:auto;font-size:.5rem"></span>
    </div>
    <div class="log-raw" id="logRaw">—</div>
  </div>
</div>

<script>
const TYPES={0:'start',1:'task',2:'task',3:'task',4:'truth',5:'chance',
  6:'task',7:'task',8:'mystery',9:'task',10:'jail',11:'task',12:'shop',
  13:'task',14:'truth',15:'chance',16:'task',17:'mystery',18:'task',19:'shop'};
const ICONS={start:'🏁',task:'🎯',truth:'💬',chance:'🎴',mystery:'❓',jail:'🔒',shop:'🛒'};
const LABELS={start:'出发',task:'任务',truth:'真心话',chance:'抽卡',mystery:'神秘',jail:'监狱',shop:'商店'};
const GP=[[5,5],[5,4],[5,3],[5,2],[5,1],[5,0],[4,0],[3,0],[2,0],[1,0],
  [0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,5],[2,5],[3,5],[4,5]];

let currentGame=null;

function buildBoard(){
  const b=document.getElementById('board');
  b.innerHTML='';
  const c=document.createElement('div');
  c.className='bcenter';c.style.cssText='grid-row:2/6;grid-column:2/6';
  c.innerHTML=`<div class="bc-t">涩涩<br>大富翁</div>
    <div class="bc-r" id="bcRound">—</div>
    <div class="bc-turn" id="bcTurn">—</div>`;
  b.appendChild(c);
  for(let i=0;i<20;i++){
    const[r,col]=GP[i];const type=TYPES[i];
    const d=document.createElement('div');
    d.className=`tile tile-${type}`;d.id=`tile-${i}`;
    d.style.cssText=`grid-row:${r+1};grid-column:${col+1}`;
    d.innerHTML=`<span class="ic">${ICONS[type]}</span><span class="lb">${LABELS[type]}</span><span class="nb">${i}</span>`;
    b.appendChild(d);
  }
}

function placeTokens(posA,posB){
  document.querySelectorAll('.tok').forEach(t=>t.remove());
  document.querySelectorAll('.tile').forEach(t=>t.classList.remove('hi-a','hi-b','hi-ab'));
  const pa=((posA%20)+20)%20,pb=((posB%20)+20)%20;
  const tA=document.getElementById(`tile-${pa}`),tB=document.getElementById(`tile-${pb}`);
  if(pa===pb){
    if(tA){const t=mk('tok tok-a','⚡');tA.appendChild(t);tA.classList.add('hi-ab')}
  }else{
    if(tA){const t=mk('tok tok-a','A');tA.appendChild(t);tA.classList.add('hi-a')}
    if(tB){const t=mk('tok tok-b','B');tB.appendChild(t);tB.classList.add('hi-b')}
  }
}
function mk(cls,txt){const d=document.createElement('div');d.className=cls;d.textContent=txt;return d}

function renderState(data){
  if(!data)return;
  const pos=data.positions||{};
  const coins=data.coins||{};
  const laps=data.laps||{};
  const names=Object.keys(pos);
  const nameA=names[0]||'P1',nameB=names[1]||'P2';
  const posA=pos[nameA]||0,posB=pos[nameB]||0;

  // board center
  const board=data.board||'';
  const rm=board.match(/〔回合\s*(\d+)\/(\d+)〕/);
  if(rm)document.getElementById('bcRound').textContent=`第 ${rm[1]} / ${rm[2]} 回合`;
  const turn=data.turn||'';
  const turnEl=document.getElementById('bcTurn');
  turnEl.textContent=turn?' '+turn+' 的回合':'—';
  turnEl.style.color=turn===nameA?'var(--rose)':'var(--vio)';

  placeTokens(posA,posB);

  // parse status for identity
  const status=data.status||'';
  const idA=status.match(new RegExp(nameA+'[^:]*身份:([^\n:]+)'))?.[1]?.trim()||'';
  const idB=status.match(new RegExp(nameB+'[^:]*身份:([^\n:]+)'))?.[1]?.trim()||'';

  const posLbl=p=>{const n=((p%20)+20)%20;return`${n} · ${LABELS[TYPES[n]]}`};

  document.getElementById('playerSide').innerHTML=`
    <div class="pcard pa">
      <div class="pc-top">
        <span class="pc-name">${nameA}</span>
      </div>
      <div class="pc-stats">
        <div class="pcs"><span class="pcs-lbl">位置 </span><span class="pcs-val">${posLbl(posA)}</span></div>
        <div class="pcs"><span class="pcs-lbl">金币 </span><span class="pcs-val gold">${coins[nameA]||0} 🪙</span></div>
        <div class="pcs"><span class="pcs-lbl">圈数 </span><span class="pcs-val">${laps[nameA]||0}</span></div>
      </div>
      ${idA?`<div class="id-box"><div class="id-name">${idA}</div></div>`:''}
    </div>
    <div class="pcard pb">
      <div class="pc-top">
        <span class="pc-name">${nameB}</span>
      </div>
      <div class="pc-stats">
        <div class="pcs"><span class="pcs-lbl">位置 </span><span class="pcs-val">${posLbl(posB)}</span></div>
        <div class="pcs"><span class="pcs-lbl">金币 </span><span class="pcs-val gold">${coins[nameB]||0} 🪙</span></div>
        <div class="pcs"><span class="pcs-lbl">圈数 </span><span class="pcs-val">${laps[nameB]||0}</span></div>
      </div>
      ${idB?`<div class="id-box"><div class="id-name">${idB}</div></div>`:''}
    </div>`;

  document.getElementById('logRaw').textContent=status;
  document.getElementById('lastUpdate').textContent='更新于 '+new Date().toLocaleTimeString('zh');
}

async function loadGames(){
  const r=await fetch('/api/games');
  if(!r.ok)return;
  const d=await r.json();
  const games=d.games||[];
  const el=document.getElementById('gameList');
  if(!games.length){el.innerHTML='<div style="font-size:.6rem;color:var(--muted)">暂无对局</div>';return;}
  el.innerHTML=games.map(g=>`
    <div class="session-card ${currentGame===g.game_id?'active':''}"
      onclick="selectGame('${g.game_id}')">
      <div class="sc-id">#${g.game_id}</div>
      <div class="sc-players">${g.players||''}</div>
      <div class="sc-meta">${g.flavor||''}</div>
      <div class="${g.status==='ended'?'sc-done':'sc-live'}">${g.status==='ended'?'已结束':'进行中'}</div>
    </div>`).join('');
  if(!currentGame&&games.length)selectGame(games[0].game_id);
}

async function selectGame(id){
  currentGame=id;
  document.querySelectorAll('.session-card').forEach(c=>{
    c.classList.toggle('active',c.querySelector('.sc-id')?.textContent==='#'+id);
  });
  await refreshState();
}

async function refreshState(){
  if(!currentGame)return;
  const r=await fetch('/api/state?game_id='+currentGame);
  if(!r.ok)return;
  renderState(await r.json());
}

buildBoard();
loadGames();
setInterval(()=>{loadGames();refreshState();},5000);
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        p = self.path.split("?")[0]

        if p == "/api/games":
            data = api("/games", player_token=TOKEN)
            self._json(data or {"games": []})

        elif p == "/api/state":
            qs = dict(urllib.parse.parse_qsl(self.path.partition("?")[2]))
            gid = qs.get("game_id", "")
            data = get_state(gid) if gid else None
            self._json(data or {})

        else:
            self._html(HTML_TEMPLATE)

    def _json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print(f"涩涩大富翁 display 启动 → http://0.0.0.0:{PORT}  (API: {API_URL})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
