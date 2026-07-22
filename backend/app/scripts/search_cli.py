import argparse
import sys

from app.core.logging import logger
from app.schemas.search import SearchRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Search indexed screenshots.")
    parser.add_argument("query", type=str, help="Search query text")
    parser.add_argument(
        "--top-k", type=int, default=10, help="Number of results (default: 10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score (default: 0.0)",
    )
    args = parser.parse_args()

    from app.services.search_service import SearchService

    service = SearchService()
    request = SearchRequest(query=args.query, top_k=args.top_k, threshold=args.threshold)

    print(f"\nQuery: {request.query}")
    print(f"Top-K: {request.top_k}  |  Threshold: {request.threshold}")
    print("-" * 80)

    response = service.search(request)

    if response.total_results == 0:
        print("\nNo results found.")
        sys.exit(0)

    print(f"\nFound {response.total_results} result(s) in {response.timing.total_ms:.0f} ms")
    print(f"  Embedding: {response.timing.query_embedding_ms:.0f} ms")
    print(f"  Vector search: {response.timing.vector_search_ms:.0f} ms")
    print()

    for i, result in enumerate(response.results, 1):
        print(f"{i:>2}. [{result.score:.4f}] {result.image_id}")
        print(f"    Path: {result.image_path}")
        text_preview = result.text[:120].replace("\n", " ")
        if text_preview:
            print(f"    Text: {text_preview}...")
        print()


if __name__ == "__main__":
    main()
