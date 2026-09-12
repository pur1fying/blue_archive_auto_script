"""Migrate positional shop selections when the Global catalog changes."""


def migrate_tactical_challenge_shop_list(server_mode, goods):
    """Keep old choices when Global moves AP first and adds Miyu third.

    The legacy 16 slots are six students, two AP items, then eight supplies.
    The new 17 slots are two AP items, Miyu, six students, then supplies.
    Existing 17-slot selections and other servers are left unchanged.
    """
    if server_mode == "Global" and len(goods) == 16:
        return goods[6:8] + [0] + goods[:6] + goods[8:]
    return goods
