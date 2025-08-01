import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
from game_classes import *  # Импортируем все наши игровые классы из предыдущего кода

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные для хранения состояния игры
players = {}
battles = {}

# Оружие и противники (инициализируем один раз)
sword = Weapon("Стальной меч", 15)
bow = Weapon("Длинный лук", 10)
enemies = {
    "goblin": Enemy("Гоблин", 60, 60, Weapon("Ржавый кинжал", 8)),
    "orc": Enemy("Орк", 120, 120, Weapon("Топор", 12), 20)
}

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    players[user_id] = None  # Сбрасываем персонажа при новом старте
    
    keyboard = [
        [InlineKeyboardButton("Воин ⚔️", callback_data='warrior')],
        [InlineKeyboardButton("Лучник 🏹", callback_data='archer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎮 Добро пожаловать в RPG Battle Bot!\n"
        "Выберите класс персонажа:",
        reply_markup=reply_markup
    )

# Обработка выбора персонажа
async def choose_class(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    choice = query.data
    
    if choice == 'warrior':
        players[user_id] = Warrior(query.from_user.first_name)
        players[user_id].weapon = sword
        text = f"⚔️ Вы выбрали Воина {query.from_user.first_name}!\nHP: 150/150\nОружие: {sword.name} (урон: {sword.damage})"
    elif choice == 'archer':
        players[user_id] = Archer(query.from_user.first_name)
        players[user_id].weapon = bow
        text = f"🏹 Вы выбрали Лучника {query.from_user.first_name}!\nHP: 80/80\nОружие: {bow.name} (урон: {bow.damage})\nСтрелы: 10"
    
    keyboard = [
        [InlineKeyboardButton("Гоблин 🐲", callback_data='goblin')],
        [InlineKeyboardButton("Орк 👹", callback_data='orc')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text + "\n\nВыберите противника:",
        reply_markup=reply_markup
    )

# Обработка выбора противника
async def choose_enemy(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    enemy_choice = query.data
    
    if user_id not in players or players[user_id] is None:
        await query.edit_message_text("Сначала выберите персонажа командой /start")
        return
    
    player = players[user_id]
    enemy = enemies[enemy_choice].__copy__()  # Создаем копию противника для каждого боя
    
    # Инициализируем бой
    battles[user_id] = {
        'player': player,
        'enemy': enemy,
        'message_id': query.message.message_id  # Для редактирования сообщения
    }
    
    await send_battle_status(user_id, context, "Битва началась!")

# Отправка/обновление статуса боя
async def send_battle_status(user_id, context: CallbackContext, action_text=""):
    battle = battles.get(user_id)
    if not battle:
        return
    
    player = battle['player']
    enemy = battle['enemy']
    
    text = (
        f"⚔️ {player.name} vs {enemy.name} ⚔️\n\n"
        f"{player.name} {player.get_hearts()} {player.health}/{player.max_health} HP\n"
        f"{enemy.name} {enemy.get_hearts()} {enemy.health}/{enemy.max_health} HP\n\n"
        f"Последнее действие: {action_text}\n\n"
        "Выберите действие:"
    )
    
    keyboard = []
    if isinstance(player, Warrior):
        cooldown_text = " (🔁)" if player.current_cooldown > 0 else ""
        keyboard.append([InlineKeyboardButton(f"Мощный удар 💥{cooldown_text}", callback_data='power_strike')])
    elif isinstance(player, Archer):
        keyboard.append([InlineKeyboardButton(f"Выстрел 🏹 (Осталось: {player.arrows})", callback_data='shoot')])
    
    keyboard.extend([
        [InlineKeyboardButton("Атаковать ⚔️", callback_data='attack')],
        [InlineKeyboardButton("Лечение ❤️ (+20 HP)", callback_data='heal')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=battle['message_id'],
            text=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")

# Обработка действий в бою
async def battle_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    if user_id not in battles:
        await query.edit_message_text("Бой не найден. Начните новую игру с /start")
        return
    
    battle = battles[user_id]
    player = battle['player']
    enemy = battle['enemy']
    action_text = ""
    
    # Обработка действий игрока
    if action == 'attack':
        player.attack(enemy)
        action_text = f"{player.name} атакует {enemy.name}!"
    elif action == 'power_strike' and isinstance(player, Warrior):
        player.power_strike(enemy)
        action_text = f"{player.name} использует Мощный удар!"
    elif action == 'shoot' and isinstance(player, Archer):
        player.shoot(enemy)
        action_text = f"{player.name} стреляет в {enemy.name}!"
    elif action == 'heal':
        player.heal(20)
        action_text = f"{player.name} восстанавливает здоровье!"
    
    # Проверка на победу/поражение
    if not enemy.is_alive:
        await query.edit_message_text(
            f"🎉 Победа! {player.name} победил {enemy.name}!\n\n"
            f"Получено {enemy.exp_reward} опыта ✨\n\n"
            "Начать новую игру: /start"
        )
        battles.pop(user_id, None)
        return
    
    # Ход противника
    if player.is_alive:
        enemy.attack(player)
        action_text += f"\n{enemy.name} атакует в ответ!"
    
    # Проверка на поражение
    if not player.is_alive:
        await query.edit_message_text(
            f"☠️ Поражение! {player.name} был побежден {enemy.name}!\n\n"
            "Попробуйте снова: /start"
        )
        battles.pop(user_id, None)
        return
    
    # Обновляем статус боя
    await send_battle_status(user_id, context, action_text)

# Обработка ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update.callback_query:
        await update.callback_query.edit_message_text("Произошла ошибка. Пожалуйста, начните заново: /start")

# Основная функция
def main() -> None:
    # Создаем приложение и передаем токен бота
    application = Application.builder().token("7612154166:AAHYYcUwQK8WTAzV9zgqb2U5qh8jSvcgS9c").build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(choose_class, pattern='^(warrior|archer)$'))
    application.add_handler(CallbackQueryHandler(choose_enemy, pattern='^(goblin|orc)$'))
    application.add_handler(CallbackQueryHandler(battle_action, pattern='^(attack|power_strike|shoot|heal)$'))
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()