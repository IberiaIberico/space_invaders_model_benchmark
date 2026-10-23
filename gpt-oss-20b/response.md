```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Space Invaders</title>
<style>
  body{margin:0;background:#000;color:#fff;font-family:monospace;overflow:hidden}
  canvas{display:block;margin:auto;background:#000}
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
const CANVAS_W=224, CANVAS_H=256;
const SCALE=Math.min(window.innerWidth/CANVAS_W, window.innerHeight/CANVAS_H);
const canvas=document.getElementById('game');
canvas.width=CANVAS_W;canvas.height=CANVAS_H;
canvas.style.transform=`scale(${SCALE})`;
const ctx=canvas.getContext('2d',{alpha:false});
ctx.imageSmoothingEnabled=false;

let keys={};
window.addEventListener('keydown',e=>keys[e.key]=true);
window.addEventListener('keyup',e=>{delete keys[e.key];});

class Sprite{constructor(x,y,w,h){this.x=x;this.y=y;this.w=w;this.h=h}}
class Player extends Sprite{
  constructor(){super(CANVAS_W/2-8, CANVAS_H-16,16,8);this.lives=3}
  move(dt){if(keys['ArrowLeft']||keys['a']) this.x-=80*dt;if(keys['ArrowRight']||keys['d']) this.x+=80*dt;this.x=Math.max(0,this.x);this.x=Math.min(CANVAS_W-this.w,this.x);}
  shoot(){if(!playerShot){playerShot=new Projectile(this.x+7.5, this.y-1,'up');}}
}
class Alien extends Sprite{
  constructor(x,y,row){super(x,y,8,8);this.row=row;this.alive=true;}
  draw(){ctx.fillStyle='#0f0';ctx.fillRect(this.x,this.y,this.w,this.h);}
}
class UFO extends Sprite{constructor(){super(-32,0,32,16);this.speed=30;this.active=false}}
class Projectile extends Sprite{
  constructor(x,y,d){super(x-1.5,y-2,3,4);this.dir=d;}
  update(dt){if(this.dir==='up') this.y-=200*dt;else this.y+=200*dt;}
}
class Shield{constructor(x,y){this.x=x;this.y=y;this.blocks=[];for(let i=0;i<8;i++)for(let j=0;j<4;j++){let b=new Sprite(x+i*2,y+j*2,2,2);b.alive=true;this.blocks.push(b)}}
  draw(){ctx.fillStyle='#888';this.blocks.forEach(b=>{if(b.alive)ctx.fillRect(b.x,b.y,b.w,b.h);})}
}

const player=new Player();
let aliens=[], alienDir=1, alienSpeed=0.5, alienTimer=0;
function initAliens(){
  aliens=[];
  for(let r=0;r<5;r++)for(let c=0;c<11;c++){
    let a=new Alien(c*16+24,r*12+20,r);
    aliens.push(a);
  }
}
initAliens();
const shields=[new Shield(32,200),new Shield(96,200),new Shield(160,200)];
let ufo=new UFO(),ufoTimer=0;
let playerShot=null, alienShots=[],score=0;

function update(dt){
  player.move(dt);
  if(keys[' ']){player.shoot();keys[' ']=false;}
  aliens.forEach(a=>{if(a.alive){a.x+=alienDir*alienSpeed;}});

  // Alien movement
  let hitEdge=false;
  aliens.forEach(a=>{if(a.alive&&(a.x<0||a.x>CANVAS_W-a.w))hitEdge=true;});
  if(hitEdge){alienDir*=-1;aliens.forEach(a=>{if(a.alive)a.y+=8;});}

  // Alien shooting
  alienTimer+=dt;
  if(alienTimer>2/alienSpeed){
    let shooters=aliens.filter(a=>a.alive);
    if(shooters.length){let s=shooters[Math.floor(Math.random()*shooters.length)];alienShots.push(new Projectile(s.x+3.5,s.y+8,'down'));}
    alienTimer=0;
  }

  // UFO
  ufoTimer+=dt;
  if(!ufo.active&&ufoTimer>20){ufo.active=true;ufo.x=-32;}
  if(ufo.active){
    ufo.x+=ufo.speed*dt;
    if(ufo.x>CANVAS_W) {ufo.active=false;ufoTimer=0;}
  }

  // Projectiles
  if(playerShot){playerShot.update(dt);if(playerShot.y<0)playerShot=null;}
  alienShots.forEach(p=>p.update(dt));
  alienShots=[...alienShots.filter(p=>p.y<CANVAS_H)];

  // Collisions
  aliens.forEach(a=>{
    if(a.alive && playerShot && rectIntersect(a,playerShot)){
      a.alive=false;score+=10;playerShot=null;
    }
    alienShots.forEach(p=>{
      if(rectIntersect(a,p)){a.alive=false;p.y=CANVAS_H;}
    });
  });

  shields.forEach(s=>s.blocks.forEach(b=>{
    if(b.alive){
      if(playerShot && rectIntersect(b,playerShot)){b.alive=false;playerShot=null;}
      alienShots.forEach(p=>{if(rectIntersect(b,p))b.alive=false;p.y=CANVAS_H;});
    }
  }));

  // UFO hit
  if(ufo.active){alienShots.forEach(p=>{if(rectIntersect(ufo,p)){ufo.active=false;p.y=CANVAS_H;score+=50;}};}

  // Check win/lose
  if(aliens.every(a=>!a.alive)){initAliens();alienSpeed*=1.05;}
  if(aliens.some(a=>a.y>CANVAS_H-20)) {alert('Game Over');location.reload();}
}
function rectIntersect(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;}

function draw(){
  ctx.fillStyle='#000';ctx.fillRect(0,0,CANVAS_W,CANVAS_H);
  // Player
  ctx.fillStyle='#ff0';ctx.fillRect(player.x,player.y,player.w,player.h);
  // Aliens
  aliens.forEach(a=>{if(a.alive)a.draw();});
  // UFO
  if(ufo.active){ctx.fillStyle='#f00';ctx.fillRect(ufo.x,ufo.y,ufo.w,ufo.h);}
  // Projectiles
  if(playerShot)ctx.fillStyle='#fff';else ctx.fillStyle='transparent';
  ctx.fillRect(playerShot?.x,playerShot?.y,playerShot?.w,playerShot?.h);
  alienShots.forEach(p=>{ctx.fillStyle='#f0f';ctx.fillRect(p.x,p.y,p.w,p.h);});
  // Shields
  shields.forEach(s=>s.draw());
  // HUD
  ctx.fillStyle='#fff';
  ctx.font='8px monospace';
  ctx.fillText(`SCORE ${score}`,4,10);
  ctx.fillText(`LIVES ${player.lives}`,CANVAS_W-40,10);
}
let last=0;
function loop(t){const dt=(t-last)/1000;last=t;update(dt);draw();requestAnimationFrame(loop);}
requestAnimationFrame(loop);
</script>
</body>
</html>
```