import math

class LCG:
    def __init__(self, seed=123, a=1664525, c=1013904223, M=2**32):
        self.x = seed
        self.a = a
        self.c = c
        self.M = M
        self.used = 0

    def NextRandom(self):
        self.x = (self.a * self.x + self.c) % self.M
        self.used += 1
        return self.x / self.M

def U_ab(rng: LCG, a: float, b: float) -> float:
    return a + (b - a) * rng.NextRandom()

def simulate_queue(
    servers: int,
    capacity: int,
    rng: LCG,
    max_randoms: int,
    arrival_a: float = 2.0,
    arrival_b: float = 5.0,
    service_a: float = 3.0,
    service_b: float = 5.0,
):
    time_now = 0.0
    in_system = 0
    losses = 0
    served = 0

    next_arrival = U_ab(rng, arrival_a, arrival_b)
    departures = [math.inf] * servers
    state_times = [0.0] * (capacity + 1)
    last_t = 0.0

    def advance_time(current_n: int, new_t: float):
        nonlocal last_t
        dt = new_t - last_t
        if dt < 0:
            raise RuntimeError("Negative elapsed time.")
        state_times[current_n] += dt
        last_t = new_t

    while rng.used < max_randoms:
        next_departure = min(departures)
        if next_arrival <= next_departure:
            advance_time(in_system, next_arrival)
            time_now = next_arrival

            if in_system < capacity:
                in_system += 1
                if math.inf in departures:
                    idx = departures.index(math.inf)
                    departures[idx] = time_now + U_ab(rng, service_a, service_b)
            else:
                losses += 1

            next_arrival = time_now + U_ab(rng, arrival_a, arrival_b)
        else:
            idx = departures.index(next_departure)
            advance_time(in_system, next_departure)
            time_now = next_departure

            in_system -= 1
            served += 1
            if in_system >= servers:
                departures[idx] = time_now + U_ab(rng, service_a, service_b)
            else:
                departures[idx] = math.inf

        if rng.used >= max_randoms:
            break

    total_time = time_now
    state_probs = (
        [te / total_time for te in state_times] if total_time > 0 else [0.0] * (capacity + 1)
    )
    attempts = losses + served
    blocking_prob = (losses / attempts) if attempts > 0 else 0.0
    avg_busy_servers = sum(min(k, servers) * p for k, p in enumerate(state_probs))
    utilization = (avg_busy_servers / servers) if servers > 0 else 0.0

    return {
        "servers": servers,
        "capacity": capacity,
        "losses": losses,
        "served_clients": served,
        "total_time": total_time,
        "blocking_prob": blocking_prob,
        "utilization": utilization,
        "state_times": state_times,
        "state_probs": state_probs,
    }

if __name__ == "__main__":
    MAX_RANDOMS = 100_000
    CAPACITY = 5

    def print_results(res: dict, title: str):
        print(f"\n=== {title} ===")
        print(f"Servers = {res['servers']} | Capacity = {res['capacity']}")
        print(f"Total time: {res['total_time']:.4f}")
        print(f"Served clients: {res['served_clients']}")
        print(f"Losses: {res['losses']}")
        print(f"Blocking probability: {res['blocking_prob']:.6f}")
        print(f"Average utilization per server: {res['utilization']:.6f}")
        print("\nState probabilities (0..K):")
        for k, p in enumerate(res["state_probs"]):
            print(f"  P(N={k}) = {p:.6f}")

    rng1 = LCG(seed=123)
    r1 = simulate_queue(servers=1, capacity=CAPACITY, rng=rng1, max_randoms=MAX_RANDOMS)
    print_results(r1, f"G/G/1/{CAPACITY}")

    rng2 = LCG(seed=123)
    r2 = simulate_queue(servers=2, capacity=CAPACITY, rng=rng2, max_randoms=MAX_RANDOMS)
    print_results(r2, f"G/G/2/{CAPACITY}")