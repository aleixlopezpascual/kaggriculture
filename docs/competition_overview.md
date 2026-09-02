# Kaggriculture Competition Specification & Rules Overview

This document provides a highly technical, deep-dive specification of the **Kaggle Kaggriculture** simulation competition. Kaggriculture is a 2-player head-to-head economic and farming simulator designed to model complex resource management, dynamic pricing, and concurrent labor scheduling.

---

## 📅 1. Game Horizon and Mechanics
* **Duration:** A 30-day season divided into 24 turns (hours) per day, totaling **720 discrete turns** (0 to 719).
* **Starting Budget:** Both players start with **$3,000** in cash.
* **Starting Land:** A 10x10 farm grid. Only the northwest 5x5 quadrant is active initially. The other three quadrants are locked.
* **Winning Condition:** Maximize your cash balance at turn 720. 
  - **Zero Salvage Value:** Unsold seeds, animals, raw goods, tools, and land carry **zero terminal value** at turn 720. Success is determined purely by liquid bank capital.

---

## 📈 2. Market Mechanics & Price Elasticity

The market has a decoupled buy/sell economy. You can always buy seeds and animals at fixed prices, but selling commodities affects their market prices dynamically based on global inventories.

### Fixed Buying Prices
* **Seeds:** Wheat seed ($5), Carrot seed ($10), Melon seed ($25), Strawberry seed ($40).
* **Animals:** Geese ($150), Sheep ($300), Cows ($500).

### Dynamic Selling Prices (Pricing Formula)
The selling price of any commodity depends on its global market inventory ($inv$), starting at a neutral inventory ($I_0 = 10,000$) for all items:

$$\text{price}(inv) = \max\left(1.0, \text{round}\left(\text{base\_price} + \text{sign} \times \text{amp} \times f(|inv - I_0|)\right)\right)$$

Where:
1. **$I_0$:** The base neutral supply (set to 10,000 units).
2. **$\text{sign}$:** $+1$ if $inv < I_0$ (scarcity, driving price up) and $-1$ if $inv > I_0$ (glut, driving price down).
3. **$\text{amp}$ (Amplitude):** Calculated as $\frac{\text{target\_impact} \times \text{base\_price}}{f(T)}$.
4. **$T$ (Anchor Throughput):** The theoretical crop/animal capacity of a single 5x5 grid over a 24-day season. (For animals, $T$ is discounted by 30% to account for wheat feed overhead).
5. **$f(x)$ (Shape Function):** Selects from `linear`, `sq` (quadratic), `sqrt`, or `log` (using $\ln(1+x)$).
6. **Price Floor:** Prices will never drop below **$1.00**.

### Staple vs. Premium Elasticity
* **Staple Goods (Wheat, Carrots):** High volume, high neutral capacity ($T$). They have highly elastic price curves that absorb massive gluts with relatively low price drops (e.g., maximum drop of ~24%).
* **Premium Goods (Melon, Strawberry, Milk, Wool, Eggs):** High base price, low neutral capacity ($T$). Even small market oversupplies (above-target gluts) drive their prices straight to the $1.00 floor.

### Order Execution Front-Running
* Market actions are processed sequentially across players, unit-by-unit (interleaved). 
* Order precedence within the action command array is critical:
  - If a player submits `SELL WHEAT 10` followed by `SELL CARROT 10`, the engine processes 1 wheat, then 1 carrot, dynamically adjusting the price with each individual transaction.
  - Champion agents sort and place high-value orders first to front-run the town consumption index and secure premium prices.

---

## 🌾 3. Agronomics (Crops Lifecycle)

The farm grid supports 100 tiles. Empty tiles must be tilled before planting.

| Crop Type | Seed Cost | Base Price | Growth (Days) | Water Need | Special Properties |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wheat** | $5 | $10 | 2 days | Daily | Required feed for Livestock |
| **Carrot** | $10 | $18 | 3 days | Daily | High-yield staple |
| **Melon** | $25 | $45 | 5 days | Daily | Highly vulnerable to glut pricing |
| **Strawberry** | $40 | $80 | 7 days | Daily | High return, long risk window |

### Crop Decay and Death
* **Watering:** Plants must be watered once per day.
* **Weather multipliers:** Sunny weather increases water depletion (e.g., -10 water/tick); rainy weather offsets it (-5 water/tick).
* **Withering:** If a plant is left unwatered for **two consecutive days**, it dies and turns into a **WEED**. Weeds yield nothing and must be cleared with a `DIG`/`TILL` action before replanting.
* **Fertilization:** Applying fertilizer doubles the plant's growth speed multiplier for the next 3 days.

---

## 🐄 4. Livestock (Animal Husbandry)

Animals are compounding cash-flow engines. They live in pastures or coops and produce indefinitely as long as they are cared for.

