import random

def random_distribution(free, skills):
    distribution = skills.copy()
    skill_names = list(skills.keys())
    while free > 0:
        skill = random.choice(skill_names)
        if distribution[skill] < 6:
            distribution[skill] += 1
            free -= 1
    
    return distribution

def dice(skills: dict, name_skill: str, hard: int):
    cube_1 = random.randint(1, 6)
    cube_2 = random.randint(1, 6)
    print(cube_1, cube_2)
    result = skills[name_skill] + cube_1 + cube_2
    
    if hard >= 14:
        if result < 7:
            return cube_1, cube_2, 'смерть'
        elif result < hard:
            return cube_1, cube_2, 'неудача'
        return cube_1, cube_2, 'успех'
        
    if result < hard:
        return cube_1, cube_2, 'неудача'
        
    elif result >= hard:
        return cube_1, cube_2, 'успех'
    

def final_choise(scores: int, events: int):
    final_score = scores / events
    if final_score < 3:
        return "Резко-негативная концовка: (персонажи не достигли цели, персонажи смертельно больны/ранены, миру угрожает опасность.)"
    if 3 <= final_score < 6:
        return "Негативная концовка: (персонажи не достигли цели, персонажи больны или не сильно ранены, мир не сильно изменился)."
    if 6 <= final_score < 9:
        return "Нейтральная: (персонажи не достигли цели, персонажи не изменились, мир остался таким, каким был раньше)"
    if 9 <= final_score < 12:
        return "Положительная: (персонажи достигли цели, жизнь персонажей стала лучше, мир стал чуть лучше.)"
    if 12 <= final_score < 16:
        return "Резко положительная: (персонажи достигли цели наилучшим способом, мир изменился в лучшую сторону, персонажи обрели всеобщее признание, их жизнь кардинально изменилась в лучшую сторону.)"
