# Setup

Requires Python 3.9+, pygame, and a MySQL or MariaDB server (WAMP, XAMPP, etc). The game still starts without the database, it just can't save scores.

## 1. Install the packages
```
pip install -r requirements.txt
```

## 2. Set up the database (WAMP / phpMyAdmin)
1. Start WAMP and open phpMyAdmin.
2. Go to the **Import** tab and import `space_invaders_cordero_db.sql`. You don't have to create the database first. It makes `space_invaders_cordero_db` with the `players` and `scores` tables. Works on MySQL 8+ and MariaDB 10.2+.
3. Careful: this file drops and recreates both tables, so importing it again deletes all players and scores. Only use it for a fresh setup.
4. If you already have a database from an older version, don't re-import. Select `space_invaders_cordero_db` in phpMyAdmin and run the migration files you're missing:
   - `add_avatar_color.sql` adds the ship color column
   - `add_ship_model.sql` adds the ship model column used by the Hangar

   You can run both more than once without losing data. Without these columns the game still works, your ship and color are just saved on this computer (`settings.json`) instead of in your account.

## 3. Database login
Open `settings.json` and change the `"database"` part if your MySQL login is different (WAMP's default is `root` with no password):
```json
"database": {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "space_invaders_cordero_db"
}
```
If you upload the project to GitHub, keep the password empty or use a throwaway one.

## 4. Test the connection
```
python test_db_connection.py
```
It adds a test player and score, reads them back, updates the profile, then deletes the test data. If it prints "All CRUD operations completed", the database is working.

## 5. Run the game
```
python main.py
```
You can run it from any folder. Resize the window or press **F11** for fullscreen.

## Controls
| Action | Keys |
|---|---|
| Move | `LEFT` / `RIGHT` or `A` / `D`, or hold the on-screen arrows |
| Fire | `SPACE` (or `UP`), or hold the on-screen FIRE button |
| Pause | `P` or `ESC`, or the pause button at the top right |
| Fullscreen | `F11` |
| Title screen | Type your name, then `ENTER` or click LAUNCH. Click CHOOSE SHIP (or the ship) to open the Hangar |
| Hangar | `LEFT` / `RIGHT` to change ship, `UP` / `DOWN` to change color (or click). `ENTER`, `ESC` or DONE to leave |
| Game over | `ENTER` to play again |
| Profile | Type a name and press `ENTER` to rename. CHANGE SHIP & COLOR opens the Hangar. ADD PICTURE or dragging an image into the window sets a profile picture. `ESC` to go back |

## Features
**Database**
- Type a name on the title screen to register or log in (`players` table).
- Every run is saved automatically (`scores` table).
- Leaderboard shows the top 10 players and highlights your row.
- Hangar: choose one of 4 ships and a color before playing, from the title screen or your profile. It's saved to your account.
- Profile pictures: add one from your files or drag an image into the window. They're stored in `profile_pictures/` on your computer and are not uploaded anywhere or saved in the database, so they don't follow you to another computer.
- Profile page: games played, best score, average score, rename, and a shortcut to the Hangar.
- Switch player without restarting the game.
- A badge on the title screen shows if the database is online.

**Gameplay**
- 4 ships: **Falcon** (balanced), **Viper** (fast and small, slower bullets), **Titan** (very fast bullets, big and slow) and **Aegis** (starts every run with a shield). Stats are in `entities/ships.py`.
- 3 lives and endless levels with more and faster enemies. Enemies that reach the bottom bounce back up, so the level only ends when all of them are dead.
- Enemies: drone (1 HP), dart (fast), armored tank (2 HP), and the Mothership boss every 5th level. The boss shoots spread shots, never runs away, and has its own health bar and music.
- Combo multiplier up to x5, level-clear bonuses and a "NEW HIGH SCORE" banner.
- 6 power-ups: Rapid Fire, Shield, Smart Bomb, Time Freeze, Extra Life and Scatter Shot (a fan of pellets that hits each enemy once, good for crowds but not bosses).

**Extras**
- Custom neon art for the ship, enemies, bullets, power-ups, background and planet.
- Particles, shockwaves, engine flames, screen shake and flashes.
- 3 music tracks (menu, battle, boss) and 13 sound effects.
- Pause menu, settings screen, hover effects, window icon, fullscreen.
- 5 themes (Nova, Inferno, Emerald, Frost, Synthwave), each with its own background, planet, accent color and UI gradient. Change it in Settings and it applies right away.
- Works offline and on computers with no audio device.

## Settings
Click **SETTINGS** on any menu, or use the pause menu while playing. Sound and music toggles and volumes, the **MOVE & FIRE BUTTONS** switch (shows or hides the on-screen buttons, keyboard always works) and screen shake are saved in `settings.json`. You can also edit it by hand:
```json
"audio": { "sound_volume": 0.8, "music_volume": 0.6, "sound_enabled": true, "music_enabled": true },
"controls": { "mobile_controls": true },
"display": { "screen_shake": true, "theme": "nova" },
"loadout": { "ship": "falcon", "color": "cyan" },
"profile_pictures": { "han": "pic_001.png" }
```
`loadout` is the last ship and color you picked. Ships: `falcon`, `viper`, `titan`, `aegis`. Colors: `white`, `cyan`, `magenta`, `yellow`, `green`. Themes: `nova`, `inferno`, `emerald`, `frost`, `synthwave`. `profile_pictures` links a lowercase player name to a file in `profile_pictures/`, you usually don't need to touch it.

## Changing the art and sounds
Everything loads by filename, so just replace a file and keep the same name.

| What | Where |
|---|---|
| Player ships (hull + glowing accent layer) | `assets/images/ship1.png` to `ship4.png` and `ship1_accent.png` to `ship4_accent.png` (Falcon, Viper, Titan, Aegis) |
| Enemies | `assets/images/enemy_normal.png`, `enemy_fast.png`, `enemy_tank.png`, `enemy_boss.png` |
| Bullets | `assets/images/bullet.png` (yours), `enemy_bullet.png` |
| Power-up icons | `assets/images/powerup_<name>.png` |
| Background and planet | `assets/images/bg_nebula.png` (tiles vertically), `planet.png` |
| Window icon | `assets/images/icon.png` |
| Sound effects | `assets/sounds/*.wav` (names are in `managers/audio_manager.py`) |
| Music | `assets/music/menu.wav`, `theme.wav`, `boss.wav` (they loop) |
| Theme backgrounds and planets | `assets/images/bg_<theme>.png`, `planet_<theme>.png` |
| Scatter Shot icon and pellet | `assets/images/powerup_scatter.png`, `pellet.png` |

The ship accent layers get tinted with the player's color, so keep them white on a transparent background.

**Regenerating the assets:** all images and sounds are made by `generate_assets.py`. It needs a few extra packages that the game doesn't:
```
pip install -r requirements-dev.txt
python generate_assets.py          # everything
python generate_assets.py images   # images only
python generate_assets.py audio    # sounds and music only
```
Edit the `draw_*` functions for the art, or `sfx_*` and `build_*` for the sounds and music, then run the script. It overwrites the files in `assets/`. Theme file names and colors are in `THEME_ART` near the top of the script, and the in-game UI colors are in `entities/theme.py`.

## Project layout
```
main.py                 window, icon, fullscreen, main loop
settings.json           audio, controls, display and database settings
managers/
    game_manager.py     game states, rules, HUD and all screens
    db_manager.py       MySQL (players, scores, leaderboard)
    audio_manager.py    sound effects and music
    settings_manager.py on-screen controls and screen shake settings
    avatar_manager.py   local profile pictures (add, list, circle crop)
entities/
    player.py enemy.py bullet.py powerup.py   game objects
    ships.py            the 4 ships and their stats
    theme.py            the 5 themes and their colors
    effects.py          particles, shockwaves, stars, scrolling background
    button.py ui.py     on-screen controls, panels, buttons, text
    sprites.py          image and font loading
assets/                 images, sounds, music and fonts
profile_pictures/       added profile pictures (made automatically, not in git)
```

## Credits
- Game and code: Cordero, Ismail A.
- Fonts: Audiowide (Astigmatic) and Rajdhani (Indian Type Foundry), both under the SIL Open Font License. The license files are in `assets/fonts/`.
- All images, sounds and music are generated with `generate_assets.py`.

## Troubleshooting
- **"Connection failed" in the console:** make sure MySQL is running and the login in `settings.json` is right, then run `python test_db_connection.py`.
- **No sound:** check the Settings screen. If your computer has no audio device, the game runs silent on purpose.
- **Ship choice isn't saved to my account:** import `add_ship_model.sql` (step 2.4). Until then it's only saved on this computer.
- **ADD PICTURE does nothing:** the file dialog needs Tk (`python3-tk` on Linux, it's already included in the Windows and macOS Python installers). If it's missing, drag an image into the game window instead.
- **Window too big:** it shrinks to fit your screen. You can also drag the edges or press F11.
