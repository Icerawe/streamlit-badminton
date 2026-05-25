from database import RANKS, RANK_INDEX

# Match categories with pair rank constraints [min_rank, max_rank]
# Each pair slot is [allowed_min, allowed_max] (inclusive on both ends)
MATCH_CATEGORIES = {
    "BG1": {
        "label": "BG1",
        "pairs": {
            1: ["BG1", "BG1"],
        }
    },
    "BG2/NB": {
        "label": "BG2/NB",
        "pairs": {
            1: ["BG2", "BG2"],
            2: ["BG1", "N"],
        }
    },
    "N": {
        "label": "N",
        "pairs": {
            1: ["N", "N"],
            2: ["BG2", "N+"],
            3: ["BG1", "S"],
        }
    },
    "N/S": {
        "label": "N/S",
        "pairs": {
            1: ["N", "S"],
            2: ["N+", "N+"],
            3: ["BG2", "P-"],
        }
    },
    "S": {
        "label": "S",
        "pairs": {
            1: ["S", "S"],
            2: ["N+", "P-"],
        }
    },
    "P": {
        "label": "P",
        "pairs": {
            1: ["P", "P"],
            2: ["P-", "P+"],
        }
    },
}


def pair_matches(rank_a: str, rank_b: str, r1: str, r2: str) -> bool:
    """Return True if {rank_a, rank_b} == {r1, r2} (exact rank match, order-independent)."""
    return {rank_a, rank_b} == {r1, r2}


def find_matching_categories(rank_a: str, rank_b: str) -> list[dict]:
    """
    Given two player ranks, return list of dicts:
    { category, pair_slot, pair_label }
    for every category+slot where this doubles pair is valid (exact match).
    """
    results = []
    for cat_key, cat in MATCH_CATEGORIES.items():
        for slot, (r1, r2) in cat["pairs"].items():
            if pair_matches(rank_a, rank_b, r1, r2):
                results.append({
                    "category": cat_key,
                    "pair_slot": slot,
                    "pair_label": f"จับคู่แบบที่ {slot} ({r1}–{r2})",
                })
    return results


def find_nearest_categories(rank_a: str, rank_b: str) -> list[dict]:
    """
    When no exact match exists, find the closest valid pair slots (by total rank distance).
    Returns list of { category, pair_label, distance, hint } sorted by distance.
    Only returns results if total distance <= 2 (1 step each player at most).
    """
    idx_a = RANK_INDEX.get(rank_a, 0)
    idx_b = RANK_INDEX.get(rank_b, 0)
    candidates = []
    for cat_key, cat in MATCH_CATEGORIES.items():
        for slot, (r1, r2) in cat["pairs"].items():
            for (ia, ib) in [(RANK_INDEX[r1], RANK_INDEX[r2]), (RANK_INDEX[r2], RANK_INDEX[r1])]:
                dist = abs(idx_a - ia) + abs(idx_b - ib)
                if dist == 0:
                    continue
                if dist > 2:
                    continue
                # only suggest if players need to go UP (not down)
                if ia < idx_a or ib < idx_b:
                    continue
                need_a = RANKS[ia] if idx_a != ia else None
                need_b = RANKS[ib] if idx_b != ib else None
                hints = []
                if need_a:
                    hints.append(f"{rank_a}→{need_a}")
                if need_b:
                    hints.append(f"{rank_b}→{need_b}")
                candidates.append({
                    "category": cat_key,
                    "pair_label": f"จับคู่แบบที่ {slot} ({r1}–{r2})",
                    "distance": dist,
                    "hint": ", ".join(hints),
                })
    # deduplicate by category+pair_label, keep lowest distance
    seen = {}
    for c in sorted(candidates, key=lambda x: x["distance"]):
        key = (c["category"], c["pair_label"])
        if key not in seen:
            seen[key] = c
    return list(seen.values())


def rank_gap_warning(rank_a: str, rank_b: str) -> str | None:
    """Return a Thai warning string if the rank gap is considered too large (>3 levels)."""
    gap = abs(RANK_INDEX.get(rank_a, 0) - RANK_INDEX.get(rank_b, 0))
    if gap > 3:
        return (
            f"⚠️ มือห่างกันมาก ({rank_a} vs {rank_b}) — ต่างกัน {gap} ระดับ  \n"
            "ไม่แนะนำให้จับคู่ เนื่องจากไม่สมดุล"
        )
    return None


def check_team_categories(players: list[dict]) -> dict:
    """
    Given a list of player dicts (each with 'name' and 'rank'),
    find all valid category pairings for any 2-player combo in the list.
    Returns dict keyed by category with list of valid pairings.
    """
    results = {}
    n = len(players)
    for i in range(n):
        for j in range(i + 1, n):
            pa = players[i]
            pb = players[j]
            matches = find_matching_categories(pa["rank"], pb["rank"])
            for m in matches:
                cat = m["category"]
                if cat not in results:
                    results[cat] = []
                results[cat].append({
                    "player_a": pa["name"],
                    "rank_a": pa["rank"],
                    "player_b": pb["name"],
                    "rank_b": pb["rank"],
                    "pair_slot": m["pair_slot"],
                    "pair_label": m["pair_label"],
                })
    return results
