import telebot
from telebot import types
import openai 
from config import TOKEN, PATH, OPENAI_API_KEY_RU, OPENAI_API_KEY_EN, STICKERS_API
from categories import cat 
from pictures import Text2ImageAPI, temp_picture, save_picture, rus_to_eng, dalle_picture_save
from algorithms import random_distribution, dice, final_choise
import re

bot = telebot.TeleBot(TOKEN)

client = openai.Client(api_key=OPENAI_API_KEY_RU, base_url="https://api.proxyapi.ru/openai/v1")
# client = openai.Client(api_key=OPENAI_API_KEY_EN)

# ключевая информация об игре
world_info = {}
# контекст для gpt
game_context = {}
# персонажи игры
characters = {}
info_for_creation = {}
# расы мира
races_dict = {}
# словарь создания персонажа
selected_race = {}
# id чата игры
global_chat_id = None
# флаг начала игры
game_started = False

final_cat = False


# cтарт в личке
@bot.message_handler(commands=['start'])
def private(message):
    if message.chat.type == "private": 
        if message.text.startswith("/start setup_"):
            markup = types.InlineKeyboardMarkup()
            choose_race = types.InlineKeyboardButton("Выбор расы", callback_data="choose_race")
            markup.add(choose_race)
            bot.send_message(message.chat.id, "Настроить своего персонажа можно по кнопке cнизу ⬇️", reply_markup=markup)
            if message.chat.id not in info_for_creation:
                info_for_creation[message.chat.id] = []

        else:
            markup = telebot.types.InlineKeyboardMarkup()
            adding = telebot.types.InlineKeyboardButton("Добавить в группу", url="https://t.me/pocket_dnd_bot?startgroup=true")
            markup.add(adding)
        
            bot.send_message(
                message.chat.id, 
                '🐉 Для начала игры добавьте меня в группу',
                reply_markup=markup
            )


# перезапуск игры(начало)
@bot.message_handler(commands=['reset'])
def restart_game(message):
    global game_started
    if game_started:
        markup = types.InlineKeyboardMarkup()
        start_game = types.InlineKeyboardButton("Подтвердить действие", callback_data="end")
        markup.add(start_game)

        bot.send_message(message.chat.id, '*‼️ Вы точно хотите завершить игру? 😢* \n\n_Это действие необратимо и приведет к полному сбросу всех игровых данных_', parse_mode="Markdown", reply_markup=markup)

    else:
        bot.send_message(message.chat.id, '*Игра еще не начата*', parse_mode="Markdown")

# перезапуск игры(конец)
@bot.callback_query_handler(func=lambda call: call.data == "end")
def clear_all(call):
    global world_info, game_context, characters, races_dict, selected_race, game_started, info_for_creation
    world_info = {}
    game_context = {}
    characters = {}
    info_for_creation = {}
    races_dict = {}
    selected_race = {}
    game_started = False

    markup = types.InlineKeyboardMarkup()
    reload = types.InlineKeyboardButton("Начать игру заново", callback_data="reload")
    markup.add(reload)
    
    bot.send_message(call.message.chat.id, '*Игра сброшена ✅*', parse_mode="Markdown", reply_markup=markup)

# повторный запуск игры
@bot.callback_query_handler(func=lambda call: call.data == "reload")
def start_again(call):
    global global_chat_id
    global_chat_id = call.message.chat.id
    info('reload')

# задания(служебная)
def info(task):
    if task == 'reload':
        global global_chat_id, game_started
        markup = types.InlineKeyboardMarkup()
        start_game = types.InlineKeyboardButton("Начать игру ✅", callback_data="start_game")
        rules = types.InlineKeyboardButton("Правила 📋", callback_data="print_rules")
        markup.add(start_game, rules, row_width=2)

        with open('pictures/start_game.jpg', 'rb') as image_file:
            bot.send_photo(
                global_chat_id, 
                photo=image_file, 
                caption="*Приветствую, отважные исследователи! 🌍✨* \n\n *Я - ваш верный помощник в мире Dungeons & Dragons! 🎲*\n\n _Позвольте мне взять на себя все сложные механики игры, чтобы вы могли наслаждаться приключениями и весельем без лишних забот. \n\n Приготовьтесь к увлекательному путешествию в миры, полные захватывающих событий и неожиданных поворотов! Давайте вместе создадим захватывающую историю!_ 🌌🎉", reply_markup=markup, parse_mode='Markdown', 
            )
        game_started = True

        return

# cтарт в чате
@bot.my_chat_member_handler()
def first_chat(update):
    if update.chat.type != "private":  
        print('start')
        global global_chat_id, game_started
        if update.new_chat_member.status == "member":
            bot.send_message(update.chat.id, "*Для запуска игры дайте мне права администратора* 👾", parse_mode='Markdown')
        elif update.new_chat_member.status == "administrator":
            global_chat_id = update.chat.id

            markup = types.InlineKeyboardMarkup()
            start_game = types.InlineKeyboardButton("Начать игру ✅", callback_data="start_game")
            rules = types.InlineKeyboardButton("Правила 📋", callback_data="print_rules")
            markup.add(start_game, rules, row_width=2)

            with open('pictures/start_game.jpg', 'rb') as image_file:
                bot.send_photo(
                    update.chat.id, 
                    photo=image_file, 
                    caption="*Приветствую, отважные исследователи! 🌍✨* \n\n *Я - ваш верный помощник в мире Dungeons & Dragons! 🎲*\n\n _Позвольте мне взять на себя все сложные механики игры, чтобы вы могли наслаждаться приключениями и весельем без лишних забот. \n\n Приготовьтесь к увлекательному путешествию в миры, полные захватывающих событий и неожиданных поворотов! Давайте вместе создадим захватывающую историю!_ 🌌🎉", reply_markup=markup, parse_mode='Markdown', 
                )
            game_started = True


