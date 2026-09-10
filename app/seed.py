"""Seed the DB with a small, fixed set of LLD problems."""
from app.models.orm import Problem

PROBLEMS = [
    dict(
        slug="parking-lot",
        title="Parking Lot System",
        difficulty="medium",
        description=(
            "Design a parking lot that supports multiple vehicle types (motorcycle, car, bus) "
            "and multiple spot sizes. The system should assign an available spot to an incoming "
            "vehicle, free it up on exit, and calculate a parking fee based on duration."
        ),
        requirements=[
            "Support at least 3 vehicle types with different spot-size needs",
            "Track which spots are free/occupied",
            "Assign the correct spot type to a vehicle on entry",
            "Free the spot and calculate a fee on exit",
            "Be able to add a new vehicle type later without rewriting the spot-assignment logic",
        ],
        expected_entities=["Vehicle", "ParkingSpot", "ParkingLot", "Ticket"],
        hints_for_variation=[
            "fee calculation and spot-fit rules differ per vehicle type",
        ],
    ),
    dict(
        slug="vending-machine",
        title="Vending Machine",
        difficulty="easy",
        description=(
            "Design a vending machine that accepts coins/cash, lets a user select an item, "
            "dispenses it if in stock and payment is sufficient, and returns change."
        ),
        requirements=[
            "Track inventory per item slot with quantity",
            "Accept payment incrementally and track balance",
            "Handle insufficient stock and insufficient payment as distinct cases",
            "Return change correctly",
            "Model the machine's state (idle, has-money, dispensing) explicitly",
        ],
        expected_entities=["Item", "Inventory", "VendingMachine", "Payment"],
        hints_for_variation=[
            "machine behavior differs across idle / money-inserted / dispensing states",
        ],
    ),
    dict(
        slug="elevator-system",
        title="Elevator System",
        difficulty="hard",
        description=(
            "Design an elevator control system for a building with multiple elevators. "
            "The system should handle external hall calls (up/down from a floor) and internal "
            "cabin requests, and decide which elevator services which request."
        ),
        requirements=[
            "Support multiple elevators in one building",
            "Handle both hall calls (from a floor) and cabin requests (from inside)",
            "Decide which elevator should service a given request",
            "Model an elevator's direction and current state explicitly",
            "Allow the dispatch strategy (e.g. nearest-elevator vs least-busy) to be swapped later",
        ],
        expected_entities=["Elevator", "ElevatorController", "Request", "Floor"],
        hints_for_variation=[
            "the dispatch/scheduling strategy is a separate concern from the elevator itself "
            "and is likely to change or be compared against alternatives",
        ],
    ),
]


def seed_problems(db):
    existing = {p.slug for p in db.query(Problem).all()}
    for data in PROBLEMS:
        if data["slug"] not in existing:
            db.add(Problem(**data))
    db.commit()
