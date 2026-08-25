from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from decimal import Decimal

from app import create_app
from app.calculator import calculate_estimate


def main() -> None:
    app = create_app()
    with app.app_context():
        result = calculate_estimate(
            job_type="bathroom_tiling",
            area_m2=Decimal("4"),
            region="pl",
        )
    print(f"{result['job_name']}")
    print(f"Total: {result['total_price']} {result['currency']}")
    print(f"Duration: {result['estimated_duration_days']} days ({result['estimated_labor_hours']} h)")
    print("Materials:")
    for item in result["materials"]:
        print(f"  {item['name']}: {item['quantity']} {item['unit']} = {item['total']} {item['currency']}")
    print("Works:")
    for item in result["works"]:
        print(f"  {item['name']}: {item['quantity']} {item['unit']} = {item['total']} {item['currency']}")
    print("Sequence:")
    for step in result["sequence"]:
        print(f"  {step['order']}. {step['name']}")


if __name__ == "__main__":
    main()