@bot.callback_query_handler(func=lambda call: call.data == "print_rules")
def show_rules(call):
    markup = types.InlineKeyboardMarkup()
    back = types.InlineKeyboardButton("Назад", callback_data="reload")
    markup.add(back)

    bot.send_message(global_chat_id, "Приготовьтесь к приключениям! ⚔️🎲\n\nДобро пожаловать в мир бота, где вас ждут увлекательные истории и захватывающие события!\n\nВот как играть:\n\n1. *Создание мира* 🗺:\n\n• Выберите один из уже существующих миров или создайте свой собственный, используя свою фантазию! 💫\n• От простой жизни на Земле до волшебных миров, от мира милых фей до острова вечной мерзлоты - выбирайте, что вам по душе! 😉\n\n2. *Создание персонажей* 🦸‍♀️🦸‍♂️:\n\n• Играйте в компании от 2 до 6 человек! 👫👬👭\n• Настройте своего персонажа 🎲\n• На выбор вам дается 6 рас, уникальных для каждого мира, с собственной внешностью и набором характеристик. 🧝‍♀️🧛‍♂️\n\n*Характеристики:*\n\n• В игре 6 характеристик, уникальных для каждого мира. 🧠💪\n• Чем выше характеристика, тем больше шансов на успех! 🚀\n\n3. *Игра* 🎲:\n\n• Мир создан, персонажи готовы - начинаются события! 🔥\n• Цель игры определяется выбранным приключением. 🎯\n• У вас есть 4 варианта действий для решения каждого события. \n• Описание действия подскажет, какой навык вам нужен. 💡\n• У каждого действия есть сложность от 8 (очень легко) до 15 (смертельно опасно). ☠️\n• Подбросьте 2 кубика и добавьте к их сумме нужный навык. 🎲\n• Если результат больше сложности - вы справились! 🥳\n• Неудачный результат - не беда, история продолжается! 😉\n• Обсуждайте с друзьями, кто и как будет действовать! 🗣\n\n4. *Концовка* 🏆:\n\n• В игре 5 разных концовок (не считая смерть). \n• Начните игру и откройте их для себя! \n\nГотовы к приключениям? Тогда в путь! 🏃‍♀️🏃‍♂️", parse_mode='Markdown', reply_markup=markup)

    

# выбор настройки мира
@bot.callback_query_handler(func=lambda call: call.data == "start_game")
def handle_start_game(call):
    global game_started
    markup_w = types.InlineKeyboardMarkup()
    choose_wrld = types.InlineKeyboardButton("Выбрать категорию", callback_data="choose_cat")
    own_wrld = types.InlineKeyboardButton("Задать категорию", callback_data="own_cat")
    global global_chat_id
    global_chat_id = call.message.chat.id

    markup_w.add(choose_wrld, own_wrld, row_width=2)

    bot.send_message(call.message.chat.id, "*Настройте мир 🌏:* \n\n1) Выберите сеттинг из заготовленных категорий 👁 \n\n2) Введите свой сеттинг ✍️\n\n❗️_Данный вариант игры является нестабильным, разработчик не несет ответственности за стабильность работы бота :)_", reply_markup=markup_w, parse_mode='Markdown')
    game_started = True


# выбор категории(запуск)
@bot.callback_query_handler(func=lambda call: call.data == "choose_cat")
def categories(call):
    page_number = 0
    send_category_page(call.message, page_number)


cat_list = list(cat.keys())

# отправка категории
def send_category_page(message, page_number):
    category_key = cat_list[page_number]
    category_data = cat[category_key]
    text = category_data[0]
    image_path = f"{PATH}{category_data[1]}"  

    with open(image_path, 'rb') as image_file:
        bot.send_photo(
            message.chat.id, 
            image_file, 
            caption=text, 
            reply_markup=create_pagination_keyboard_cat(page_number),
            parse_mode='Markdown'
        )

# ввод своей категории
@bot.callback_query_handler(func=lambda call: call.data == "own_cat")
def own_category(call):
    input_wrld = bot.send_message(call.message.chat.id, "🌏 Введите свою категорию мира:")
    bot.register_next_step_handler(input_wrld, process_own_category)

# проверка категории
def process_own_category(message):
    user_category = message.text
    if len(user_category) <= 40:
        generate_world(message.chat.id, user_category)
    else:
        markup_w = types.InlineKeyboardMarkup()
        own_wrld = types.InlineKeyboardButton("Задать категорию", callback_data="own_cat")

        markup_w.add(own_wrld)
        bot.send_message(message.chat.id, "*Длина сеттинга не должна превышать 30 символов.* \nПожалуйста, введите сеттинг повторно:", reply_markup=markup_w)