| Animal | Purchase Cost | Housing | Feed Required | Base Product | Yield Interval | Care Bonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Goose** | $150 | Coop | Wheat (Daily) | Egg | Every 2 days | +1 Care multi |
| **Sheep** | $300 | Pasture | Wheat (Daily) | Wool | Every 4 days | +1 Care multi |
| **Cow** | $500 | Pasture | Wheat (Daily) | Milk | Every 3 days | +1 Care multi |

### Care & Feeding Rules
* **Feeding:** Animals must be fed exactly 1 unit of harvested Wheat daily. If an animal goes unfed for **two consecutive days**, it escapes/dies and is removed from the farm.
* **Care Bonus (+1 Multiplier):** Applying a `CARE` action increases the animal's happiness index. Maintaining high care scores triggers compounding yields, making animals significantly more profitable than crops over long horizons.
* **Fertilizer:** Livestock generate Fertilizer over time as a by-product, which can be harvested and used to speed up crop cycles.

---

## 👷 5. Labor & Land Scaling

The environment begins with the main farmer, but you can scale your operations.

### Hired Farm Hands
* **Base Capacity:** The farmer gets 24 action points (APs) per day (1 per hour).
* **Farm Hands:** You can hire additional hands using `HIRE` at the start of the day. Each hired hand adds 24 APs (moves and acts in parallel).
* **Fibonacci Wage Curve:** The daily wage for hired hands scales exponentially using the Fibonacci sequence:
  - 1 Hand: $1 / day
  - 2 Hands: $2 / day
  - 3 Hands: $3 / day
  - 5 Hands: $5 / day
  - 10 Hands: $143 / day
  - *Strategic Margin:* Hiring up to 3–5 hands is highly cost-effective; hiring 10+ hands requires extremely high crop throughput to justify the wage.

### Land Quadrant Purchases
* Grid is divided into four 5x5 quadrants: NW (Active), NE (Locked), SW (Locked), SE (Locked).
* Locked quadrants can be purchased with the `BUY_LAND` action for a price that escalates with each subsequent quadrant bought.

---

## 📥 6. Observation JSON Structure

Each turn (hour), your agent receives a JSON state observation:

```json
{
  "player": 0,
  "day": 5,
  "hour": 14,
  "farms": [
    {
      "money": 2450.50,
      "farmer": [3, 4],
      "tiles": [
        // Grid array (flat 100 items for 10x10)
        // Values: null (empty), "LOCKED", or tile object:
        {
          "kind": "PLANT",
          "crop": "MELON",
          "planted_day": 2,
          "watered_today": true,
          "consecutive_unwatered": 0,
          "yield_units": 1,
          "max_lifespan_step": 240,
          "fertilized_until_day": 5
        }
      ]
    },
    { "money": 3100.0, "farmer": [1, 2], "tiles": [...] } // Opponent
  ],
  "market": {
    "inventories": { "WHEAT": 10500, "CARROT": 9800, "MELON": 10000, "STRAWBERRY": 10000 },
    "prices": { "WHEAT": 9.50, "CARROT": 18.20, "MELON": 45.00, "STRAWBERRY": 80.00 }
  },
  "private": {
    "shed": { "WHEAT": 12, "FERTILIZER": 4 },
    "seeds": { "WHEAT": 4, "CARROT": 2 },
    "inventories": [
      ["WHEAT", "WHEAT"], // Farmer's bag
      []                  // Hired Hand 1's bag
    ]
  }
}
```

---

## 📤 7. Action JSON Structure

Your agent returns actions for all active workers (the farmer + hired hands) along with market orders:

```json
{
  "farmer": ["MOVE", "N"],
  "hands": [
    ["WATER"],
    ["HARVEST"]
  ],
  "market": [
    ["BUY_SEED", "WHEAT", 5],
    ["SELL", "WHEAT", 10],
    ["HIRE"],
    ["BUY_LAND"]
  ]
}
```

---

## 🏆 8. Strategic Roadmap for AI Architecture

To dominate the ladder, our implementation must capitalize on several meta behaviors discovered in the competition:

1. **Market Front-Running (Order Priority):** High-value luxury items (Melons, Milk, Strawberries) must be sold first inside the command array to capture the maximum available town demand price before the market gluts.
2. **Self-Sustaining Livestock Loops:** Cows and Sheep are the highest-margin engines. However, they eat 1 wheat daily. An optimal agent schedules a cyclic pipeline where a dedicated quadrant grows Wheat to feed 8 Cows / 4 Sheep, producing highly profitable Milk and Wool, while using their by-product Fertilizer to speed up the wheat cycles.
3. **Optimized Labor Scheduling:** Using 3–5 hands is highly profitable. Our agents must run pathfinding algorithms (like A* search or heuristic grid sweep) to ensure workers do not waste APs moving unnecessarily. Keeping the shed central and using `DROP`/`PICKUP` efficiently is a major bottleneck.
4. **Finite-Horizon Salvage Clean-out:** At Turn 700+, we must stop buying seeds, stop feeding animals, harvest all remaining assets, and dump our entire inventory onto the market to maximize terminal liquidity.
