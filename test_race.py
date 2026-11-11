import argparse
import asyncio

import httpx


async def run_race(base_url: str, mode: str) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:
        product = (await client.get("/resource/1")).json()["data"]
        product.pop("id")
        product["stok"] = 1
        reset = await client.put("/resource/1", json=product)
        reset.raise_for_status()

        payload = {"product_id": 1, "quantity": 1, "cashier_name": "Race Test"}
        first, second = await asyncio.gather(
            client.post("/transactions", json=payload),
            client.post("/transactions", json=payload),
        )
        final_product = (await client.get("/resource/1")).json()["data"]

    successful = sum(response.status_code == 202 for response in (first, second))
    print(f"Mode: {mode}")
    print("Response 1:", first.status_code, first.json())
    print("Response 2:", second.status_code, second.json())
    print("Final stock:", final_product["stok"])
    print("Successful transactions:", successful)

    expected = 2 if mode == "unsafe" else 1
    if successful != expected:
        raise SystemExit(
            f"Expected {expected} successful transaction(s), got {successful}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pelita POS stock race experiment")
    parser.add_argument("--mode", choices=("unsafe", "safe"), required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(run_race(arguments.base_url, arguments.mode))