# генерация мира 
def generate_world(chat_id, setting):
    world_info[global_chat_id] = [setting]
    create = bot.send_sticker(global_chat_id, STICKERS_API[0])
    gen = f"Ты ведущий для моей новой игры, создай мир для игры с сеттингом - {setting}, соблюдай строгий шаблон. Название мира; Краткое описание мира; 4 кратких описания приключения как для DND для этого мира. Добавь немного эмодзи в свое сообщение. Оформи сообщение в стиле Markdown."
    markup = telebot.types.InlineKeyboardMarkup()
    choose_adv = types.InlineKeyboardButton("Выбрать приключение", callback_data="choose_adv")
    sorry = types.InlineKeyboardButton("Перегенерировать", callback_data="sorry")
    markup.add(choose_adv, sorry, row_width=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": gen}],
        max_tokens=1200
    )

    output = response.choices[0].message.content.replace("#", "")
    game_context[chat_id] = [{"role": "user", "content": gen}, {"role": "assistant", "content": output}]

    bot.delete_message(global_chat_id, create.message_id)
    generat = bot.send_sticker(global_chat_id, STICKERS_API[1])

    prompt_small = 'Выведи единым текстом краткое описание мира из прошлой генерации(без дополнительных слов)'

    game_context[chat_id].append({"role": "user", "content": prompt_small})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=game_context[chat_id],
        max_tokens=500
    )

    small_disc = response.choices[0].message.content
    game_context[chat_id].append({"role": "assistant", "content": small_disc})

    temp_picture(small_disc)

    with open(PATH + 'game_assets/temp.png', 'rb') as image_file:
        bot.send_photo(chat_id, image_file)

    bot.send_message(chat_id, output, parse_mode='Markdown', reply_markup=markup)
    bot.delete_message(global_chat_id, generat.message_id)
    

# выбор приключения и рас
@bot.callback_query_handler(func=lambda call: call.data.startswith(("choose_adv", "adv_")))
def adventure_choose(call):
    if call.data == "choose_adv":
        markup = types.InlineKeyboardMarkup(row_width=4)
        for k in range(1, 5):
            markup.add(types.InlineKeyboardButton(f"{k}", callback_data=f"adv_{k}"))
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        adv_number = call.data.split("_")[1]
        prompt = f"Выведи название приключения {adv_number} (без markdown)"
        game_context[call.message.chat.id].append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[call.message.chat.id],
            max_tokens=30
        )

        adventure = response.choices[0].message.content
        game_context[call.message.chat.id].append({"role": "assistant", "content": adventure})
        bot.answer_callback_query(call.id, f"Вы выбрали приключение: {adventure}")
        race = bot.send_sticker(global_chat_id, STICKERS_API[3])  
        world_info[global_chat_id].append(adventure)

        prompt_race = 'Теперь выведи 6 рас для жителей этого мира, их краткое описание и предустановленные для них характеристики(6 штук), чье значение варьируется от 0 до 6. Сумма всех навыков СТРОГО НЕ БОЛЬШЕ 6(например 1 + 0 + 3 + 1 + 1 + 0). Можешь добавить эмодзи. Обязательно используй Markdown'

        game_context[call.message.chat.id].append({"role": "user", "content": prompt_race})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[call.message.chat.id],
            max_tokens=1200
        )


        races = response.choices[0].message.content.replace("#", "")
        game_context[call.message.chat.id].append({"role": "assistant", "content": races})

        bot_username = bot.get_me().username
        rl = f"https://t.me/{bot_username}?start=setup_"

        markup = types.InlineKeyboardMarkup()
        go_to_private = types.InlineKeyboardButton("🧝🏻‍♀️ Настроить персонажа", url=rl)
        markup.add(go_to_private)

        global races_dict

        prompt_races_dict = 'Верни из этого описания рас в формате словаря все расы. Напиши только код(без маркдауна(```py), только словарь). Формат словаря: ключ - название, значение - список, где первый элемент - описание расы, а второй - вложенный словарь, где ключи - характеристики(из прошлого промпта), а значения - значения характеристик для каждой расы(тоже из прошлого промпта)'
        game_context[call.message.chat.id].append({"role": "user", "content": prompt_races_dict})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[call.message.chat.id]
        )

        races_dict = eval(response.choices[0].message.content)
        game_context[call.message.chat.id].append({"role": "assistant", "content": str(races_dict)})

        bot.send_message(call.message.chat.id, races, parse_mode='Markdown', reply_markup=markup)
        bot.delete_message(call.message.chat.id, race.message_id)


# начало настройки персонажа и выбор расы
@bot.callback_query_handler(func=lambda call: call.data.startswith('choose_race'))
def choose_race(call):
    page_number = 0
    send_race_page(call.message, page_number)

# запуск пагинации для рас
def send_race_page(message, page_number):
    race_name = list(races_dict.keys())[page_number]
    race_info = races_dict[race_name][0]  
    race_stats = races_dict[race_name][1]

    race_stats_formatted = "\n".join([f"*{stat}*: {value}" for stat, value in race_stats.items()])
    
    text=f"*{race_name}*\n\n{race_info}\n\n*Характеристики:*\n\n{race_stats_formatted}"
    
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=create_pagination_keyboard_race(page_number),
        parse_mode='Markdown'
    )

# инлайн сообщение о балансе
@bot.callback_query_handler(func=lambda call: call.data == "sorry")
def balance(call):
    bot.answer_callback_query(call.id, "К сожалению, из-за ограниченого баланса и проблем с API ключами, повторная генерация недоступна 😭")

# создание пагинации для сеттинга
def create_pagination_keyboard_cat(page_number):
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    left_button = types.InlineKeyboardButton("⬅️", callback_data=f"left_c:{page_number}")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"select_c:{page_number}")
    right_button = types.InlineKeyboardButton("➡️", callback_data=f"right_c:{page_number}")

    if page_number > 0:
        keyboard.add(left_button)
    
    keyboard.add(select_button)
    
    if page_number < len(cat_list) - 1:
        keyboard.add(right_button)
    
    return keyboard


