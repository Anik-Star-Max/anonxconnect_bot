import database

async def get_top():
    users = database._load_users()
    ranking = []
    for u in users.values():
        if u.get("allow_account", False):
            ranking.append((u["name"], len(u.get("referrals",[]))))
    ranking.sort(key=lambda x: x[1], reverse=True)
    msg = "🏆 <b>Top Referrals</b> 🏆\n"
    for idx, (name, count) in enumerate(ranking[:10], 1):
        msg += f"{idx}. {name} — {count} referrals\n"
    return msg if ranking else "No referrals yet."
