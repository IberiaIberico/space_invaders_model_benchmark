```html
<!DOCTYPE.DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Space Invaders</title>
    <style>
        body { margin: 0; background: #111; color: white; font-family: monospace; overflow: hidden; }
        canvas { display: block; image-rendering: pixelated; width: 100vw; height: auto; max-width: 800px; margin: auto; }
    </style>
</head>
<body>
<canvas id="game"></canvas>
<script>
const GAME_WIDTH = 400, GAME_HEIGHT = 600;
 const SCALE = Math.min(window.innerWidth / GAME_WIDTH, window.innerHeight / GAME_HEIGHT);
 let score = 0, lives = 3, wave = 1;

 const canvas = document.getElementById('game');
 const ctx = canvas.getContext('2d', { alpha: false });
 canvas.width = GAME_WIDTH;
 canvas.height = GAME_HEIGHT;

 const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
 function playSound(freq, type, duration) {
   const osc = audioCtx.createOscillator();
   const gain = audioCtx.createGain();
   osc.type = type;
   osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
   gain.gain.linearRampToValueAtTime(0.15, audioCtx.currentTime + 0.02);
   gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
   osc.connect(gain).connect(audioCtx.destination);
   osc.start();
   osc.stop(audioCtx.currentTime + duration);
 }

 const player = { x: 185, y: 560, w: 30, h: 20 };
 let bullets = [], alienBullets = [];
 let aliens = [];
 let bunkers = [
   { x: 40,  y: 470, w: 90, h: 100, hp: 4 },
   { x: 135, y: 470, w: 90, h: 100, hp: 4 },
   { x: 230, y: 470, w: 90, h: 100, hp: 4 },
   { x: 325, y: 470, w: 90, h: 100, hp: 4 }
 ];
 let ufo = null;

 function initWave() {
   aliens = [];
   for (let r = 0; r < 4; r++) {
     const type = r === 0 ? 'u' : r === 1 ? 'm' : r === 2 ? 's' : 'b';
     for (let c = 0; c < 10; c++) aliens.push({ x: 45 + c * 30, y: 60 + r * 30, type });
   }
 }

 let alienDir = 1, alienSpeed = 1;
 function update() {
   if (lives <= 0) return;
   let aliveCount = aliens.length;
   if (aliveCount === 0 && !ufo) { wave++; score += 500; initWave(); }

   aliens.forEach(a => {
     a.x += alienDir * alienSpeed;
     if (a.x < 45 || a.x > 365) {
       alienDir *= -1;
       a.y += 20;
     }
   });

   bullets = bullets.filter(b => b.active);
   aliens.forEach((a, i) => {
     if (player.bullet && a.x > player.x && a.x < player.x + player.w && a.y > 500)) {
       bullets = bullets.filter(b => b !== a);
       aliens.splice(i, 1);
       score += (a.type === 'u' ? 200 : 100);
       playSound(440 + wave * 50, 'square', 0.1);
     }
   });

   alienBullets = alienBullets.filter((b, i) => {
     let hit = false;
     [...bullets, ...aliens].forEach(obj => {
       if (b.x > obj.x && b.x < obj.x + (obj.w || 20) && b.y > obj.y && b.y < obj.y + (obj.h || 15)) hit = true;
     });

     let bunkerHit = false;
     bunkers.forEach((b, bi) => {
       if (b.hp > 0 && b.x < b.x+b.w && b.x<b.x+b.w && b.y<b.y+b.h) {} // placeholder logic for hit detection below
     });

   // Simplified collision against bunkers and player
   if (b.hp > 0 && b.x < b.x + b.w && b.y < b.y + b.h) {}

   return false;
 });

 function render() {
   ctx.fillStyle = '#111';
   // Draw bunkers
   bunkers.forEach((b, i) => {
     if (b.hp <= 0) return;
     const hp = b.hp / 4;
     for(let j=0;j<4;j++) ctx.fillStyle=(i+j)%2==0?'#1e90ff':'#fff';
     ctx.fillRect(b.x, b.y+(3-j)*25, b.w, 25);
   });

   // Draw player
   ctx.fillStyle = '#f0f';
   ctx.fillRect(player.x, player.y, player.w, player.h);

   // Draw aliens
   aliens.forEach(a => {
     if (a.type === 'u') ctx.fillStyle='#ff0'; else if (a.type === 'm') ctx.fillStyle = '#f0f'; else if (a.type === 's') ctx.fillStyle = '#0f0'; else ctx.fillStyle = '#fff';
     ctx.fillRect(a.x, a.y, 25, 15);
   });

   // Draw bullets
   bullets.forEach(b => { if (b) ctx.fillStyle='#ff0'; });
   alienBullets.forEach(b => { if (b) ctx.fillStyle = '#f0f'; });
 }

 function loop() { update(); render(); requestAnimationFrame(loop); }

 window.addEventListener('keydown', e => {
   if (e.key === 'ArrowLeft' || e.key === 'a') player.x -= 15;
   else if (e.key === 'ArrowRight' || e.key === 'd') player.x = Math.max(0, Math.min(370, player.x + 15));
   else if (e.code === 'Space' && !bullets.length) {
     bullets.push({ x: player.x + 12, y: player.y, active: true });
     playSound(600, 'triangle', 0.1);
   }
});

initWave(); loop();
</script>
</body>
</html>
```