# обработка кнопок для сеттинга
@bot.callback_query_handler(func=lambda call: call.data.startswith(('left_c', 'right_c', 'select_c', 'generate_world')))
def callback_query(call):
    global final

    action = call.data.split(':')[0] if ':' in call.data else call.data

    if action.startswith('left_c') or action.startswith('right_c') or action.startswith('select_c'):
        page_number = int(call.data.split(':')[1])

        if action == "left_c" and page_number > 0:
            page_number -= 1
        elif action == "right_c" and page_number < len(cat_list) - 1:
            page_number += 1
        elif action == "select_c":
            final = cat_list[page_number]
            markup = types.InlineKeyboardMarkup()
            comeback = types.InlineKeyboardButton("Вернуться к выбору", callback_data="choose_cat")
            generate = types.InlineKeyboardButton("Сгенерировать мир", callback_data="generate_world")

            markup.add(comeback, generate)

            global final_cat

            final_cat = bot.send_message(call.message.chat.id, f"Вы выбрали: {final}", reply_markup=markup)

            return

        image_path = f"{PATH}{cat[cat_list[page_number]][1]}"
        with open(image_path, 'rb') as image_file:
            bot.edit_message_media(
                media=types.InputMediaPhoto(
                    media=image_file,
                    caption=cat[cat_list[page_number]][0],
                    parse_mode='Markdown'
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=create_pagination_keyboard_cat(page_number)
            )       
    
    elif action == 'generate_world':
        bot.delete_message(global_chat_id, final_cat.message_id)
        generate_world(call.message.chat.id, final)

# создание пагинации для рас
def create_pagination_keyboard_race(page_number):
    keyboard = types.InlineKeyboardMarkup()
    
    left_button = types.InlineKeyboardButton("⬅️", callback_data=f"left_r:{page_number}")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"select_r:{page_number}")
    right_button = types.InlineKeyboardButton("➡️", callback_data=f"right_r:{page_number}")
    
    if page_number > 0:
        keyboard.add(left_button)
    
    keyboard.add(select_button)
    
    if page_number < len(races_dict) - 1:
        keyboard.add(right_button)
    
    return keyboard

# обработка кнопок для рас
@bot.callback_query_handler(func=lambda call: call.data.startswith(('left_r', 'right_r', 'select_r')))
def handle_race_selection(call):
    action = call.data.split(':')[0]
    page_number = int(call.data.split(':')[1])

    if action == "left_r" and page_number > 0:
        page_number -= 1
    elif action == "right_r" and page_number < len(races_dict) - 1:
        page_number += 1
    elif action == "select_r":
        global race_name
        race_name = list(races_dict.keys())[page_number]

        info_for_creation[call.message.chat.id].append(race_name)
        print(info_for_creation)

        # if global_chat_id not in characters:
        #     characters[global_chat_id] = {}

        # if call.message.chat.id not in characters[global_chat_id]:
        #     characters[global_chat_id][call.message.chat.id] = [race_name]


        selected_race[call.message.chat.id] = {
            'name': race_name,
            'info': races_dict[race_name][0],
            'stats': races_dict[race_name][1]
        }

        markup = types.InlineKeyboardMarkup()
        comeback = types.InlineKeyboardButton("Вернуться к выбору ⬅️", callback_data="choose_race")
        next_step = types.InlineKeyboardButton("Далее ✅", callback_data="skills")
        markup.add(comeback, next_step)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"*Вы выбрали расу: {race_name}🧝🏻‍♀️✨*\nТеперь давайте _настроим вашего персонажа!_",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return
    

    race_name = list(races_dict.keys())[page_number]
    race_info = races_dict[race_name][0]  
    race_stats = races_dict[race_name][1]

    race_stats_formatted = "\n".join([f"*{stat}*: {value}" for stat, value in race_stats.items()])
    
    text=f"*{race_name}*\n\n{race_info}\n\n*Характеристики:*\n\n{race_stats_formatted}"
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=create_pagination_keyboard_race(page_number),
        parse_mode='Markdown'
    )

skills_final = None

