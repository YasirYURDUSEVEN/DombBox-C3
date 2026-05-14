from machine import Pin, SoftI2C, PWM, ADC
import ssd1306, time, random, json, gc

# --- Donanım ---
gc.collect()
i2c = SoftI2C(scl=Pin(9), sda=Pin(8), freq=200000)
try:
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except:
    print("Ekran hatasi!")

# --- Notalar ---
NOTE_C4, NOTE_D4, NOTE_E4, NOTE_F4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_C5 = 262, 294, 330, 349, 392, 440, 494, 523
NOTE_FS4, NOTE_GS4, NOTE_AS4 = 370, 415, 466

# --- Şarkı Listeleri ---
selvi_boylum = [
    (NOTE_A4, 600), (NOTE_G4, 200), (NOTE_FS4, 200), (NOTE_G4, 200), (NOTE_E4, 800),
    (NOTE_E4, 200), (NOTE_C5, 200), (NOTE_E4, 200), (NOTE_D4, 800),
    (NOTE_D4, 200), (NOTE_B4, 200), (NOTE_C5, 200), (NOTE_B4, 200), (NOTE_D4, 200), (NOTE_C5, 200), (NOTE_B4, 200), (NOTE_A4, 400)
]
girdap = [
    (NOTE_A4, 200), (NOTE_B4, 200), (NOTE_B4, 400), (NOTE_B4, 400),
    (NOTE_A4, 200), (NOTE_B4, 200), (NOTE_C5, 200), (NOTE_B4, 200), (NOTE_B4, 400),
    (NOTE_A4, 200), (NOTE_C5, 200), (NOTE_B4, 200), (NOTE_A4, 200), (NOTE_G4, 200), (NOTE_FS4, 200), (NOTE_G4, 600)
]
hasret = [
    (NOTE_B4, 200), (NOTE_C5, 200), (NOTE_C5, 200), (NOTE_C5, 400),
    (NOTE_D4, 200), (NOTE_E4, 200), (NOTE_D4, 200), (NOTE_C5, 200), (NOTE_B4, 200), (NOTE_A4, 200), (NOTE_G4, 400)
]

# --- Pin Tanımlamaları ---
btn_act = Pin(3, Pin.IN, Pin.PULL_UP)
btn_nav = Pin(4, Pin.IN, Pin.PULL_UP)
bat_sense = ADC(Pin(1))
bat_sense.atten(ADC.ATTN_11DB)
buzzer = PWM(Pin(2))
buzzer.duty(0)

# --- Sistem Değişkenleri ---
game_state = "INTRO"
sound_on = True
vol_idx, diff_idx = 1, 1
volume_levels = [350, 750, 1023]
v_names = ["DUSUK", "ORTA", "FULL"]
diff_levels = ["KOLAY", "ORTA", "ZOR"]
current_sel, score = 0, 0

game_keys = ["FLAPPY", "BLOCK", "DINO", "SPACE", "RACE", "FROG"]
game_options = ["Domb Kusu", "Kat Cikmaca", "Domb Kosusu", "Uzay Savasi", "Retro Yaris", "Kurbaga"]

high_scores = {k: [0]*10 for k in game_keys}

# --- Fonksiyonlar ---
def save_scores():
    try:
        with open("scores.json", "w") as f:
            json.dump(high_scores, f)
    except:
        pass

def load_scores():
    global high_scores
    try:
        with open("scores.json", "r") as f:
            high_scores = json.load(f)
    except:
        pass

def update_highscore(game, new_score):
    if new_score <= 0 or game not in high_scores: return
    scores = high_scores[game]
    scores.append(new_score)
    scores.sort(reverse=True)
    high_scores[game] = scores[:10]
    save_scores()

def beep(freq, dur):
    if sound_on and volume_levels[vol_idx] > 0:
        try:
            buzzer.freq(freq)
            buzzer.duty(volume_levels[vol_idx])
            time.sleep_ms(dur)
            buzzer.duty(0)
        except:
            pass

def play_melody(melody_type):
    m = []
    if melody_type == "DOMB_THEME":
        m = [(NOTE_E4, 150), (NOTE_E4, 150), (0, 150), (NOTE_E4, 150), (0, 150), (NOTE_C4, 150), (NOTE_E4, 150), (0, 150), (NOTE_G4, 150)]
    elif melody_type == "CHIP_TUNE":
        m = [(NOTE_C4, 200), (NOTE_G4, 200), (NOTE_C5, 200), (NOTE_G4, 200), (NOTE_A4, 200), (NOTE_F4, 200)]
    
    for note, dur in m:
        if note == 0:
            time.sleep_ms(dur)
        else:
            beep(note, dur)
        time.sleep_ms(50)

