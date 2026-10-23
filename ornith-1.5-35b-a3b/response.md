```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SPACE INVADERS</title>
<style>
  html,body{margin:0;padding:0;background:#000;height:100%;overflow:hidden;}
  #wrap{position:fixed;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;}
  canvas{background:#000;image-rendering:pixelated;image-rendering:crisp-edges;}
</style>
</head>
<body>
<div id="wrap">
<canvas id="game"></canvas>
</div>
<script>
(function(){
"use strict";

const GAME_W = 480, GAME_H = 560;
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
canvas.width = GAME_W;
canvas.height = GAME_H;
ctx.imageSmoothingEnabled = false;

function resize(){
  const s = Math.min(window.innerWidth/GAME_W, window.innerHeight/GAME_H);
  canvas.style.width = (GAME_W*s)+'px';
  canvas.style.height = (GAME_H*s)+'px';
}
window.addEventListener('resize', resize);
resize();

// ---------- Sprite definitions ----------
function normalize(rows){
  let w=0; for(const r of rows) w=Math.max(w,r.length);
  return rows.map(r=>r.padEnd(w,' '));
}
const SPR = {
  player: normalize([
    "   ##   ",
    "  ####  ",
    " ###### ",
    "########",
    "########",
  ]),
  squidA: normalize([" .##. "," ##### ","######","###.##"," ##### "]),
  squidB: normalize([" .##. "," ##### ","###.##","######"," ##### "]),
  crabA:  normalize([" #.#. ",".###.","#####","#.#.#","#####",".#.#."]),
  crabB:  normalize(["#...#","#####",".#.#.","#####","#.#.#",".###."]),
  crab2A: normalize([" ##.##",".#####","######","######",".#####"]),
  crab2B: normalize([".##.##","######",".#####","######","#####."]),
  ufo:    normalize(["  ###  "," ##### ","#.#.#.#","#######"," ##### "]),
};

// ---------- Audio ----------
let actx=null;
function initAudio(){
  if(!actx){ try{ actx = new (window.AudioContext||window.webkitAudioContext)(); }catch(e){} }
  if(actx && actx.state==='suspended') actx.resume();
}
function tone(freq,dur,type,vol,fallTo){
  if(!actx) return;
  const t=actx.currentTime;
  const o=actx.createOscillator(), g=actx.createGain();
  o.type=type||'square'; o.frequency.setValueAtTime(freq,t);
  if(fallTo!==undefined) o.frequency.exponentialRampToValueAtTime(fallTo,t+dur);
  g.gain.setValueAtTime(vol||0.18,t);
  g.gain.exponentialRampToValueAtTime(0.0001,t+dur);
  o.connect(g).connect(actx.destination);
  o.start(t); o.stop(t+dur+0.02);
}
function noise(dur,vol){
  if(!actx) return;
  const n=Math.floor(actx.sampleRate*dur);
  const buf=actx.createBuffer(1,n,actx.sampleRate);
  const d=buf.getChannelData(0);
  for(let i=0;i<n;i++) d[i]=(Math.random()*2-1)*(1-i/n);
  const src=actx.createBufferSource(); src.buffer=buf;
  const g=actx.createGain(); g.gain.value=vol||0.2;
  src.connect(g).connect(actx.destination); src.start();
}
const sStep=()=>tone(70+game.tempo*6,0.05,'square',0.09);
const sShot=()=>tone(880,0.12,'square',0.14,300);
const sKill=()=>{tone(420,0.06,'square',0.13,700);tone(700,0.1,'triangle',0.1,1100);};
const sBoom=()=>{noise(0.45,0.28);tone(180,0.4,'sawtooth',0.12,60);};
let ufoOsc=null,ufoGain=null;
function ufoStart(){
  if(!actx) return;
  const o=actx.createOscillator(), g=actx.createGain();
  o.type='sawtooth'; o.frequency.value=180;
  g.gain.value=0.0; o.connect(g).connect(actx.destination);
  o.start();
  const lfo=actx.createOscillator(); lfo.frequency.value=5; const lg=actx.createGain(); lg.gain.value=60;
  lfo.connect(lg).connect(o.frequency); lfo.start();
  g.gain.setValueAtTime(0.0,actx.currentTime);
  g.gain.linearRampToValueAtTime(0.12,actx.currentTime+0.05);
  ufoOsc=o; ufoGain=g; ufoLfo=lfo; ufoLg=lg;
}
let ufoLfo=null,ufoLg=null;
function ufoStop(){
  if(!actx||!ufoOsc) return;
  const t=actx.currentTime;
  ufoGain.gain.cancelScheduledValues(t);
  ufoGain.gain.setValueAtTime(ufoGain.gain.value,t);
  ufoGain.gain.linearRampToValueAtTime(0.0001,t+0.1);
  ufoOsc.stop(t+0.15); ufoLfo.stop(t+0.15);
  ufoOsc=null;ufoGain=null;
}

// ---------- Game state ----------
const game = {
  state:'title', // title, play, dead, over, waveclear
  score:0, hi:parseInt(localStorage.getItem('si_hi')||'0',10),
  lives:3, wave:1,
  stepTimer:0, animFrame:0, alienDir:1,
  shotTimer:0, ufoTimer:12000,
  alienShotTimer:0,
  spawnTimer:0, flashLives:0, waveClearTimer:0,
  tempo:0,
};

const ALIEN_TOTAL = 55; // 5 rows x 11 cols
let aliens=[];
function buildAliens(){
  aliens=[];
  const cols=11, rows=5;
  for(let r=0;r<rows;r++){
    for(let c=0;c<cols;c++){
      let type='squid', pts=30;
      if(r===1||r===2){ type='crab'; pts=12; }
      else if(r>=3){ type='crab2'; pts=8; }
      aliens.push({row:r,col:c,type,pts,alive:true});
    }
  }
}

const PX=3; // pixel scale for sprites
const formation = { ox:0, oy:60 };
const SPACING_X=34, SPACING_Y=30;
const STEP_X=10, DROP_Y=22;

let player={ x: GAME_W/2 - 13, y: GAME_H-52, w:26, h:18, speed:210 };
let playerShot=null; // {x,y,h}
const alienBullets=[];
let ufo=null;
let ufoScorePop=null; // {x,y,t,val}

// Shields
const shields=[];
function buildShields(){
  shields.length=0;
  const bw=4, bh=4, cw=11, ch=7;
  const shieldY = GAME_H-128;
  const positions=[78, 178, 278, 378];
  const pattern=[
    "###########",
    "###########",
    "###########",
    "###########",
    "###########",
    "###...###",
    "###...###",
  ];
  for(const px of positions){
    const blocks=[];
    for(let r=0;r<pattern.length;r++){
      for(let c=0;c<pattern[r].length;c++){
        if(pattern[r][c]!=='.') blocks.push({x:px+c*bw, y:shieldY+r*bh, w:bw, h:bh, on:true});
      }
    }
    shields.push(blocks);
  }
}

// ---------- Input ----------
const keys={};
window.addEventListener('keydown',e=>{
  if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' '].includes(e.key)) e.preventDefault();
  keys[e.key]=true;
  initAudio();
  if(e.key===' '){
    if(game.state==='title'){ startGame(); }
    else if(game.state==='over'||game.state==='waveclear'){ /* handled by timer */ }
  }
});
window.addEventListener('keyup',e=>{ keys[e.key]=false; });

function startGame(){
  game.state='play';
  game.score=0; game.lives=3; game.wave=1;
  resetWave();
}
function resetWave(){
  buildAliens();
  formation.ox = (GAME_W - (11*SPACING_X - SPACING_X))/2 + 6;
  formation.oy = 60;
  alienBullets.length=0;
  playerShot=null;
  ufo=null; ufoScorePop=null;
  game.stepTimer=0; game.alienShotTimer=0; game.ufoTimer=9000+Math.random()*6000;
  buildShields();
}

// ---------- Update ----------
function update(dt){
  if(game.state==='title') return;

  if(game.state==='dead'){
    game.spawnTimer-=dt;
    game.flashLives=(game.flashLives+dt)%700<350;
    if(game.spawnTimer<=0){
      game.lives--;
      if(game.lives<0){
        game.state='over';
      } else {
        player.x = GAME_W/2 - 13;
        playerShot=null; alienBullets.length=0;
        game.spawnTimer=1500;
        game.state='play';
      }
    }
    return;
  }

  if(game.state==='waveclear'){
    game.waveClearTimer-=dt;
    if(game.waveClearTimer<=0){
      game.wave++;
      resetWave();
      game.state='play';
    }
    return;
  }

  if(game.state==='over') return;

  // ---- player move ----
  let mv=0;
  if(keys['ArrowLeft']||keys['a']||keys['A']) mv-=1;
  if(keys['ArrowRight']||keys['d']||keys['D']) mv+=1;
  player.x += mv*player.speed*dt/1000;
  player.x = Math.max(8, Math.min(GAME_W-player.w-8, player.x));

  // ---- player shot (one on screen) ----
  game.shotTimer-=dt;
  if((keys[' ']||keys['ArrowUp']||keys['w']||keys['W']) && !playerShot && game.shotTimer<=0){
    playerShot={ x: player.x+player.w/2-2, y: player.y-8, h:12 };
    sShot();
    game.shotTimer=60;
  }

  // ---- alien rhythm / tempo ----
  const aliveCount = aliens.filter(a=>a.alive).length;
  const ratio = aliveCount/ALIEN_TOTAL;
  let interval = 40 + 190*ratio;
  interval *= Math.max(0.35, 1 - (game.wave-1)*0.06);
  game.tempo = 1 - interval/230; // 0..~1 for pitch
  game.stepTimer += dt;
  while(game.stepTimer >= interval){
    game.stepTimer -= interval;
    moveAliens();
  }

  // ---- alien shooting ----
  const maxBullets = 3 + Math.floor(game.wave/2);
  game.alienShotTimer -= dt;
  if(aliveCount>0 && alienBullets.length<maxBullets && game.alienShotTimer<=0){
    const rate = Math.max(180, 1100 - game.wave*90);
    game.alienShotTimer = rate + Math.random()*rate*0.6;
    shootAlien();
  }

  // ---- UFO ----
  game.ufoTimer -= dt;
  if(!ufo && game.ufoTimer<=0){
    const dir = Math.random()<0.5?1:-1;
    ufo={ x: dir===1?-46:GAME_W+46, y:42, w:36, h:16, dir, speed:80 };
    ufoStart();
    game.ufoTimer = 11000 + Math.random()*7000;
  }
  if(ufo){
    ufo.x += ufo.dir*ufo.speed*dt/1000;
    if((ufo.dir===1 && ufo.x>GAME_W+20)||(ufo.dir===-1 && ufo.x<-60)){
      ufo=null; ufoStop();
    }
  }
  if(ufoScorePop){
    ufoScorePop.t -= dt;
    ufoScorePop.y -= 0.25*dt;
    if(ufoScorePop.t<=0) ufoScorePop=null;
  }

  // ---- move shots ----
  if(playerShot){
    playerShot.y -= 460*dt/1000;
    if(playerShot.y < -14) playerShot=null;
  }
  for(let i=alienBullets.length-1;i>=0;i--){
    const b=alienBullets[i];
    b.y += 250*dt/1000;
    if(b.y>GAME_H+10) alienBullets.splice(i,1);
  }

  // ---- popups ----
  for(let i=ufoScorePops.length-1;i>=0;i--){
    ufoScorePops[i].t-=dt; ufoScorePops[i].y-=0.3*dt;
    if(ufoScorePops[i].t<=0) ufoScorePops.splice(i,1);
  }

  // ---- collisions ----
  collidePlayerShot();
  collideAlienBullets();

  // ---- wave clear check ----
  if(aliens.filter(a=>a.alive).length===0 && game.state==='play'){
    game.state='waveclear';
    game.waveClearTimer=2200;
    tone(523,0.1,'square',0.1,523); setTimeout(()=>tone(784,0.15,'square',0.1,784),120);
  }
}

function moveAliens(){
  sStep();
  const alive=aliens.filter(a=>a.alive);
  if(alive.length===0) return;
  let minX=1e9,maxX=-1e9,minY=1e9;
  for(const a of alive){
    const ax = formation.ox + a.col*SPACING_X;
    const ay = formation.oy + a.row*SPACING_Y;
    minX=Math.min(minX,ax); maxX=Math.max(maxX,ax+24); minY=Math.min(minY,ay);
  }
  let drop=false;
  if(game.alienDir===1){
    if(maxX > GAME_W-10){ game.alienDir=-1; drop=true; }
  } else {
    if(minX < 10){ game.alienDir=1; drop=true; }
  }
  formation.ox += game.alienDir*STEP_X;
  if(drop){ formation.oy += DROP_Y; game.alienDir*=-1; }
  if(formation.oy + (4)*SPACING_Y > player.y-30){ game.state='over'; }
}

function shootAlien(){
  const cols={};
  for(const a of aliens) if(a.alive){ if(!cols[a.col]||a.row>cols[a.col].row) cols[a.col]=a; }
  const keys2=Object.keys(cols).map(Number);
  if(keys2.length===0) return;
  const c = keys2[Math.floor(Math.random()*keys2.length)];
  const a = cols[c];
  const ax = formation.ox + c*SPACING_X + 10;
  const ay = formation.oy + a.row*SPACING_Y + 24;
  alienBullets.push({x:ax,y:ay,w:3,h:12});
}

function collidePlayerShot(){
  if(!playerShot) return;
  // UFO
  if(ufo){
    if(playerShot.x<ufo.x+ufo.w && playerShot.x+4>ufo.x && playerShot.y<ufo.y+ufo.h && playerShot.y+playerShot.h>ufo.y){
      const val=[50,100,150,300][Math.floor(Math.random()*4)];
      game.score+=val;
      ufoScorePops.push({x:ufo.x,y:ufo.y,t:1200,val});
      tone(120,0.2,'square',0.15,400);
      for(const b of getBlocksIn(ufo.x,ufo.y)) b.on=false;
      ufo=null; ufoStop(); playerShot=null; return;
    }
  }
  // Aliens
  for(const a of aliens){
    if(!a.alive) continue;
    const ax = formation.ox + a.col*SPACING_X;
    const ay = formation.oy + a.row*SPACING_Y;
    if(playerShot.x<ax+24 && playerShot.x+4>ax && playerShot.y<ay+24 && playerShot.y+playerShot.h>ay){
      a.alive=false; game.score+=a.pts; sKill(); playerShot=null; return;
    }
  }
  collideShields(playerShot, true);
}

function collideAlienBullets(){
  for(let i=alienBullets.length-1;i>=0;i--){
    const b=alienBullets[i];
    if(ufo && b.x<ufo.x+ufo.w && b.x+4>ufo.x && b.y<ufo.y+ufo.h && b.y+b.h>ufo.y){
      const val=[50,100,150,300][Math.floor(Math.random()*4)];
      game.score+=val;
      ufoScorePops.push({x:ufo.x,y:ufo.y,t:1200,val});
      tone(120,0.2,'square',0.15,400);
      ufo=null; ufoStop(); alienBullets.splice(i,1); continue;
    }
    // player
    if(b.x<player.x+player.w && b.x+3>player.x && b.y<player.y+player.h && b.y+b.h>player.y){
      alienBullets.splice(i,1); killPlayer(); return;
    }
    collideShields(b, false);
  }
}

function getBlocksIn(x,y){
  const out=[];
  for(const s of shields) for(const blk of s) if(blk.on && Math.abs(blk.x+2-x)<10 && Math.abs(blk.y+2-y)<10) out.push(blk);
  return out;
}
function collideShields(b, isPlayer){
  for(const s of shields){
    for(const blk of s){
      if(!blk.on) continue;
      if(b.x<s.x+blk.w && b.x+4>s.x && b.y<s.y+blk.h && b.y+b.h>s.y){
        blk.on=false;
        // chip neighbors a bit
        for(const n of s){ if(n.on && Math.abs(n.x-blk.x)<=4 && Math.abs(n.y-blk.y)<=4 && Math.random()<0.5) n.on=false; }
        return true;
      }
    }
  }
  return false;
}

function killPlayer(){
  sBoom();
  game.state='dead';
  game.spawnTimer=1200;
  game.flashLives=0;
  playerShot=null;
}

// ---------- Render ----------
function drawSprite(name,x,y,color){
  const sp=SPR[name]; if(!sp) return;
  ctx.fillStyle=color;
  for(let r=0;r<sp.length;r++){
    const row=sp[r];
    for(let c=0;c<row.length;c++){
      const ch=row[c];
      if(ch!==' '&&ch!=='.'){ ctx.fillRect(Math.floor(x+c*PX), Math.floor(y+r*PX), PX, PX); }
    }
  }
}

function render(){
  ctx.fillStyle='#000';
  ctx.fillRect(0,0,GAME_W,GAME_H);

  // HUD line
  ctx.fillStyle='#fff';
  ctx.fillRect(0,24,GAME_W,1);

  // Score
  ctx.fillStyle='#fff';
  ctx.font='bold 16px monospace';
  ctx.textAlign='left';
  ctx.fillText('SCORE',14,18);
  ctx.textAlign='right';
  ctx.fillText(String(game.score).padStart(6,'0'),GAME_W-14,18);
  ctx.textAlign='center';
  ctx.font='10px monospace';
  ctx.fillStyle='#888';
  ctx.fillText('HIGH SCORE '+String(game.hi).padStart(6,'0'),GAME_W/2,14);
  ctx.fillText('WAVE '+game.wave,GAME_W/2,26);

  // Aliens
  const curFrame = game.animFrame;
  for(const a of aliens){
    if(!a.alive) continue;
    let spr, col='#fff';
    if(a.type==='squid'){ spr=curFrame===0?SPR.squidA:SPR.squidB; }
    else if(a.type==='crab'){ spr=curFrame===0?SPR.crabA:SPR.crabB; }
    else { spr=curFrame===0?SPR.crab2A:SPR.crab2B; col='#fff'; }
    const ax = formation.ox + a.col*SPACING_X;
    const ay = formation.oy + a.row*SPACING_Y;
    drawSprite(spr,ax,ay,col);
  }

  // UFO
  if(ufo) drawSprite('ufo',ufo.x,ufo.y,'#0f0');

  // Shields
  ctx.fillStyle='#39ff14';
  for(const s of shields) for(const blk of s){ if(blk.on) ctx.fillRect(blk.x,blk.y,blk.w-0.5,blk.h-0.5); }

  // Alien bullets
  ctx.fillStyle='#fff';
  for(const b of alienBullets){ 
    for(let y=0;y<b.h;y+=3) ctx.fillRect(b.x,b.y+y,b.w,2);
  }

  // Player shot
  if(playerShot){
    ctx.fillStyle='#fff';
    for(let y=0;y<playerShot.h;y+=2) ctx.fillRect(playerShot.x,playerShot.y+y,2,1);
  }

  // Player
  if(game.state!=='dead' || game.flashLives%700<350){
    drawSprite('player',Math.floor(player.x),Math.floor(player.y),'#fff');
  }

  // Lives icons
  for(let i=0;i<Math.max(0,game.lives);i++){
    drawSprite('player',24+i*28, GAME_H-16, '#fff');
  }

  // UFO score popups
  ctx.font='bold 14px monospace';
  for(const p of ufoScorePops){
    ctx.fillStyle='#0f0';
    ctx.textAlign='center';
    ctx.fillText(String(p.val),Math.floor(p.x)+18,Math.floor(p.y));
  }

  // Overlays
  if(game.state==='title'){
    ctx.textAlign='center';
    ctx.fillStyle='#fff';
    ctx.font='bold 34px monospace';
    ctx.fillText('SPACE',GAME_W/2,190);
    ctx.fillText('INVADERS',GAME_W/2,228);
    // sample aliens + scores
    drawSprite('squid', GAME_W/2-150, 270, '#fff');
    drawSprite('crab', GAME_W/2-40, 270, '#fff');
    drawSprite('crab2', GAME_W/2+70, 270, '#fff');
    ctx.font='14px monospace'; ctx.fillStyle='#fff';
    ctx.fillText('= 30',GAME_W/2-175,286);
    ctx.fillText('= 12',GAME_W/2-65,286);
    ctx.fillText('= 8 ',GAME_W/2+45,286);
    drawSprite('ufo', GAME_W/2-18, 320, '#0f0');
    ctx.fillStyle='#0f0'; ctx.fillText('= ?',GAME_W/2+30,336);

    ctx.fillStyle='#ff0';
    ctx.font='bold 16px monospace';
    const blink = (performance.now()%1000)<600;
    if(blink) ctx.fillText('PRESS SPACE TO START',GAME_W/2,430);
    ctx.fillStyle='#888'; ctx.font='10px monospace';
    ctx.fillText('\u2190 \u2192 / A D  MOVE   SPACE  FIRE',GAME_W/2,470);
  }

  if(game.state==='waveclear'){
    ctx.textAlign='center';
    ctx.fillStyle='#0f0';
    ctx.font='bold 26px monospace';
    ctx.fillText('WAVE '+game.wave+' CLEAR',GAME_W/2,GAME_H/2);
  }

  if(game.state==='over'){
    ctx.textAlign='center';
    ctx.fillStyle='#f00';
    ctx.font='bold 40px monospace';
    ctx.fillText('GAME OVER',GAME_W/2,260);
    ctx.fillStyle='#fff'; ctx.font='16px monospace';
    ctx.fillText('SCORE '+String(game.score).padStart(6,'0'),GAME_W/2,300);
    ctx.fillStyle='#ff0';
    const blink=(performance.now()%1000)<600;
    if(blink){ ctx.font='bold 14px monospace'; ctx.fillText('PRESS SPACE TO RESTART',GAME_W/2,350); }
  }

  updateHi();
}

function updateHi(){
  if(game.score>game.hi){ game.hi=game.score; try{localStorage.setItem('si_hi',String(game.hi));}catch(e){} }
}

// ---------- Main loop ----------
let last=performance.now();
function loop(t){
  const dt=Math.min(50, t-last);
  last=t;
  update(dt);
  render();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

})();
</script>
</body>
</html>
```