# настройка скиллов
@bot.callback_query_handler(func=lambda call: call.data.startswith(("skills", "shuffle", "save")))
def define_skills(call):
    if call.data == "skills":
        markup = types.InlineKeyboardMarkup()
        shuffle = types.InlineKeyboardButton("Бросить кубики 🎲", callback_data="shuffle")
        markup.add(shuffle)

        bot.send_message(call.message.chat.id, '*Узнаем характеристики вашего персонажа*', reply_markup=markup, parse_mode='Markdown')
    
    elif call.data == "shuffle":
        global skills_final
        race_data = selected_race.get(call.message.chat.id)
        if race_data:
            race_stats = race_data['stats']

        free = 16 - sum(race_stats.values())
        skills_final = random_distribution(free, race_stats)

        def format_skill_value(value):
            red = "🟥"
            yellow = "🟨"
            green = "🟩"
            empty = "⬛️"

            if value in [0, 1, 2]:
                color = red
            elif value in [3, 4]:
                color = yellow
            elif value in [5, 6]:
                color = green

            return color * value + empty * (6 - value)

        formatted_skills = "\n".join([f"*{key.capitalize()}:* {format_skill_value(value)}" for key, value in skills_final.items()])

        markup = types.InlineKeyboardMarkup()
        shuffle_button = types.InlineKeyboardButton("Перераспределить 🎲", callback_data="shuffle")
        save_button = types.InlineKeyboardButton("Сохранить ✅", callback_data="save")
        markup.add(shuffle_button, save_button)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'*Узнаем характеристики вашего персонажа*\n\n{formatted_skills}',
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    elif call.data == 'save':
        info_for_creation[call.message.chat.id].insert(1, skills_final)
        race = selected_race[call.message.chat.id]['name']

        race_stick = bot.send_sticker(call.message.chat.id, STICKERS_API[2])        
        prompt_player = f'Создай теперь игрового персонажа для этого сеттинга. Раса - {race}. Характеристики - {skills_final}. Дай мне его имя и краткое описание внешности, характеристик(как достоинств, так и недостатков), связь с миром. Не больше 4 предложений. Все, кроме имени, в один параграф'

        game_context[global_chat_id].append({"role": "user", "content": prompt_player})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[global_chat_id],
            max_tokens=800
        )

        character = response.choices[0].message.content.replace("#", "")
        game_context[global_chat_id].append({"role": "assistant", "content": character})
        

        prompt_pers = 'Создай теперь список питон(без маркдауна(```py), только список), где первый элемент - имя персонажа, а второй - текст описания только его внешности(без характеристик и связи с миром). Верни ТОЛЬКО код'
        game_context[global_chat_id].append({"role": "user", "content": prompt_pers})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[global_chat_id],
            max_tokens=300
        )
        global character_list
        character_list = eval(response.choices[0].message.content)
        game_context[global_chat_id].append({"role": "assistant", "content": str(character_list)})
        info_for_creation[call.message.chat.id].insert(0, character_list[0])
        info_for_creation[call.message.chat.id].insert(2, character_list[1])

        markup_p = types.InlineKeyboardMarkup()
        balance_button_p = types.InlineKeyboardButton("Перегенерировать 🎲", callback_data="sorry")
        save_pers_button_p = types.InlineKeyboardButton("Сохранить персонажа ✅", callback_data="pers")
        markup_p.add(balance_button_p, save_pers_button_p)

        global char_path
        char_path = save_picture(character_list[0], character_list[1])

        # characters[global_chat_id][call.message.chat.id].insert(0, character_list[0])
        # characters[global_chat_id][call.message.chat.id].insert(2, character_list[1])
        info_for_creation[call.message.chat.id].append(char_path)
        print(info_for_creation)

        with open(char_path, 'rb') as image_file:
            bot.send_photo(call.message.chat.id, image_file, caption=character, reply_markup=markup_p, parse_mode='Markdown')

        bot.delete_message(call.message.chat.id, race_stick.message_id)


# завершение настройки персонажа и отправка сообщения о нем в чат
@bot.callback_query_handler(func=lambda call: call.data == "pers")
def pers_save(call):
    global global_chat_id
    character_data = info_for_creation[call.message.chat.id]
    username = call.from_user.username if call.from_user.username else f"Пользователь {call.message.chat.id}"
    character_name = character_data[0]
    race = character_data[1]
    skills = character_data[3]

    if global_chat_id not in characters:
            characters[global_chat_id] = {}



    existing_characters_count = len(characters[global_chat_id])


    if existing_characters_count >= 6:
        bot.send_message(call.message.chat.id, "*Максимальное количество персонажей для игры уже достигнуто!* 😢")
        return

    bot.send_message(call.message.chat.id, "*Вы успешно настроили своего персонажа!* 🎉")

    if call.message.chat.id not in characters[global_chat_id]:
        characters[global_chat_id][call.message.chat.id] = [character_name, race, character_data[2], skills, character_data[-1]]
    
    print(characters)

    formatted_skills = "\n".join([f"*{key.capitalize()}*: {value}" for key, value in skills.items()])
    main_chat_message = (
        f"*{username}* создал персонажа:\n\n"
        f"*Имя*: {character_name}\n\n"
        f"*Раса*: {race}\n\n"
        f"*Характеристики:*\n\n{formatted_skills}\n\n"
    )

    existing_characters_count = len(characters[global_chat_id])
    characters_created_message = f"Персонажей уже создали - {', '.join([f'@{bot.get_chat_member(global_chat_id, user_id).user.username or user_id}' for user_id in characters[global_chat_id].keys()])} ({existing_characters_count})"

    main_chat_message += characters_created_message

    file_path = characters[global_chat_id][call.message.chat.id][-1]


    if existing_characters_count >= 2:
        markup = types.InlineKeyboardMarkup()
        start_game_button = types.InlineKeyboardButton("Запустить игру 🎮", callback_data="game_started")
        markup.add(start_game_button)
        with open(file_path, 'rb') as image_file:
            bot.send_photo(
                global_chat_id, 
                photo=image_file, 
                caption=main_chat_message, 
                reply_markup=markup, 
                parse_mode='Markdown', 
            )
    elif existing_characters_count >= 6:
        markup = types.InlineKeyboardMarkup()
        start_game_button = types.InlineKeyboardButton("Запустить игру 🎮", callback_data="game_started")
        markup.add(start_game_button)
        bot.send_message(global_chat_id, "Достигнуто *максимальное количество персонажей*. Вы можете начать игру, используя кнопку ниже.")
        with open(file_path, 'rb') as image_file:
            bot.send_photo(
                global_chat_id, 
                photo=image_file, 
                caption=main_chat_message, 
                reply_markup=markup, 
                parse_mode='Markdown', 
            )
    else:
        with open(file_path, 'rb') as image_file:
            bot.send_photo(
                global_chat_id, 
                photo=image_file, 
                caption=main_chat_message, 
                parse_mode='Markdown', 
            )

# начало цикла самой игры
@bot.callback_query_handler(func=lambda call: call.data == "game_started")
def main_game(call):
    global event_count
    event_count = 5

    markup = types.InlineKeyboardMarkup()
    up_button = types.InlineKeyboardButton("⬆️", callback_data="increase_event_count")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data="select_event_count")
    down_button = types.InlineKeyboardButton("⬇️", callback_data="decrease_event_count")

    markup.add(up_button)
    markup.add(select_button)
    markup.add(down_button)
    bot.send_message(call.message.chat.id, f'Настройте количество игровых событий: {event_count}', reply_markup=markup)

