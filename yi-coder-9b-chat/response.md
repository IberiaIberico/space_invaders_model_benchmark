```HTML
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Space Invaders</title>
    <style>
      body {
        margin: 0;
        overflow: hidden;
      }
    </style>
  </head>
  <body>
    <canvas id="gameCanvas"></canvas>

    <script>
      const canvas = document.getElementById('gameCanvas');
      const ctx = canvas.getContext('2d');

      // Game constants
      const GAME_WIDTH = 800;
      const GAME_HEIGHT = 600;
      const SHIP_SPEED = 3;
      const ALIEN_SPEED = 1;
      const SHOT_SPEED = 5;
      const SCORE_PER_ALIEN = 10;

      // Game variables
      let playerX = GAME_WIDTH / 2;
      let playerY = GAME_HEIGHT - 50;
      let playerShotX = null;
      let playerShotY = null;
      let alienRow = [];
      let alienSpeed = ALIEN_SPEED;
      let score = 0;
      let gameOver = false;

      // Create the player ship
      function drawPlayer() {
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.moveTo(playerX, playerY);
        ctx.lineTo(playerX - 20, playerY + 30);
        ctx.lineTo(playerX + 20, playerY + 30);
        ctx.closePath();
        ctx.fill();
      }

      // Create the alien rows
      function drawAliens() {
        alienRow.forEach((alien, index) => {
          if (alien === true) {
            ctx.fillStyle = 'red';
            ctx.beginPath();
            ctx.moveTo(index % 10 * 65 + 32.5, Math.floor(index / 10) * 40);
            ctx.lineTo(index % 10 * 65, Math.floor(index / 10) * 40 + 30);
            ctx.lineTo(index % 10 * 65 + 65, Math.floor(index / 10) * 40 + 30);
            ctx.closePath();
            ctx.fill();
          }
        });
      }

      // Update the game state and draw everything on each frame
      function updateAndDraw(timestamp) {
        if (!gameOver) {
          ctx.clearRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
          drawPlayer();
          drawAliens();
          requestAnimationFrame(updateAndDraw);
        } else {
          console.log('Game Over');
        }
      }

      // Start the game loop
      requestAnimationFrame(updateAndDraw);
    </script>
  </body>
</html>
```