```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Space Invaders</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: monospace;
        }
        canvas {
            border: 2px solid #fff;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    <script>
        (function() {
            'use strict';

            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            let gameWidth, gameHeight;
            let scale = 1;

            function resizeCanvas() {
                const windowRatio = window.innerWidth / window.innerHeight;
                if (windowRatio > 4 / 3) {
                    gameWidth = 800 * scale;
                    gameHeight = 600 * scale;
                } else {
                    gameWidth = 600 * windowRatio * scale;
                    gameHeight = 600 * scale;
                }
                canvas.width = Math.floor(gameWidth);
                canvas.height = Math.floor(gameHeight);
            }

            function setScale(s) {
                scale = s;
                resizeCanvas();
            }

            resizeCanvas();

            const colors = {
                black: '#000',
                white: '#fff',
                green: '#0f0',
                red: '#f00'
            };

            let gameState = {
                lives: 3,
                score: 0,
                wave: 1,
                gameOver: false,
                level: 0,
                ufoTimer: 0,
                ufoActive: false
            };

            const keys = {
                left: false,
                right: false,
                space: false
            };

            document.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowLeft' || e.key === 'A') keys.left = true;
                if (e.key === 'ArrowRight' || e.key === 'D') keys.right = true;
                if (e.key === ' ') keys.space = true;
            });

            document.addEventListener('keyup', (e) => {
                if (e.key === 'ArrowLeft' || e.key === 'A') keys.left = false;
                if (e.key === 'ArrowRight' || e.key === 'D') keys.right = false;
                if (e.key === ' ') keys.space = false;
            });

            let player = {
                x: gameWidth / 2 - 10,
                y: gameHeight - 30,
                width: 20,
                height: 10,
                speed: 5,
                shotCooldown: 0
            };

            const aliens = [];
            let alienFormation = [];
            let alienDirection = 1;
            let alienMoveSpeed = 1;
            let alienMoveDown = false;
            let alienMoveDownCounter = 0;
            let alienPoints = [30, 20, 15, 10, 8, 7, 6, 5];
            let alienTypes = [
                { color: '#0f0', points: 30 },
                { color: '#ff0', points: 20 },
                { color: '#f00', points: 15 },
                { color: '#0ff', points: 10 },
                { color: '#ff0', points: 8 },
                { color: '#0f0', points: 7 },
                { color: '#f0f', points: 6 },
                { color: '#0ff', points: 5 }
            ];

            function createAlienFormation() {
                alienFormation = [];
                const rows = Math.min(5, gameState.wave);
                for (let row = 0; row < rows; row++) {
                    const cols = Math.min(12 - row * 2, 11);
                    for (let col = 0; col < cols; col++) {
                        alienFormation.push({
                            x: 50 + col * 40,
                            y: 50 + row * 30,
                            width: 30,
                            height: 20,
                            type: row % alienTypes.length,
                            points: alienPoints[row]
                        });
                    }
                }
            }

            function resetAliens() {
                aliens.length = 0;
                createAlienFormation();
                for (const alien of alienFormation) {
                    aliens.push({ ...alien, health: 1 });
                }
                alienDirection = 1;
                alienMoveSpeed = 1 + gameState.level * 0.2;
                alienMoveDown = false;
                alienMoveDownCounter = 0;
            }

            let playerShot = null;
            const playerShots = [];

            function createPlayerShot() {
                if (player.shotCooldown > 0) return;
                player.shotCooldown = 30;
                playerShots.push({
                    x: player.x + player.width / 2 - 5,
                    y: player.y,
                    width: 10,
                    height: 10,
                    speed: 7
                });
            }

            const alienShots = [];
            let alienShotCooldown = 0;

            function createAlienShot() {
                if (alienShotCooldown > 0) return;
                const alien = aliens[Math.floor(Math.random() * aliens.length)];
                if (!alien) return;
                alienShots.push({
                    x: alien.x + alien.width / 2 - 5,
                    y: alien.y + alien.height,
                    width: 10,
                    height: 10,
                    speed: 3
                });
                alienShotCooldown = Math.random() * 60 + 30;
            }

            const shields = [];
            function createShields() {
                for (let i = 0; i < 4; i++) {
                    shields.push({
                        x: gameWidth / 2 - 150 + i * 80,
                        y: gameHeight - 150,
                        width: 60,
                        height: 30,
                        health: 1
                    });
                }
            }

            function resetShields() {
                for (const shield of shields) {
                    shield.health = 1;
                }
            }

            let ufo = null;

            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const sounds = {
                shoot: createSound(audioContext, 'shoot'),
                destroy: createSound(audioContext, 'destroy'),
                playerExplode: createSound(audioContext, 'playerExplode'),
                ufo: createSound(audioContext, 'ufo')
            };

            function createSound(ctx, name) {
                const oscillator = ctx.createOscillator();
                const gainNode = ctx.createGain();
                oscillator.type = Math.random() > 0.5 ? 'sine' : 'square';
                oscillator.frequency.value = name === 'shoot' ? 800 : name === 'destroy' ? 1200 : name === 'playerExplode' ? 600 : 400;
                gainNode.gain.value = 0.1;
                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);
                return { oscillator, gainNode };
            }

            function playSound(sound) {
                if (sound) {
                    sound.oscillator.start();
                    setTimeout(() => sound.oscillator.stop(), 200);
                }
            }

            let lastTime = 0;
            let deltaTime = 0;

            function gameLoop(currentTime) {
                if (!lastTime) lastTime = currentTime;
                deltaTime = (currentTime - lastTime) / 16; // Normalize to ~60fps
                lastTime = currentTime;

                update();
                render();

                requestAnimationFrame(gameLoop);
            }

            function update() {
                if (gameState.gameOver) return;

                player.shotCooldown -= deltaTime;
                alienShotCooldown -= deltaTime;

                if (keys.left && player.x > 0) player.x -= player.speed * deltaTime;
                if (keys.right && player.x < gameWidth - player.width) player.x += player.speed * deltaTime;
                if (keys.space) createPlayerShot();

                if (!alienMoveDown) {
                    for (let i = 0; i < aliens.length; i++) {
                        const alien = aliens[i];
                        if (alien.x + alien.width > gameWidth || alien.x < 0) {
                            alienMoveDown = true;
                            break;
                        }
                    }
                }

                if (alienMoveDown) {
                    alienMoveDownCounter += deltaTime;
                    if (alienMoveDownCounter >= 30) {
                        for (const alien of aliens) {
                            alien.y += 15 * deltaTime;
                        }
                        alienMoveDownCounter = 0;
                        createAlienShot();
                    }
                } else {
                    for (const alien of aliens) {
                        alien.x += alienDirection * alienMoveSpeed * deltaTime;
                    }
                }

                if (Math.random() < 0.01 && !gameState.ufoActive) {
                    gameState.ufoTimer = 240;
                    gameState.ufoActive = true;
                    ufo = {
                        x: Math.random() * (gameWidth - 50),
                        y: -50,
                        width: 30,
                        height: 20
                    };
                }

                if (gameState.ufoTimer > 0) {
                    gameState.ufoTimer -= deltaTime;
                    ufo.y += 1.5 * deltaTime;
                    if (ufo.y > gameHeight) {
                        gameState.ufoActive = false;
                        gameState.score += 300;
                    }
                }

                for (let i = playerShots.length - 1; i >= 0; i--) {
                    const shot = playerShots[i];
                    shot.y -= shot.speed * deltaTime;
                    if (shot.y < 0) {
                        playerShots.splice(i, 1);
                    } else {
                        for (let j = aliens.length - 1; j >= 0; j--) {
                            const alien = aliens[j];
                            if (checkCollision(shot, alien)) {
                                playSound(sounds.destroy);
                                gameState.score += alien.points;
                                aliens.splice(j, 1);
                                playerShots.splice(i, 1);
                                break;
                            }
                        }
                    }
                }

                for (let i = alienShots.length - 1; i >= 0; i--) {
                    const shot = alienShots[i];
                    shot.y += shot.speed * deltaTime;
                    if (checkCollision(shot, player)) {
                        playSound(sounds.playerExplode);
                        gameState.lives--;
                        if (gameState.lives <= 0) {
                            gameState.gameOver = true;
                        }
                        alienShots.splice(i, 1);
                    } else if (shot.y > gameHeight) {
                        alienShots.splice(i, 1);
                    }
                }

                for (let i = aliens.length - 1; i >= 0; i--) {
                    const alien = aliens[i];
                    if (alien.y + alien.height > gameHeight) {
                        playSound(sounds.playerExplode);
                        gameState.lives--;
                        if (gameState.lives <= 0) {
                            gameState.gameOver = true;
                        }
                        aliens.splice(i, 1);
                    }
                }

                for (let i = shields.length - 1; i >= 0; i--) {
                    const shield = shields[i];
                    for (let j = playerShots.length - 1; j >= 0; j--) {
                        const shot = playerShots[j];
                        if (checkCollision(shot, shield)) {
                            shield.health--;
                            playerShots.splice(j, 1);
                            if (shield.health <= 0) shields.splice(i, 1);
                            break;
                        }
                    }
                    for (let j = alienShots.length - 1; j >= 0; j--) {
                        const shot = alienShots[j];
                        if (checkCollision(shot, shield)) {
                            shield.health--;
                            alienShots.splice(j, 1);
                            if (shield.health <= 0) shields.splice(i, 1);
                            break;
                        }
                    }
                }

                if (aliens.length === 0 && !gameState.gameOver) {
                    gameState.wave++;
                    resetAliens();
                    resetShields();
                    createShields();
                    gameState.level = Math.floor(gameState.wave / 5);
                }
            }

            function checkCollision(a, b) {
                return a.x < b.x + b.width &&
                       a.x + a.width > b.x &&
                       a.y < b.y + b.height &&
                       a.y + a.height > b.y;
            }

            function render() {
                ctx.fillStyle = colors.black;
                ctx.fillRect(0, 0, gameWidth, gameHeight);

                if (gameState.ufoActive && ufo) {
                    ctx.fillStyle = '#fff';
                    drawUFO(ufo);
                }

                for (const alien of aliens) {
                    ctx.fillStyle = alienTypes[alien.type].color;
                    drawAlien(alien);
                }

                for (const shield of shields) {
                    ctx.fillStyle = '#0f0';
                    drawShield(shield);
                }

                if (playerShot) {
                    ctx.fillStyle = colors.green;
                    drawPlayerShot(playerShot);
                }

                for (const shot of playerShots) {
                    ctx.fillStyle = colors.green;
                    drawPlayerShot(shot);
                }

                for (const shot of alienShots) {
                    ctx.fillStyle = colors.red;
                    drawAlienShot(shot);
                }

                ctx.fillStyle = colors.green;
                drawPlayer(player);

                renderScore();
            }

            function drawAlien(alien) {
                const type = alienTypes[alien.type];
                ctx.beginPath();
                if (type.color === '#0f0') {
                    // Type 1: Simple rectangle
                    ctx.rect(alien.x, alien.y, alien.width, alien.height);
                } else if (type.color === '#ff0') {
                    // Type 2: Square with a dot
                    ctx.rect(alien.x + 5, alien.y + 5, 20, 10);
                    ctx.rect(alien.x + 10, alien.y + 8, 4, 4);
                } else if (type.color === '#f00') {
                    // Type 3: Triangle
                    const points = [
                        [alien.x + 5, alien.y],
                        [alien.x + 25, alien.y],
                        [alien.x + 15, alien.y + 20]
                    ];
                    ctx.moveTo(points[0][0], points[0][1]);
                    for (let i = 1; i < points.length; i++) {
                        ctx.lineTo(points[i][0], points[i][1]);
                    }
                    ctx.closePath();
                } else if (type.color === '#0ff') {
                    // Type 4: Circle
                    ctx.beginPath();
                    ctx.arc(alien.x + 15, alien.y + 10, 8, 0, Math.PI * 2);
                    ctx.closePath();
                }
                ctx.fill();
            }

            function drawPlayer(player) {
                ctx.beginPath();
                // Player cannon
                ctx.rect(player.x, player.y, player.width, player.height);
                // Barrel
                ctx.rect(player.x + 5, player.y - 10, 10, 10);
                ctx.fill();
            }

            function drawPlayerShot(shot) {
                ctx.beginPath();
                ctx.rect(shot.x, shot.y, shot.width, shot.height);
                ctx.fill();
            }

            function drawAlienShot(shot) {
                ctx.beginPath();
                ctx.rect(shot.x, shot.y, shot.width, shot.height);
                ctx.fill();
            }

            function drawShield(shield) {
                ctx.beginPath();
                // Shield base
                ctx.rect(shield.x, shield.y, shield.width, shield.height);
                // Shield segments
                for (let i = 0; i < 3; i++) {
                    const x = shield.x + 5 + i * 15;
                    const y = shield.y - 5;
                    ctx.rect(x, y, 10, 20);
                }
                ctx.fill();
            }

            function drawUFO(ufo) {
                ctx.beginPath();
                // UFO body
                ctx.arc(ufo.x + 15, ufo.y + 10, 8, 0, Math.PI * 2);
                // UFO antennae
                ctx.moveTo(ufo.x + 10, ufo.y - 5);
                ctx.lineTo(ufo.x + 10, ufo.y - 15);
                ctx.moveTo(ufo.x + 20, ufo.y - 5);
                ctx.lineTo(ufo.x + 20, ufo.y - 15);
                ctx.stroke();
            }

            function renderScore() {
                ctx.fillStyle = colors.white;
                ctx.font = '16px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('SCORE', 10, 30);
                ctx.fillText(gameState.score.toString().padStart(7, '0'), 10, 50);

                ctx.textAlign = 'right';
                ctx.fillText('WAVE', gameWidth - 10, 30);
                ctx.fillText(gameState.wave.toString(), gameWidth - 10, 50);

                ctx.textAlign = 'center';
                ctx.fillText('LIVES', gameWidth / 2, 30);
                for (let i = 0; i < gameState.lives; i++) {
                    ctx.drawImage(canvas, player.x + i * 20, 45, 20, 10);
                }
            }

            function resetGame() {
                gameState = {
                    lives: 3,
                    score: 0,
                    wave: 1,
                    gameOver: false,
                    level: 0,
                    ufoTimer: 0,
                    ufoActive: false
                };
                player.x = gameWidth / 2 - 10;
                resetAliens();
                createShields();
            }

            window.addEventListener('resize', resizeCanvas);
            setInterval(() => {
                if (!gameState.gameOver) {
                    for (const alien of aliens) {
                        if (Math.random() < 0.01) {
                            createAlienShot();
                        }
                    }
                }
            }, 100);

            resetGame();
            requestAnimationFrame(gameLoop);
        })();
    </script>
</body>
</html>
```