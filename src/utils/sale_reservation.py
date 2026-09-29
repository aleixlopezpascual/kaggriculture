class BoundedSaleReservation:
    def __init__(self):
        self.debt_records = {}  # item -> qty
        self.current_shop_block = None

    def process_turn_with_future(self, state, current_actions, future_actions_tape):
        step = state.turn
        block = step // 72

        # Reset debt records at shop block transitions
        if self.current_shop_block != block:
            self.current_shop_block = block
            self.debt_records.clear()

        # 1. Debt Settlement Pass
        adjusted_actions = []
        for action in current_actions:
            if isinstance(action, tuple) and len(action) == 3 and action[0] == "SELL":
                item, qty = action[1], action[2]
                debt = self.debt_records.get(item, 0)
                if debt > 0:
                    if qty > debt:
                        adjusted_actions.append(("SELL", item, qty - debt))
                        self.debt_records[item] = 0
                    else:
                        self.debt_records[item] = debt - qty
                else:
                    adjusted_actions.append(action)
            else:
                adjusted_actions.append(action)

        # 2. Sliding Window Lookahead Pass (Only active during steps 288 to 695)
        if 288 <= step <= 695:
            # Check physical shed inventory
            avail_stock = dict(state.farm.inventory)
            # Subtract currently scheduled sales to get safe surplus
            for action in adjusted_actions:
                if (
                    isinstance(action, tuple)
                    and len(action) == 3
                    and action[0] == "SELL"
                ):
                    item, qty = action[1], action[2]
                    avail_stock[item] = max(0, avail_stock.get(item, 0) - qty)

            # Check future tape actions
            for f_action in future_actions_tape[:5]:  # lookahead limit of 5
                if (
                    isinstance(f_action, tuple)
                    and len(f_action) == 3
                    and f_action[0] == "SELL"
                ):
                    f_item, f_qty = f_action[1], f_action[2]

                    # Exclude items needed for animal/seed purchase/feeding
                    if any(
                        act[0] == "BUY_PRODUCT" and act[1] == f_item
                        for act in current_actions
                    ):
                        continue

                    if avail_stock.get(f_item, 0) >= f_qty:
                        # Pull sale early
                        adjusted_actions.insert(0, ("SELL", f_item, f_qty))
                        self.debt_records[f_item] = (
                            self.debt_records.get(f_item, 0) + f_qty
                        )
                        avail_stock[f_item] -= f_qty

        return adjusted_actions