def safe_show():
    try:
        oled.show()
    except:
        pass

def get_battery():
    try:
        raw = bat_sense.read()
        p = int((raw - 2100) * 100 / (2800 - 2100))
        return min(100, max(0, p))
    except:
        return 0

def draw_bat():
    p = get_battery()
    oled.rect(110, 2, 14, 7, 1)
    oled.fill_rect(110, 2, int(14 * (p/100)), 7, 1)
    oled.pixel(125, 4, 1)
    oled.pixel(125, 5, 1)

def draw_menu(title, options, selected):
    oled.fill(0)
    oled.text(title, 5, 2)
    draw_bat()
    oled.hline(0, 12, 128, 1)
    start_i = max(0, selected - 2)
    for i in range(start_i, min(len(options), start_i + 4)):
        y = 18 + ((i - start_i) * 11)
        if i == selected:
            oled.fill_rect(0, y-1, 128, 10, 1)
            oled.text("> " + options[i], 2, y, 0)
        else:
            oled.text("  " + options[i], 2, y, 1)
    safe_show()

def music_menu():
    m_sel = 0
    m_opts = ["Al Yazmalim", "Girdap", "Hasret", "Domb Theme", "GERI"]
    while True:
        draw_menu("MUZIK KUTUSU", m_opts, m_sel)
        if btn_nav.value() == 0:
            m_sel = (m_sel + 1) % 5
            beep(600, 20)
            time.sleep(0.2)
        if btn_act.value() == 0:
            if m_sel == 0:
                for n, d in selvi_boylum: beep(n, d); time.sleep_ms(50)
            elif m_sel == 1:
                for n, d in girdap: beep(n, d); time.sleep_ms(50)
            elif m_sel == 2:
                for n, d in hasret: beep(n, d); time.sleep_ms(50)
            elif m_sel == 3:
                play_melody("DOMB_THEME")
            elif m_sel == 4:
                break
            time.sleep(0.2)

def show_scores_menu():
    sub_sel = 0
    while True:
        draw_menu("SKORLAR", game_options + ["GERI"], sub_sel)
        if btn_nav.value() == 0:
            sub_sel = (sub_sel + 1) % 7
            beep(600, 20)
            time.sleep(0.2)
        if btn_act.value() == 0:
            if sub_sel == 6: break
            game_key = game_keys[sub_sel]
            while True:
                oled.fill(0)
                oled.text(game_options[sub_sel][:15], 5, 2)
                oled.hline(0, 12, 128, 1)
                for i in range(10):
                    s = high_scores[game_key][i]
                    y, x = (16 + (i*8), 5) if i < 5 else (16 + ((i-5)*8), 65)
                    oled.text(f"{i+1}.{s}", x, y)
                oled.text("< GERI", 40, 56)
                safe_show()
                if btn_act.value() == 0 or btn_nav.value() == 0:
                    beep(800, 20)
                    time.sleep(0.2)
                    break
            time.sleep(0.2)

def reset_vars():
    global bird_y, bird_v, pipe_x, pipe_h, block_w, block_x, block_y, direction, stack
    global dino_y, dino_v, obstacle_x, obs_type, is_jumping, ship_x, ship_dir
    global bullet_active, bullet_x, bullet_y, enemies, score, race_car_x, race_enemies, frog_y, frog_x, frog_cars
    score = 0
    bird_y, bird_v, pipe_x, pipe_h = 30, 0, 120, 20
    block_w, block_x, block_y, direction, stack = 40, 0, 56, 3, []
    dino_y, dino_v, obstacle_x, obs_type, is_jumping = 48, 0, 130, 0, False
    ship_x, ship_dir, bullet_active, bullet_x, bullet_y = 60, 4, False, 0, 0
    enemies = [[random.randint(10, 110), 10, 2], [random.randint(10, 110), 22, -2]]
    race_car_x = 60 
    race_enemies = [[random.choice([20, 60, 100]), -25], [random.choice([20, 60, 100]), -75]]
    frog_x, frog_y = 62, 56
    frog_cars = [[random.randint(0,120), 16, 2], [random.randint(0,120), 32, -3], [random.randint(0,120), 48, 2]]

# --- ANA DÖNGÜ ---
load_scores()
reset_vars()

