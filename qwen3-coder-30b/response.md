```html
<!DOCTYPE html>
<html>
<head>
    <title>Space Invaders</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: monospace;
            overflow: hidden;
        }
        canvas {
            border: 2px solid #fff;
            image-rendering: pixelated;
            image-rendering: -moz-crisp-edges;
            image-rendering: crisp-edges;
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="320" height="240"></canvas>

    <script>
        // Game constants
        const CANVAS_WIDTH = 320;
        const CANVAS_HEIGHT = 240;
        const PLAYER_WIDTH = 16;
        const PLAYER_HEIGHT = 8;
        const PLAYER_SPEED = 3;
        const ALIEN_ROWS = 5;
        const ALIEN_COLS = 10;
        const ALIEN_WIDTH = 12;
        const ALIEN_HEIGHT = 8;
        const ALIEN_SPACING_X = 14;
        const ALIEN_SPACING_Y = 10;
        const ALIEN_SPEED = 1;
        const ALIEN_DROP = 5;
        const PLAYER_SHOT_SPEED = 4;
        const ALIEN_SHOT_SPEED = 2;
        const SHIELD_WIDTH = 32;
        const SHIELD_HEIGHT = 16;
        const SHIELD_SPACING = 20;
        const UFO_WIDTH = 20;
        const UFO_HEIGHT = 8;
        const UFO_SPEED = 2;
        const MAX_SHOTS = 1;
        const PLAYER_LIVES = 3;
        const INITIAL_ALIEN_SPEED = 1;
        const ALIEN_SPEED_INCREMENT = 0.1;
        const SHOT_DAMAGE = 1;

        // Game state
        let gameState = {
            player: {
                x: CANVAS_WIDTH / 2 - PLAYER_WIDTH / 2,
                y: CANVAS_HEIGHT - 20,
                width: PLAYER_WIDTH,
                height: PLAYER_HEIGHT,
                alive: true
            },
            aliens: [],
            playerShots: [],
            alienShots: [],
            shields: [],
            ufo: {
                x: -UFO_WIDTH,
                y: 10,
                width: UFO_WIDTH,
                height: UFO_HEIGHT,
                alive: false,
                direction: 1
            },
            score: 0,
            lives: PLAYER_LIVES,
            level: 1,
            alienSpeed: INITIAL_ALIEN_SPEED,
            alienDirection: 1,
            lastAlienMoveTime: 0,
            alienMoveDelay: 500,
            lastUfoSpawnTime: 0,
            ufoSpawnDelay: 10000,
            lastShotTime: 0,
            shotDelay: 200,
            gameOver: false
        };

        // Audio context
        let audioContext;
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn("Web Audio API not supported");
        }

        // Canvas setup
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = CANVAS_WIDTH;
        canvas.height = CANVAS_HEIGHT;

        // Initialize game objects
        function initGame() {
            gameState.player.x = CANVAS_WIDTH / 2 - PLAYER_WIDTH / 2;
            gameState.player.alive = true;
            gameState.aliens = [];
            gameState.playerShots = [];
            gameState.alienShots = [];
            gameState.shields = [];
            gameState.ufo.alive = false;
            gameState.alienSpeed = INITIAL_ALIEN_SPEED;
            gameState.alienDirection = 1;
            gameState.lastAlienMoveTime = 0;
            gameState.lastUfoSpawnTime = 0;
            gameState.gameOver = false;

            // Create aliens
            for (let row = 0; row < ALIEN_ROWS; row++) {
                for (let col = 0; col < ALIEN_COLS; col++) {
                    const x = col * ALIEN_SPACING_X + 20;
                    const y = row * ALIEN_SPACING_Y + 40;
                    gameState.aliens.push({
                        x: x,
                        y: y,
                        width: ALIEN_WIDTH,
                        height: ALIEN_HEIGHT,
                        alive: true,
                        type: row < 2 ? 1 : row < 4 ? 2 : 3
                    });
                }
            }

            // Create shields
            for (let i = 0; i < 4; i++) {
                const x = i * (SHIELD_WIDTH + SHIELD_SPACING) + 40;
                gameState.shields.push({
                    x: x,
                    y: CANVAS_HEIGHT - 60,
                    width: SHIELD_WIDTH,
                    height: SHIELD_HEIGHT,
                    health: 10
                });
            }
        }

        // Sound functions
        function playSound(frequency, duration, type = 'square') {
            if (!audioContext) return;
            
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.type = type;
            oscillator.frequency.value = frequency;
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            setTimeout(() => {
                oscillator.stop();
            }, duration);
        }

        function playAlienMoveSound() {
            playSound(200, 50, 'square');
        }

        function playPlayerShotSound() {
            playSound(800, 100, 'sine');
        }

        function playAlienExplosionSound() {
            playSound(400, 200, 'square');
        }

        function playPlayerExplosionSound() {
            playSound(100, 500, 'sawtooth');
        }

        function playUfoSound() {
            playSound(600, 1000, 'sine');
        }

        // Input handling
        const keys = {};
        window.addEventListener('keydown', (e) => {
            keys[e.key] = true;
        });
        window.addEventListener('keyup', (e) => {
            keys[e.key] = false;
        });

        // Update game state
        function update(deltaTime) {
            if (gameState.gameOver) return;

            // Player movement
            if ((keys['ArrowLeft'] || keys['a'] || keys['A']) && gameState.player.x > 0) {
                gameState.player.x -= PLAYER_SPEED;
            }
            if ((keys['ArrowRight'] || keys['d'] || keys['D']) && gameState.player.x < CANVAS_WIDTH - PLAYER_WIDTH) {
                gameState.player.x += PLAYER_SPEED;
            }

            // Player shooting
            if (keys[' '] && gameState.player.alive && gameState.playerShots.length < MAX_SHOTS) {
                const now = Date.now();
                if (now - gameState.lastShotTime > gameState.shotDelay) {
                    gameState.playerShots.push({
                        x: gameState.player.x + PLAYER_WIDTH / 2 - 1,
                        y: gameState.player.y,
                        width: 2,
                        height: 4
                    });
                    playPlayerShotSound();
                    gameState.lastShotTime = now;
                }
            }

            // Update player shots
            for (let i = gameState.playerShots.length - 1; i >= 0; i--) {
                const shot = gameState.playerShots[i];
                shot.y -= PLAYER_SHOT_SPEED;

                // Remove if off screen
                if (shot.y < 0) {
                    gameState.playerShots.splice(i, 1);
                    continue;
                }

                // Check collision with aliens
                for (let j = gameState.aliens.length - 1; j >= 0; j--) {
                    const alien = gameState.aliens[j];
                    if (!alien.alive) continue;

                    if (shot.x < alien.x + alien.width &&
                        shot.x + shot.width > alien.x &&
                        shot.y < alien.y + alien.height &&
                        shot.y + shot.height > alien.y) {
                        
                        alien.alive = false;
                        gameState.playerShots.splice(i, 1);
                        playAlienExplosionSound();
                        
                        // Score based on alien type
                        if (alien.type === 1) gameState.score += 30;
                        else if (alien.type === 2) gameState.score += 20;
                        else gameState.score += 10;
                        
                        break;
                    }
                }

                // Check collision with shields
                for (let j = gameState.shields.length - 1; j >= 0; j--) {
                    const shield = gameState.shields[j];
                    if (shield.health <= 0) continue;

                    if (shot.x < shield.x + shield.width &&
                        shot.x + shot.width > shield.x &&
                        shot.y < shield.y + shield.height &&
                        shot.y + shot.height > shield.y) {
                        
                        shield.health -= SHOT_DAMAGE;
                        gameState.playerShots.splice(i, 1);
                        break;
                    }
                }
            }

            // Update alien shots
            for (let i = gameState.alienShots.length - 1; i >= 0; i--) {
                const shot = gameState.alienShots[i];
                shot.y += ALIEN_SHOT_SPEED;

                // Remove if off screen
                if (shot.y > CANVAS_HEIGHT) {
                    gameState.alienShots.splice(i, 1);
                    continue;
                }

                // Check collision with player
                if (gameState.player.alive &&
                    shot.x < gameState.player.x + gameState.player.width &&
                    shot.x + shot.width > gameState.player.x &&
                    shot.y < gameState.player.y + gameState.player.height &&
                    shot.y + shot.height > gameState.player.y) {
                    
                    gameState.player.alive = false;
                    playPlayerExplosionSound();
                    gameState.lives--;
                    gameState.playerShots = [];
                    gameState.alienShots = [];
                    
                    if (gameState.lives <= 0) {
                        gameState.gameOver = true;
                    }
                    gameState.player.x = CANVAS_WIDTH / 2 - PLAYER_WIDTH / 2;
                    break;
                }

                // Check collision with shields
                for (let j = gameState.shields.length - 1; j >= 0; j--) {
                    const shield = gameState.shields[j];
                    if (shield.health <= 0) continue;

                    if (shot.x < shield.x + shield.width &&
                        shot.x + shot.width > shield.x &&
                        shot.y < shield.y + shield.height &&
                        shot.y + shot.height > shield.y) {
                        
                        shield.health -= SHOT_DAMAGE;
                        gameState.alienShots.splice(i, 1);
                        break;
                    }
                }
            }

            // Update aliens
            const now = Date.now();
            if (now - gameState.lastAlienMoveTime > gameState.alienMoveDelay) {
                let moveDown = false;

                // Check if aliens need to change direction
                for (const alien of gameState.aliens) {
                    if (!alien.alive) continue;
                    
                    if ((gameState.alienDirection === 1 && alien.x + alien.width >= CANVAS_WIDTH - 10) ||
                        (gameState.alienDirection === -1 && alien.x <= 10)) {
                        moveDown = true;
                        break;
                    }
                }

                if (moveDown) {
                    gameState.alienDirection *= -1;
                    for (const alien of gameState.aliens) {
                        if (!alien.alive) continue;
                        alien.y += ALIEN_DROP;
                        
                        // Check if aliens reached the bottom
                        if (alien.y + alien.height >= gameState.player.y) {
                            gameState.gameOver = true;
                        }
                    }
                } else {
                    for (const alien of gameState.aliens) {
                        if (!alien.alive) continue;
                        alien.x += gameState.alienSpeed * gameState.alienDirection;
                    }
                }

                playAlienMoveSound();
                gameState.lastAlienMoveTime = now;

                // Increase speed
                gameState.alienSpeed += ALIEN_SPEED_INCREMENT;
                gameState.alienMoveDelay = Math.max(100, 500 - (gameState.level * 50));
            }

            // Spawn UFO occasionally
            if (!gameState.ufo.alive && now - gameState.lastUfoSpawnTime > gameState.ufoSpawnDelay) {
                gameState.ufo.x = gameState.ufo.direction === 1 ? -UFO_WIDTH : CANVAS_WIDTH;
                gameState.ufo.alive = true;
                playUfoSound();
                gameState.lastUfoSpawnTime = now;
            }

            // Update UFO position
            if (gameState.ufo.alive) {
                gameState.ufo.x += UFO_SPEED * gameState.ufo.direction;
                
                // Remove UFO when off screen
                if ((gameState.ufo.direction === 1 && gameState.ufo.x > CANVAS_WIDTH) ||
                    (gameState.ufo.direction === -1 && gameState.ufo.x < -UFO_WIDTH)) {
                    gameState.ufo.alive = false;
                }
            }

            // Check if all aliens are destroyed
            const allDead = gameState.aliens.every(alien => !alien.alive);
            if (allDead) {
                gameState.level++;
                initGame();
            }

            // Check UFO collision with player shots
            for (let i = gameState.playerShots.length - 1; i >= 0; i--) {
                const shot = gameState.playerShots[i];
                if (gameState.ufo.alive &&
                    shot.x < gameState.ufo.x + gameState.ufo.width &&
                    shot.x + shot.width > gameState.ufo.x &&
                    shot.y < gameState.ufo.y + gameState.ufo.height &&
                    shot.y + shot.height > gameState.ufo.y) {
                    
                    gameState.playerShots.splice(i, 1);
                    gameState.ufo.alive = false;
                    gameState.score += 500;
                    break;
                }
            }
        }

        // Render game
        function render() {
            // Clear canvas
            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

            if (!gameState.gameOver) {
                // Draw player
                if (gameState.player.alive) {
                    ctx.fillStyle = '#fff';
                    ctx.fillRect(gameState.player.x, gameState.player.y, gameState.player.width, gameState.player.height);
                    
                    // Draw player details
                    ctx.fillRect(gameState.player.x + 2, gameState.player.y - 2, 12, 2);
                }

                // Draw aliens
                for (const alien of gameState.aliens) {
                    if (!alien.alive) continue;
                    
                    ctx.fillStyle = '#fff';
                    switch (alien.type) {
                        case 1: // Top row aliens
                            ctx.fillRect(alien.x, alien.y, alien.width, alien.height);
                            break;
                        case 2: // Middle row aliens
                            ctx.fillRect(alien.x + 2, alien.y, alien.width - 4, alien.height);
                            ctx.fillRect(alien.x, alien.y + 2, 2, 4);
                            ctx.fillRect(alien.x + alien.width - 2, alien.y + 2, 2, 4);
                            break;
                        case 3: // Bottom row aliens
                            ctx.fillRect(alien.x, alien.y + 2, alien.width, alien.height - 4);
                            ctx.fillRect(alien.x + 2, alien.y, 2, 2);
                            ctx.fillRect(alien.x + alien.width - 4, alien.y, 2, 2);
                            break;
                    }
                }

                // Draw player shots
                ctx.fillStyle = '#fff';
                for (const shot of gameState.playerShots) {
                    ctx.fillRect(shot.x, shot.y, shot.width, shot.height);
                }

                // Draw alien shots
                ctx.fillStyle = '#fff';
                for (const shot of gameState.alienShots) {
                    ctx.fillRect(shot.x, shot.y, shot.width, shot.height);
                }

                // Draw shields
                for (const shield of gameState.shields) {
                    if (shield.health <= 0) continue;
                    
                    ctx.fillStyle = '#0f0';
                    ctx.fillRect(shield.x, shield.y, shield.width, shield.height);
                    
                    // Draw shield damage
                    const damageWidth = Math.floor((shield.width * shield.health) / 10);
                    ctx.fillStyle = '#0a0';
                    ctx.fillRect(shield.x, shield.y, damageWidth, shield.height);
                }

                // Draw UFO
                if (gameState.ufo.alive) {
                    ctx.fillStyle = '#fff';
                    ctx.fillRect(gameState.ufo.x, gameState.ufo.y, gameState.ufo.width, gameState.ufo.height);
                    
                    // Draw UFO details
                    ctx.fillRect(gameState.ufo.x + 4, gameState.ufo.y - 2, 12, 2);
                }
            }

            // Draw score and lives
            ctx.fillStyle = '#fff';
            ctx.font = '8px monospace';
            ctx.fillText(`SCORE: ${gameState.score}`, 5, 10);
            ctx.fillText(`LIVES: ${gameState.lives}`, CANVAS_WIDTH - 40, 10);
            ctx.fillText(`LEVEL: ${gameState.level}`, CANVAS_WIDTH / 2 - 20, 10);

            // Draw game over
            if (gameState.gameOver) {
                ctx.fillStyle = '#fff';
                ctx.font = '16px monospace';
                ctx.textAlign = 'center';
                ctx.fillText('GAME OVER', CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2);
                ctx.font = '8px monospace';
                ctx.fillText(`FINAL SCORE: ${gameState.score}`, CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2 + 20);
                ctx.textAlign = 'left';
            }
        }

        // Game loop
        let lastTime = 0;
        function gameLoop(timestamp) {
            const deltaTime = timestamp - lastTime;
            lastTime = timestamp;

            update(deltaTime);
            render();

            requestAnimationFrame(gameLoop);
        }

        // Start the game
        initGame();
        requestAnimationFrame(gameLoop);
    </script>
</body>
</html>
```