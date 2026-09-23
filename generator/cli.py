import argparse
import json
import os
import sys
import time
from multiprocessing import Pool, cpu_count

from .indexer import SQLiteIndexer
from .worker import init_worker, render_thread_chunk


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate static HTML pages and SQLite index from ModMail logs."
    )
    parser.add_argument(
        "--input", "-i", default="logs.jsonl", help="Path to input logs.jsonl"
    )
    parser.add_argument("--output", "-o", default="dist", help="Output directory")
    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=250,
        help="Batch size for worker processes",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=max(1, cpu_count() - 1),
        help="Worker process count",
    )
    return parser.parse_args()


def stream_batches(filepath, batch_size):
    batch = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            batch.append(json.loads(line))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def main():
    args = parse_args()
    if not os.path.exists(args.input):
        print(f"Error: input file {args.input} does not exist", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    threads_dir = os.path.join(args.output, "threads")
    os.makedirs(threads_dir, exist_ok=True)

    db_path = os.path.join(args.output, "index.db")
    indexer = SQLiteIndexer(db_path)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    start_time = time.time()
    print(
        f"Starting generation: input={args.input}, output={args.output}, concurrency={args.concurrency}"
    )

    total_threads = 0
    with Pool(
        processes=args.concurrency, initializer=init_worker, initargs=(template_dir,)
    ) as pool:
        tasks = (
            (batch, args.output)
            for batch in stream_batches(args.input, args.batch_size)
        )
        for chunk_results in pool.imap_unordered(render_thread_chunk, tasks):
            indexer.insert_batch(chunk_results)
            total_threads += len(chunk_results)
            if total_threads % 2000 == 0 or total_threads == 18133:
                print(f"Generated {total_threads} pages...")

    print("Finalizing SQLite database index...")
    indexer.close()

    elapsed = time.time() - start_time
    print(
        f"Done! Successfully generated {total_threads} thread pages and SQLite index in {elapsed:.2f} seconds."
    )


if __name__ == "__main__":
    main()
