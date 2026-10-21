"""Offline behavioral fixtures; these never apply or guarantee an outcome."""


def economic_action(context: dict, intend):
    minute, here = context["minute"], context["perception"]["location"]
    hour = minute % 1440
    economy, inventory = context["economy"], context["inventory"]
    if context["needs"]["fullness"] < 38 and inventory["meals"]:
        return intend("eat", duration=30, text="I want to eat a meal I am carrying.")
    if context["needs"]["energy"] < 15:
        if here != context["self"]["home"]:
            return intend("move", target=context["self"]["home"], text="I need to go home to rest.")
        return intend("sleep", duration=120)
    if inventory["meals"] <= 1 and 480 <= hour < 1200:
        shops = []
        for shop in economy["known_shops"]:
            location = shop["location"]
            travel = context["travel_minutes"].get(location, 60)
            hours = context["opening_hours"][location]
            if not hours["opens"] <= hour + travel < hour + travel + 10 <= hours["closes"]:
                continue
            if context["account"]["cents"] < shop["price_cents"]:
                continue
            if shop["observed_stock"] == 0 and minute - shop["observed_at"] < 360:
                continue
            if location == here and economy["local_shop"]["stock"] == 0:
                continue
            shops.append((shop["price_cents"], travel, location))
        if shops:
            _, _, destination = min(shops)
            if here != destination:
                return intend("move", target=destination, text="I want to buy groceries.")
            shop = economy["local_shop"]
            quantity = min(3, shop["stock"], context["account"]["cents"] // shop["price_cents"])
            return intend("buy", duration=10, arguments={"item": "meal", "quantity": quantity})
    if context["town_app"]["unread_notices"] and 480 <= hour < 1260:
        return intend("read_news", duration=5, text="I want to check the town notice board.")
    for proposal in context["town_app"]["proposals"]:
        if (
            proposal["status"] == "open"
            and proposal["eligible"]
            and proposal["my_vote"] is None
            and minute + 5 < proposal["closes"]
        ):
            opinion = context["self"]["opinion"]
            choice = "yes" if opinion >= -0.2 else "no" if opinion < -0.4 else "abstain"
            return intend(
                "vote", duration=5, arguments={"proposal_id": proposal["id"], "choice": choice}
            )
    if context["needs"]["fullness"] < 38 and not inventory["meals"]:
        # Scarcity is not repaired by a fixture granting free inventory.
        if here != context["self"]["home"]:
            return intend(
                "move",
                target=context["self"]["home"],
                text="I need to reconsider food options at home.",
            )
        return intend("wait", duration=30, text="I have no food and need to reconsider my options.")
    return None