# выбор количества событий
@bot.callback_query_handler(func=lambda call: call.data in ["increase_event_count", "decrease_event_count", "select_event_count"])
def adjust_event_count(call):
    global event_count

    if call.data == "increase_event_count":
        if event_count < 15:
            event_count += 1
        else:
            bot.answer_callback_query(call.id, "✖️Максимальное количество событий — 15", show_alert=True)

    elif call.data == "decrease_event_count":
        if event_count > 5:
            event_count -= 1
        else:
            bot.answer_callback_query(call.id, "✖️Минимальное количество событий — 5", show_alert=True)

    elif call.data == "select_event_count":
        final_events = event_count
        world_info[global_chat_id].append(final_events)
        markup = types.InlineKeyboardMarkup()
        start_cycle = types.InlineKeyboardButton("⬆️", callback_data="start_game_cycle")
        markup.add(start_cycle)
        bot.send_message(call.message.chat.id, f'*Игра началась!✨🎮*\n\n_Сеттинг мира: {world_info[global_chat_id][0]}_\n_Ваше приключение: {world_info[global_chat_id][1]}_', parse_mode='Markdown', reply_markup=markup)
        game_started = True
        return
    
    markup = types.InlineKeyboardMarkup()
    up_button = types.InlineKeyboardButton("⬆️", callback_data="increase_event_count")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data="select_event_count")
    down_button = types.InlineKeyboardButton("⬇️", callback_data="decrease_event_count")
    markup.add(up_button)
    markup.add(select_button)
    markup.add(down_button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Настройте количество игровых событий: {event_count}', reply_markup=markup)
    
formula_end_sum = 0

# Начало событий
@bot.callback_query_handler(func=lambda call: call.data == "start_game_cycle")
def main_game(call):
    count = world_info[global_chat_id][2]
    adventure = world_info[global_chat_id][1]

    intro_prompt = f'Правила. Всего в игре ровно {count} событий. Каждое из событий должно быть связано с приключением "{adventure}", которое ты генерировал ранее в описании мира и у которого есть цель. Давай нам одно событие и 4 варианта действий для него c разметкой Markdown, которые задействуют какую-то из характеристик мира и все разной сложности(от 8 до 15, где 8 - самое легкое, а 15 - смертельно опасное)(вариант ответа должен иметь название, которое кратко(1 или 2 слова) описывает действие). Сначала строка - название характеристики, необходимой для этого действия, а под ней строка с показателем сложности. У выбора уровня сложности должно быть логичное обоснование. В любой момент игры ты можешь сгенерировать встречу с жителем этого мира. Я говорю тебе исход события и персонажа, чьи способности мы использовали, а также, при наличии смертельной опасности, произошла ли смерть или нет. Твоя задача, сгенерировать новое событие, по тем же правилам, основываясь на результате действия(получилось/не получилось; позитивное/негативное событие соответственно) и делай так каждый раз. События должны быть последовательны, чтобы в конце можно было составить логическую цепочку, которая привела к развязке - цели приключения. Последнее событие ОБЯЗАТЕЛЬНО ДОЛЖНО быть развязкой. Если никто из персонажей не умер, игра может закончиться по-разному, я скажу тебе, к какой концовке все пришло. Смертельная опасность может быть только в событиях со сложностью 14 и 15, в описании к таким событиям обязательно должно быть указано наличие смертельной опасности. Сейчас сразу выдай мне текст первого события(заголовок, краткое описание, 4 варианта действия с разной сложностью. К каждом событию добавь немного эмодзи и всегда используй markdown)'

    game_context[global_chat_id].append({"role": "user", "content": intro_prompt})

    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[call.message.chat.id],
            max_tokens = 1000
        )
    
    first_adv = response.choices[0].message.content.replace("#", "")













    
    game_context[global_chat_id].append({"role": "assistant", "content": first_adv})

    choises_dict = 'Верни из этого описания события в формате словаря все варианты действий. Напиши только код(без маркдауна(```py), только словарь). Формат словаря: ключ - номер варианта действия(цифрой), значение - список, где первый элемент - сложность события, а второй - характеристика, которая используется'

    game_context[global_chat_id].append({"role": "user", "content": choises_dict})

    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[call.message.chat.id],
        )
    
    global event_dict

    event_dict = eval(response.choices[0].message.content)
    game_context[global_chat_id].append({"role": "assistant", "content": str(event_dict)})

    event_dict = {int(key): value for key, value in event_dict.items()}

    print(event_dict)

    markup = types.InlineKeyboardMarkup(row_width=2)
    for idx, (name, details) in enumerate(event_dict.items()):
        button = types.InlineKeyboardButton(name, callback_data=f"confirm_choice:{idx}")
        markup.add(button)

    bot.send_message(call.message.chat.id, first_adv, parse_mode="Markdown", reply_markup=markup)

# Подтвержение варианта действия
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_choice:"))
def confirm_choice(call):
    event_idx = int(call.data.split(':')[1])
    event_names = list(event_dict.keys())
    event_name = event_names[event_idx]
    difficulty, skill = event_dict[event_name]

    confirm_markup = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Назад", callback_data="cancel_choice")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"choice_selected:{event_idx}")
    confirm_markup.add(cancel_button, select_button, row_width=2)

    bot.send_message(call.message.chat.id, f"Вы уверены, что хотите выбрать вариант '{event_name}'?\n\n*Сложность:* {difficulty}\n*Характеристика:* {skill}", reply_markup=confirm_markup, parse_mode="Markdown")

