import argparse
import sys

from app.core.logging import logger
from app.schemas.explain import ExplainRequest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explain why screenshots match a search query."
    )
    parser.add_argument("query", type=str, help="Search query text")
    parser.add_argument(
        "--top-k", type=int, default=10, help="Number of results to explain (default: 10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score (default: 0.0)",
    )
    parser.add_argument(
        "--image-ids",
        type=str,
        nargs="*",
        default=None,
        help="Specific image IDs to explain (skips search)",
    )
    args = parser.parse_args()

    from app.services.explanation_service import ExplanationService

    service = ExplanationService()
    request = ExplainRequest(
        query=args.query,
        top_k=args.top_k,
        threshold=args.threshold,
        image_ids=args.image_ids,
    )

    print(f"\nQuery: {request.query}")
    print(f"Top-K: {request.top_k}  |  Threshold: {request.threshold}")
    if args.image_ids:
        print(f"Image IDs: {', '.join(args.image_ids)}")
    print("-" * 80)

    response = service.explain(request)

    if response.total_explanations == 0:
        print("\nNo results to explain.")
        sys.exit(0)

    print(
        f"\n{response.total_explanations} explanation(s) in {response.timing.total_ms:.0f} ms"
    )
    print(f"  Search: {response.timing.search_ms:.0f} ms")
    print(f"  Explain: {response.timing.explain_ms:.0f} ms")
    print()

    for i, item in enumerate(response.explanations, 1):
        cache_tag = " [CACHED]" if item.cache_hit else ""
        print(f"{i:>2}. [{item.score:.4f}] {item.image_id}{cache_tag}")
        print(f"    Path: {item.image_path}")
        if item.explanation:
            print(f"    Explanation: {item.explanation}")
        if item.latency_ms > 0:
            print(f"    API Latency: {item.latency_ms:.0f} ms")
        print()


if __name__ == "__main__":
    main()