while True:
    if game_state == "INTRO":
        for x in range(130, -65, -8):
            oled.fill(0)
            oled.text("DOMBBOX", x, 28)
            safe_show()
            time.sleep_ms(20)
            if btn_act.value() == 0 or btn_nav.value() == 0: break
        game_state = "MAIN_MENU"

    elif game_state == "MAIN_MENU":
        main_opts = ["Oyunlar", "Skorlar", "Muzik", "Ayarlar", "Yapimci"]
        draw_menu("DOMB-BOX", main_opts, current_sel)
        if btn_nav.value() == 0: 
            current_sel = (current_sel + 1) % 5
            beep(600, 20)
            time.sleep(0.2)
        if btn_act.value() == 0:
            if current_sel == 0: game_state = "SELECT_MENU"; current_sel = 0
            elif current_sel == 1: show_scores_menu(); current_sel = 1
            elif current_sel == 2: music_menu(); current_sel = 2
            elif current_sel == 3: game_state = "SETTINGS_MENU"; current_sel = 0
            elif current_sel == 4: game_state = "CREDITS"; current_sel = 0
            beep(1000, 40)
            time.sleep(0.2)

    elif game_state == "SETTINGS_MENU":
        s_opts = ["Ses: " + ("ACIK" if sound_on else "KAPALI"), "Ses S.: " + v_names[vol_idx], "Zorluk: " + diff_levels[diff_idx], "Skor Sifirla", "GERI"]
        draw_menu("AYARLAR", s_opts, current_sel)
        if btn_nav.value() == 0: 
            current_sel = (current_sel + 1) % 5
            beep(600, 20)
            time.sleep(0.2)
        if btn_act.value() == 0:
            if current_sel == 0: sound_on = not sound_on
            elif current_sel == 1: vol_idx = (vol_idx + 1) % 3
            elif current_sel == 2: diff_idx = (diff_idx + 1) % 3
            elif current_sel == 3: 
                high_scores = {k: [0]*10 for k in game_keys}
                save_scores()
                beep(200, 400)
            elif current_sel == 4: game_state = "MAIN_MENU"; current_sel = 3
            beep(1000, 40)
            time.sleep(0.2)

    elif game_state == "SELECT_MENU":
        sel_opts = game_options + ["GERI"]
        draw_menu("OYUNLAR", sel_opts, current_sel)
        if btn_nav.value() == 0: 
            current_sel = (current_sel + 1) % 7
            beep(600, 20)
            time.sleep(0.2)
        if btn_act.value() == 0:
            if current_sel < 6: 
                last_game = game_keys[current_sel]
                reset_vars()
                game_state = last_game
            else:
                game_state = "MAIN_MENU"
                current_sel = 0
            beep(1000, 40)
            time.sleep(0.2)

    elif game_state == "GAMEOVER":
        update_highscore(last_game, score)
        oled.fill(0)
        oled.text("BITTI!", 40, 15)
        oled.text("SKOR: "+str(score), 35, 30)
        safe_show()
        time.sleep(1)
        while btn_act.value() == 1 and btn_nav.value() == 1: pass
        game_state = "SELECT_MENU"

    elif game_state == "CREDITS":
        oled.fill(0)
        oled.text("YAPIMCI", 35, 10)
        oled.text("DombTech", 32, 30)
        oled.text("v1.0 Stable", 20, 50)
        safe_show()
        if btn_act.value() == 0 or btn_nav.value() == 0:
            game_state = "MAIN_MENU"
            current_sel = 4
            time.sleep(0.2)

    elif game_state in game_keys:
        if btn_nav.value() == 0:
            game_state = "SELECT_MENU"
            time.sleep(0.3)
            continue
        
        action = (btn_act.value() == 0)
        oled.fill(0)
        dm = diff_idx + 1

        if game_state == "SPACE":
            if action and not bullet_active:
                bullet_x, bullet_y, bullet_active = ship_x + 6, 50, True
                beep(2000, 5)
            for e in enemies:
                e[0] += e[2] * dm
                if e[0] > 115 or e[0] < 5: e[2] *= -1
                if bullet_active and abs(bullet_x - (e[0]+6)) < 10 and bullet_y < e[1]+8:
                    score += 1; bullet_active = False; e[0] = random.randint(10, 110); beep(1200, 10)
                oled.fill_rect(int(e[0]), e[1], 12, 7, 1)
            if bullet_active:
                bullet_y -= 6
                oled.fill_rect(bullet_x, bullet_y, 2, 6, 1)
                if bullet_y < 0: bullet_active = False
            ship_x += ship_dir
            oled.fill_rect(ship_x, 56, 14, 5, 1)
            if ship_x > 114 or ship_x < 2: ship_dir *= -1

        elif game_state == "RACE":
            if action:
                old_x = race_car_x
                race_car_x = 20 if race_car_x == 100 else (60 if race_car_x == 20 else 100)
                if old_x != race_car_x: score += 1; beep(400, 5)
                time.sleep(0.15)
            for en in race_enemies:
                en[1] += 3 + dm
                if en[1] > 64: en[1] = -30; en[0] = random.choice([20, 60, 100])
                if abs(en[1] - 48) < 18 and en[0] == race_car_x: game_state = "GAMEOVER"
                oled.fill_rect(en[0], en[1], 14, 18, 1)
            oled.fill_rect(race_car_x, 48, 14, 20, 1)
            oled.vline(42, 0, 64, 1)
            oled.vline(86, 0, 64, 1)

        elif game_state == "DINO":
            if action and not is_jumping: dino_v = -7; is_jumping = True; beep(600, 5)
            dino_y += dino_v
            if is_jumping: dino_v += 1
            if dino_y >= 48: dino_y = 48; is_jumping = False; dino_v = 0
            obstacle_x -= (3 + dm)
            if obstacle_x < -20: obstacle_x = 130; obs_type = random.randint(0, 2); score += 1
            if obs_type < 2:
                h = 10 if obs_type == 0 else 16
                if obstacle_x < 18 and obstacle_x > 5 and dino_y > (56 - h - 5): game_state = "GAMEOVER"
                oled.fill_rect(obstacle_x, 56-h, 7, h, 1)
            else:
                y_bird = 34 if diff_idx > 0 else 38
                if obstacle_x < 18 and obstacle_x > 5 and abs(dino_y - y_bird) < 8: game_state = "GAMEOVER"
                oled.fill_rect(obstacle_x, y_bird, 12, 6, 1)
            oled.fill_rect(10, int(dino_y), 11, 9, 1); oled.hline(0, 57, 128, 1)

        elif game_state == "FLAPPY":
            if action: bird_v = -3; beep(800, 5)
            bird_v += 1; bird_y += bird_v; pipe_x -= (2 + dm)
            if pipe_x < -15: pipe_x = 128; pipe_h = random.randint(10, 35); score += 1
            if bird_y < 0 or bird_y > 60 or (pipe_x < 22 and pipe_x > 5 and (bird_y < pipe_h or bird_y > pipe_h + 22)): game_state = "GAMEOVER"
            oled.fill_rect(15, int(bird_y), 9, 7, 1)
            oled.fill_rect(pipe_x, 0, 14, pipe_h, 1)
            oled.fill_rect(pipe_x, pipe_h+26, 14, 64, 1)

        elif game_state == "BLOCK":
            block_x += direction + (dm if direction > 0 else -dm)
            if block_x + block_w >= 128 or block_x <= 0: direction *= -1
            if action:
                if not stack: stack.append([block_x, 56, block_w]); score += 1; block_y = 48
                else:
                    px, py, pw = stack[-1]
                    nl, nr = max(block_x, px), min(block_x + block_w, px + pw)
                    if nr > nl:
                        block_w = nr - nl; block_x = nl; stack.append([block_x, block_y, block_w]); score += 1; beep(1000, 20)
                        if block_y <= 16:
                            for s in stack: s[1] += 8
                        else: block_y -= 8
                    else: game_state = "GAMEOVER"
                while btn_act.value() == 0: pass
            for s in stack: oled.fill_rect(s[0], s[1], s[2], 7, 1)
            oled.fill_rect(block_x, block_y, block_w, 7, 1)

        elif game_state == "FROG":
            if action: frog_y -= 8; time.sleep(0.1)
            if frog_y < 8: score += 1; frog_y = 56
            for c in frog_cars:
                c[0] = (c[0] + c[2]) % 135
                if abs(frog_y - c[1]) < 7 and frog_x < c[0]+22 and frog_x+6 > c[0]: game_state = "GAMEOVER"
                oled.fill_rect(int(c[0]), c[1], 24, 9, 1)
            oled.fill_rect(frog_x, frog_y, 7, 7, 1)

        oled.text(str(score), 110, 4)
        safe_show()
        time.sleep_ms(15)
