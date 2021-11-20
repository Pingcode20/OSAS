# Ship constant definitions

# Weight class for any ship
size_any = 'Any'

# Weight classes
size_drone = 'Drone'
size_destroyer = 'Destroyer'
size_cruiser = 'Cruiser'
size_capital = 'Capital'

# Subtypes
subtype_drone = size_drone
subtype_destroyer = size_destroyer
subtype_cruiser = size_cruiser
subtype_capital = size_capital
subtype_bomber = 'Bomber'
subtype_anti_cruiser = 'Cruiser Targeting'

# Attack types
attack_type_any = 'starship'
attack_type_drone = size_drone
attack_type_destroyer = size_destroyer
attack_type_cruiser = size_cruiser
attack_type_capital = size_capital

# AI types
ai_bully = 'Bully'
ai_saturate = 'Saturate'
ai_random = 'Random'

# Ship Stats
stat_quantity = 'quantity'
stat_attack = 'attack'
stat_defence = 'defense'
stat_saturation = 'saturation'
stat_speed = 'speed'
stat_jump = 'jump'
stat_hull = 'hull'
stat_slots = 'slot'
stat_aegis = 'aegis'
stat_targeting = 'targeting order'
stat_tactics = 'tactics'
stat_overload = 'overload'
stat_devastate = 'devastate'
stat_current_hull = 'current hull'

# Enumerations
targeting_orders = {
    size_drone: [size_drone, size_destroyer, size_cruiser, size_capital],
    size_destroyer: [size_drone, size_destroyer, size_cruiser, size_capital],
    size_cruiser: [size_destroyer, size_cruiser, size_drone, size_capital],
    size_capital: [size_capital, size_cruiser, size_destroyer, size_drone],
    subtype_bomber: [size_destroyer, size_cruiser, size_capital, size_drone],
    subtype_anti_cruiser: [size_cruiser, size_capital, size_destroyer, size_drone],
}

hull_types = [size_drone, size_destroyer, size_cruiser, size_capital]

ai_types = [ai_bully, ai_saturate, ai_random]
