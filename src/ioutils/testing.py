from .fio import FioDirTest, FioFileTest, FioResult
import itertools
import pandas as pd
import os
import logging
import uuid

__ALL_MODES=["read","write","randread","randwrite","readwrite","randrw"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def main():
    import argparse

    parser = argparse.ArgumentParser(description="-- IO Testing Utility --")

    parser.add_argument("input", help="directory (or file) which should be tested")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=__ALL_MODES+["all"],
        help="Choose which mode(s) to run, separated by whitespace",
    )
    parser.add_argument(
        "--basename",
        "-n",
        type=str,
        default="fioresult",
        help="Base name for result files (default: fioresult)",
    )
    parser.add_argument(
        "--byof",
        action="store_true",
        help="Bring your own file in directory and test read with this (helpful to test how caching affects speed)",
    )

    args = parser.parse_args()


    if "all" in args.modes:
        args.modes = __ALL_MODES

    if args.byof:
        for write_mode in ["write","randwrite","randrw","readwrite"]:
            if write_mode in args.modes:
                print(f"removing {write_mode} from mode list!!")
                args.modes.remove(write_mode)

    # Example: parameter_ranges = {"bs": ["4K", "64K"], "size": ["10M", "100M"]}
    parameter_ranges = {
        "runtime":[30],
        "bs": ["4K","4M"],
        "size": ["100M","1G"],
    }

    # Build all combinations of parameters
    param_names = list(parameter_ranges.keys())
    param_values = list(parameter_ranges.values())
    combos = list(itertools.product(*param_values))

    results = []
    for mode in args.modes:
        for combo in combos:
            params = dict(zip(param_names, combo))
            param_str = "_".join(f"{k}-{v}" for k, v in params.items())
            unique_id = uuid.uuid4().hex[:8]
            name = f"{args.basename}_{mode}_{param_str}_{unique_id}"
            fio_args = dict(name=name, rw=mode, **params)
            logging.info(f"Running fio test: {name} with params: {fio_args}")
            if args.byof:
                fio_args.pop("size")
                
            fio = FioFileTest(**fio_args) if args.byof else FioDirTest(**fio_args)
            fio_result = fio.run_test(path=args.input)
            df = FioResult.from_fio_json(fio_result)
            for k, v in fio_args.items():
                df[k] = v
            results.append(df)
            outdir = "fio_scan_results"
            os.makedirs(outdir, exist_ok=True)
            parquet_path = os.path.join(outdir, f"{name}.parquet")
            df.to_parquet(parquet_path)
            logging.info(f"Saved results to {parquet_path}")

    # Merge all results
    if results:
        merged = pd.concat(results, ignore_index=True)
        merged_path = f"fio_scan_results/{args.basename}_all_results.parquet"
        merged.to_parquet(merged_path)
        logging.info(f"Merged all results and saved to {merged_path}")


