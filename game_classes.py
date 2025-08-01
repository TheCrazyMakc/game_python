class Character:
    def __init__(self, name, max_health, health, weapon=None):
        self.name = name
        self.max_health = max_health
        self.health = health
        self.weapon = weapon
        self.is_alive = True

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            print(f"{self.name} погиб! 💀")
        else:
            hearts = self.get_hearts()
            print(f"{self.name} получил {damage} урона. {hearts}")

    def get_hearts(self):
        heart_count = round(self.health / self.max_health * 10)
        return "❤️" * heart_count + "🖤" * (10 - heart_count)

    def attack(self, target):
        if self.weapon:
            damage = self.weapon.damage
            print(f"{self.name} атакует {target.name} с помощью {self.weapon.name}! ⚔️")
            target.take_damage(damage)
        else:
            damage = 5
            print(f"{self.name} атакует {target.name} кулаками! 👊")
            target.take_damage(damage)

# Класс игрока
class Player(Character):
    def __init__(self, name, max_health=100, health=100, weapon=None):
        super().__init__(name, max_health, health, weapon)
        self.experience = 0
        self.level = 1
        
    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)
        hearts = self.get_hearts()
        print(f"{self.name} восстановил {amount} HP. {hearts}")

# Класс противника
class Enemy(Character):
    def __init__(self, name, max_health=50, health=50, weapon=None, exp_reward=10):
        super().__init__(name, max_health, health, weapon)
        self.exp_reward = exp_reward
    
    def __copy__(self):
        return Enemy(self.name, self.max_health, self.max_health, 
                   Weapon(self.weapon.name, self.weapon.damage) if self.weapon else None, 
                   self.exp_reward)

# Класс воина
class Warrior(Player):
    def __init__(self, name):
        super().__init__(name, max_health=150, health=150)
        self.special_ability_cooldown = 3
        self.current_cooldown = 0
        
    def power_strike(self, target):
        if self.current_cooldown <= 0:
            damage = 30 + (self.weapon.damage if self.weapon else 0)
            print(f"{self.name} использует МОЩНЫЙ УДАР по {target.name}! 💥")
            target.take_damage(damage)
            self.current_cooldown = self.special_ability_cooldown
        else:
            print(f"Способность перезаряжается! Осталось ходов: {self.current_cooldown} 🔄")
            self.attack(target)
            
    def end_turn(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

# Класс лучника
class Archer(Player):
    def __init__(self, name):
        super().__init__(name, max_health=80, health=80)
        self.arrows = 10
        
    def shoot(self, target):
        if self.arrows > 0:
            damage = 25 + (self.weapon.damage if self.weapon else 0)
            print(f"{self.name} стреляет в {target.name}! 🏹")
            target.take_damage(damage)
            self.arrows -= 1
        else:
            print("Нет стрел! 🚫 Используется обычная атака.")
            self.attack(target)
            
    def restock_arrows(self, amount):
        self.arrows += amount
        print(f"{self.name} пополнил запас стрел. Теперь {self.arrows} стрел 🎯")

# Класс оружия
class Weapon:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

# Механика сражения
class Battle:
    @staticmethod
    def fight(player, enemy):
        print(f"\n=== ⚔️ БИТВА: {player.name} vs {enemy.name} ⚔️ ===")
        
        while player.is_alive and enemy.is_alive:
            # Ход игрока
            print("\n--- Ваш ход ---")
            print(f"1. Атака ({player.weapon.name if player.weapon else 'кулаки'})")
            
            if isinstance(player, Warrior):
                print(f"2. Мощный удар {'(готово)' if player.current_cooldown <= 0 else '(перезарядка)'}")
            elif isinstance(player, Archer):
                print(f"2. Выстрел из лука (осталось стрел: {player.arrows})")
                
            print("3. Лечение (+20 HP)")
            
            action = input("Выберите действие (1-3): ")
            
            if action == "1":
                player.attack(enemy)
            elif action == "2":
                if isinstance(player, Warrior):
                    player.power_strike(enemy)
                elif isinstance(player, Archer):
                    player.shoot(enemy)
            elif action == "3":
                player.heal(20)
            else:
                print("Неверный ввод, пропуск хода ❌")
                
            if isinstance(player, Warrior):
                player.end_turn()
            
            # Проверка на победу
            if not enemy.is_alive:
                print(f"\n⭐ {player.name} победил {enemy.name}! ⭐")
                if isinstance(player, Player):
                    player.experience += enemy.exp_reward
                    print(f"Получено {enemy.exp_reward} опыта! ✨")
                return True
                
            # Ход противника
            print("\n--- Ход противника ---")
            enemy.attack(player)
            
            # Проверка на поражение
            if not player.is_alive:
                print(f"\n☠️ {player.name} был побежден {enemy.name}! ☠️")
                return False