# Отмена
@bot.callback_query_handler(func=lambda call: call.data == "cancel_choice")
def cancel_choice(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# Выбор персонажа
@bot.callback_query_handler(func=lambda call: call.data.startswith("choice_selected:"))
def select_choice(call):
    event_idx = int(call.data.split(':')[1])
    
    
    characters_in_game = characters[global_chat_id]
    
    character_markup = types.InlineKeyboardMarkup(row_width=2)
    for user_id, character_info in characters_in_game.items():
        character_name = character_info[0]
        character_button = types.InlineKeyboardButton(character_name, callback_data=f"perform_action:{event_idx}:{user_id}")
        character_markup.add(character_button)

    bot.send_message(call.message.chat.id, "*Выберите персонажа для совершения действия:*", reply_markup=character_markup)
    bot.delete_message(call.message.chat.id, call.message.message_id)

# Детали персонажа
@bot.callback_query_handler(func=lambda call: call.data.startswith("perform_action:"))
def show_character_info(call):
    _, event_idx, user_id = call.data.split(':')
    event_idx = int(event_idx)
    user_id = int(user_id)

    character_info = characters[global_chat_id][user_id]
    character_name = character_info[0]
    race = character_info[1]
    skills = character_info[3]
    photo = character_info[-1]

    formatted_skills = "\n".join([f"*{key.capitalize()}*: {value}" for key, value in skills.items()])
    character_message = (
        f"*Имя персонажа:* {character_name}\n\n"
        f"*Раса:* {race}\n\n"
        f"*Характеристики:*\n\n{formatted_skills}"
    )

    character_markup = types.InlineKeyboardMarkup(row_width=2)
    back_button = types.InlineKeyboardButton("Назад", callback_data=f"cancel_character_info:{event_idx}")
    select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"finalize_choice:{event_idx}:{user_id}")
    character_markup.add(back_button, select_button)

    with open(photo, 'rb') as image_file:
            bot.send_photo(
                call.message.chat.id, 
                photo=image_file, 
                caption=character_message, 
                parse_mode='Markdown',
                reply_markup=character_markup 
            )

# отмена
@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_character_info:"))
def cancel_character_info(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# бросок кубиков
@bot.callback_query_handler(func=lambda call: call.data.startswith("finalize_choice:"))
def throw_dice(call):
    _, event_idx, user_id = call.data.split(':')
    event_idx = int(event_idx)
    user_id = int(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    dice = types.InlineKeyboardButton("Кинуть кубики 🎲", callback_data=f'dice:{event_idx}:{user_id}')
    markup.add(dice)
    bot.send_message(call.message.chat.id, 'Узнайте итог события по кнопке внизу!', reply_markup=markup)
    bot.delete_message(call.message.chat.id, call.message.message_id)

# итоги
@bot.callback_query_handler(func=lambda call: call.data.startswith("dice:"))
def throw_dice(call):
    _, event_idx, user_id = call.data.split(':')
    event_idx = int(event_idx) + 1
    user_id = int(user_id)
    character_info = characters[global_chat_id][user_id]
    character_name = character_info[0]
    skills = character_info[3]


    dice1, dice2, test_result = dice(skills, event_dict[event_idx][1], event_dict[event_idx][0])
    bot.send_message(call.message.chat.id, f'*🎲 Значения на кубиках: {dice1}, {dice2}*\n\nРезультат события: {test_result}')
    global formula_end_sum
    if test_result == 'неудача':
        formula_end_sum += event_dict[event_idx][0] * 0.2
    elif test_result == 'успех':
        formula_end_sum += event_dict[event_idx][0]
    else:
        formula_end_sum = -1
    bot.delete_message(call.message.chat.id, call.message.message_id)

    basic_generation(call.message.chat.id, game_context, event_idx, character_name, test_result, formula_end_sum, dead=False)

#     game_cycle(call.message.chat.id, game_context, event_idx, character_name, test_result)


# # def game_cycle(chat_id, initial_game_context, initial_event_idx, initial_character_name, initial_test_result):
# #     game_context = initial_game_context
# #     event_idx = initial_event_idx
# #     character_name = initial_character_name
# #     test_result = initial_test_result
# #     max_events = world_info[chat_id][-1]  
# #     global formula_end_sum
# #     formula_end_sum = 0  

# #     for i in range(2, max_events):
# #         dead = (formula_end_sum == -1)

# #         game_context, event_idx, character_name, test_result, formula_end_sum = basic_generation(
# #             chat_id, game_context, event_idx, character_name, test_result, formula_end_sum, dead
# #         )


    










def basic_generation(chat_id, game_context, event_idx, character_name, test_result, formula_end_sum, dead=False):
    if dead == False:
        create = bot.send_sticker(global_chat_id, STICKERS_API[4])
        gen_prompt = f'Выбранное действие: {event_idx}, персонаж: {character_name}, результат: {test_result}'
        game_context[chat_id].append({"role": "user", "content": gen_prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[chat_id],
            max_tokens = 1000
        )
        action = response.choices[0].message.content
        game_context[global_chat_id].append({"role": "assistant", "content": action})
        bot.delete_message(global_chat_id, create.message_id)
        choises_dict = 'Верни из этого описания события в формате словаря все варианты действий. Напиши только код(без маркдауна(```py), только словарь). Формат словаря: ключ - номер варианта действия(цифрой), значение - список, где первый элемент - сложность события, а второй - характеристика, которая используется'

        game_context[global_chat_id].append({"role": "user", "content": choises_dict})

        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=game_context[chat_id],
            )
        
        global event_dict

        event_dict = eval(response.choices[0].message.content)
        game_context[global_chat_id].append({"role": "assistant", "content": str(event_dict)})

        event_dict = {int(key): value for key, value in event_dict.items()}

        print(event_dict)

        markup = types.InlineKeyboardMarkup(row_width=2)
        for idx, (name, details) in enumerate(event_dict.items()):
            button = types.InlineKeyboardButton(name, callback_data=f"confirm_choice:{idx}")
            markup.add(button)

        bot.send_message(chat_id, action, parse_mode="Markdown", reply_markup=markup)

        # Подтвержение варианта действия
        @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_choice:"))
        def confirm_choice(call):
            event_idx = int(call.data.split(':')[1])
            event_names = list(event_dict.keys())
            event_name = event_names[event_idx]
            difficulty, skill = event_dict[event_name]

            confirm_markup = types.InlineKeyboardMarkup()
            cancel_button = types.InlineKeyboardButton("Назад", callback_data="cancel_choice")
            select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"choice_selected:{event_idx}")
            confirm_markup.add(cancel_button, select_button, row_width=2)

            bot.send_message(call.message.chat.id, f"Вы уверены, что хотите выбрать вариант '{event_name}'?\n\n*Сложность:* {difficulty}\n*Характеристика:* {skill}", reply_markup=confirm_markup, parse_mode="Markdown")

        # Отмена
        @bot.callback_query_handler(func=lambda call: call.data == "cancel_choice")
        def cancel_choice(call):
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # Выбор персонажа
        @bot.callback_query_handler(func=lambda call: call.data.startswith("choice_selected:"))
        def select_choice(call):
            event_idx = int(call.data.split(':')[1])
            
            
            characters_in_game = characters[global_chat_id]
            
            character_markup = types.InlineKeyboardMarkup(row_width=2)
            for user_id, character_info in characters_in_game.items():
                character_name = character_info[0]
                character_button = types.InlineKeyboardButton(character_name, callback_data=f"perform_action:{event_idx}:{user_id}")
                character_markup.add(character_button)

            bot.send_message(call.message.chat.id, "*Выберите персонажа для совершения действия:*", reply_markup=character_markup)
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # Детали персонажа
        @bot.callback_query_handler(func=lambda call: call.data.startswith("perform_action:"))
        def show_character_info(call):
            _, event_idx, user_id = call.data.split(':')
            event_idx = int(event_idx)
            user_id = int(user_id)

            character_info = characters[global_chat_id][user_id]
            character_name = character_info[0]
            race = character_info[1]
            skills = character_info[3]
            photo = character_info[-1]

            formatted_skills = "\n".join([f"*{key.capitalize()}*: {value}" for key, value in skills.items()])
            character_message = (
                f"*Имя персонажа:* {character_name}\n\n"
                f"*Раса:* {race}\n\n"
                f"*Характеристики:*\n\n{formatted_skills}"
            )

            character_markup = types.InlineKeyboardMarkup(row_width=2)
            back_button = types.InlineKeyboardButton("Назад", callback_data=f"cancel_character_info:{event_idx}")
            select_button = types.InlineKeyboardButton("Выбрать", callback_data=f"finalize_choice:{event_idx}:{user_id}")
            character_markup.add(back_button, select_button)

            with open(photo, 'rb') as image_file:
                    bot.send_photo(
                        call.message.chat.id, 
                        photo=image_file, 
                        caption=character_message, 
                        parse_mode='Markdown',
                        reply_markup=character_markup 
                    )

        # отмена
        @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_character_info:"))
        def cancel_character_info(call):
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # бросок кубиков
        @bot.callback_query_handler(func=lambda call: call.data.startswith("finalize_choice:"))
        def throw_dice(call):
            _, event_idx, user_id = call.data.split(':')
            event_idx = int(event_idx)
            user_id = int(user_id)
            markup = types.InlineKeyboardMarkup(row_width=2)
            dice = types.InlineKeyboardButton("Кинуть кубики 🎲", callback_data=f'dice:{event_idx}:{user_id}')
            markup.add(dice)
            bot.send_message(call.message.chat.id, 'Узнайте итог события по кнопке внизу!', reply_markup=markup)
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # итоги события
        @bot.callback_query_handler(func=lambda call: call.data.startswith("dice:"))
        def throw_dice(call):
            _, event_idx, user_id = call.data.split(':')
            event_idx = int(event_idx) + 1
            user_id = int(user_id)
            character_info = characters[global_chat_id][user_id]
            character_name = character_info[0]
            skills = character_info[3]

            dice1, dice2, test_result = dice(skills, event_dict[event_idx][1], event_dict[event_idx][0])
            bot.send_message(call.message.chat.id, f'*🎲 Значения на кубиках: {dice1}, {dice2}*\n\nРезультат события: {test_result}')
            bot.delete_message(call.message.chat.id, call.message.message_id)

            if test_result == 'неудача':
                formula_end_sum += event_dict[event_idx][0] * 0.2
            elif test_result == 'успех':
                formula_end_sum += event_dict[event_idx][0]
            else:
                formula_end_sum = -1
                

            return game_context, event_idx, character_name, test_result, formula_end_sum
        
    else:
        ending = final_choise(formula_end_sum, world_info[chat_id][-1])
        prompt = f"Это финальное событие, после него новых событий нет. Предыдущие выборы привели к {ending}"
        game_context[global_chat_id].append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=game_context[global_chat_id],
            max_tokens=1000
        )
        finall = eval(response.choices[0].message.content)

        bot.send_message(global_chat_id, finall)



    

    





print('bot polling')
bot.polling()