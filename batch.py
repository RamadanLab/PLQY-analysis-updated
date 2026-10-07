import argparse
import logging
from pathlib import Path
import re
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plqy import compute_plqy, remove_stray_light
from plotting import generate_plqy_figure
from utils import (
    combine_short_long_spectra,
    load_and_interpolate_calibration,
    load_spectrum_file,
    scale_baseline_and_time,
    trim_spectrum,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger("Batch PLQY")


class SampleProcessingError(Exception):
    """Raised when a sample cannot be processed (e.g., missing files or bad data)."""
    pass


def process_single_sample(short_in_path: Path, args) -> dict:
    """Processes a single short_in.txt spectrum file and returns a summary dict."""
    work_dir = short_in_path.parent
    short_name = short_in_path.name
    logger.info("=" * 50)
    logger.info("Processing sample: %s", short_name)


    out_path = work_dir / short_name.replace("in.txt", "out.txt")
    if not out_path.exists():
        out_path = work_dir / re.sub(r"_spot\d+", "", short_name).replace("in.txt", "out.txt")
        logger.info("Using generic _out file: %s", out_path)
    
    if not out_path.exists():
        raise SampleProcessingError(
            f"No suitable '_out.txt' file found for sample '{short_name}' (looked for {out_path.name})"
        )


    if args.common:
        bckg_path = work_dir / "bckg.txt"
        empty_path = work_dir / "empty.txt"
    else:
        bckg_path = work_dir / short_name.replace("in.txt", "bckg.txt")
        empty_path = work_dir / short_name.replace("in.txt", "empty.txt")

    if not bckg_path.exists():
        raise SampleProcessingError(f"Background file missing: {bckg_path.name}")
    if not empty_path.exists():
        raise SampleProcessingError(f"Empty file missing: {empty_path.name}")


    short_files = {
        "short_in": short_in_path,
        "bckg": bckg_path,
        "empty": empty_path,
        "out": out_path,
    }
    loaded_spectra = {}

    for file_key, file_path in short_files.items():
        try:
            loaded_spectra[file_key] = load_spectrum_file(file_path)
        except (ValueError, IndexError, IOError, TypeError) as e:
            raise SampleProcessingError(
                f"Failed to parse {file_key} file '{file_path.name}': {e}"
            )

    raw_in = loaded_spectra["short_in"]
    raw_bckg = loaded_spectra["bckg"]
    raw_empty = loaded_spectra["empty"]
    raw_out = loaded_spectra["out"]

    wavelengths = raw_in[:, 0]

    
    wavelengths, raw_in_trimmed, raw_out_trimmed, raw_empty_trimmed, raw_bckg_trimmed = [
        trim_spectrum(data, args.trim_indices)
        for data in (wavelengths, raw_in[:, 1], raw_out[:, 1], raw_empty[:, 1], raw_bckg[:, 1])
    ]

    short_in_proc = scale_baseline_and_time(
        raw_in_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices
    )
    short_out_proc = scale_baseline_and_time(
        raw_out_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices
    )
    short_empty_proc = scale_baseline_and_time(
        raw_empty_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices
    )

 
    long_in_name = short_name.replace("short_in.txt", "long_in.txt")
    long_in_path = work_dir / long_in_name

    if long_in_path.exists():
        logger.info("Found long_in file: %s", long_in_name)
    else:
        escaped_name = re.escape(long_in_name)
        pattern_str = re.sub(r'\d+ms', r'\\d+ms', escaped_name)
        pattern = re.compile(rf"^{pattern_str}")
        matches = [
        file for file in work_dir.iterdir()
        if file.is_file() and pattern.match(file.name)
    ]
        if matches:
            long_in_path = matches[0]
            logger.info("Removed integration time from long_in path: %s", long_in_path.name)
        else:
            logger.warning("No long file found")
            raise SampleProcessingError(f"long_in file missing: {long_in_path.name}")
        
    long_out_path = work_dir / long_in_path.name.replace("in.txt", "out.txt")
    if not long_out_path.exists():
            long_out_path = work_dir / re.sub(r"_spot\d+", "", long_in_name).replace("in.txt", "out.txt")
            logger.info("Removed spot reference from long_out path: %s", long_out_path.name)
            if not long_out_path.exists():
                escaped_name = re.escape(long_out_path.name)
                pattern_str = re.sub(r'\d+ms', r'\\d+ms', escaped_name)
                pattern = re.compile(rf"^{pattern_str}")
                matches = [
                file for file in work_dir.iterdir()
                if file.is_file() and pattern.match(file.name)
            ]
                if matches:
                    long_in_path = matches[0]
                    logger.info("Removed integration time from long_out path: %s", long_out_path.name)
                else:
                    logger.warning("No long file found")
                    raise SampleProcessingError(f"long_out file missing: {long_out_path.name}")


            

    if args.common:
            long_bckg_path = work_dir / "long_bckg.txt"
            long_empty_path = work_dir / "long_empty.txt"
    else:
            long_bckg_path = work_dir / long_in_name.replace("in.txt", "bckg.txt")
            long_empty_path = work_dir / long_in_name.replace("in.txt", "empty.txt")

    if not long_bckg_path.exists() or not long_empty_path.exists():
        raise SampleProcessingError("long_bckg / long_empty file missing.")

    
    long_files = {
            "long_in": long_in_path,
            "long_bckg": long_bckg_path,
            "long_empty": long_empty_path,
            "long_out": long_out_path,
    }
    loaded_long_spectra = {}

    for file_key, file_path in long_files.items():
        try:
            loaded_long_spectra[file_key] = load_spectrum_file(file_path)
        except (ValueError, IndexError, IOError, TypeError) as e:
            raise SampleProcessingError(
                f"Failed to parse {file_key} file '{file_path.name}': {e}"
            )

    raw_long_in = loaded_long_spectra["long_in"]
    raw_long_bckg = loaded_long_spectra["long_bckg"]
    raw_long_empty = loaded_long_spectra["long_empty"]
    raw_long_out = loaded_long_spectra["long_out"]

    (
            raw_long_in_trimmed,
            raw_long_out_trimmed,
            raw_long_empty_trimmed,
            raw_long_bckg_trimmed,
    ) = [
            trim_spectrum(data, args.trim_indices)
            for data in (raw_long_in[:, 1], raw_long_out[:, 1], raw_long_empty[:, 1], raw_long_bckg[:, 1])
    ]

    long_in_proc = scale_baseline_and_time(
            raw_long_in_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices
    )
    long_out_proc = scale_baseline_and_time(
            raw_long_out_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices
    )
    long_empty_proc = scale_baseline_and_time(
            raw_long_empty_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices
    )

    counts_in = combine_short_long_spectra(
            short_in_proc, long_in_proc, wavelengths, tuple(args.laser_range)
        )
    counts_out = combine_short_long_spectra(
            short_out_proc, long_out_proc, wavelengths, tuple(args.laser_range)
        )
    counts_empty = combine_short_long_spectra(
            short_empty_proc, long_empty_proc, wavelengths, tuple(args.laser_range)
        )



    if args.cal_path and Path(args.cal_path).exists():
        cal = load_and_interpolate_calibration(args.cal_path, wavelengths)
    else:
        logger.warning("No calibration file supplied/found. Using uncalibrated counts.")
        cal = np.ones_like(wavelengths)

    spec_in = counts_in * cal
    spec_out = counts_out * cal
    spec_empty = counts_empty * cal

 
    if args.stray_light:
        spec_in, spec_out, spec_empty = remove_stray_light(
            spec_in,
            spec_out,
            spec_empty,
            wavelengths,
            stray_range=(370.0, 390.0),
            pl_range=tuple(args.pl_range),
        )


    try:
        result, centre, fwhm, voigt_fit, fitlabel = compute_plqy(
            wavelengths=wavelengths,
            spec_in=spec_in,
            spec_out=spec_out,
            spec_empty=spec_empty,
            laser_range=tuple(args.laser_range),
            pl_range=tuple(args.pl_range),
            correction_factor=args.correction_factor,
        )
    except Exception as e:
        raise SampleProcessingError(f"PLQY calculation failed: {e}")

  
    try:
        fig = generate_plqy_figure(
            result=result,
            laser_range=tuple(args.laser_range),
            pl_range=tuple(args.pl_range),
            voigt_fit=voigt_fit,
            fitlabel=fitlabel,
            short_time_ms=args.short_time,
        )

        pdf_out_path = work_dir / short_name.replace("in.txt", "fig.pdf")
        txt_out_path = work_dir / short_name.replace("in.txt", "spectra.txt")

        fig.savefig(pdf_out_path, format="pdf", bbox_inches="tight")
        plt.close(fig) 

        spec_matrix = np.c_[wavelengths, spec_empty, spec_in, spec_out, spec_in - spec_out]
        np.savetxt(
            txt_out_path,
            spec_matrix,
            delimiter="\t",
            fmt="%.5e",
            header="Wavelength\tempty\tin\tout\tproc",
            comments="",
        )
    except Exception as e:
        raise SampleProcessingError(f"Failed to generate/save figures or text matrix: {e}")

    return {
        "File Name": short_name,
        "Sample": short_name.replace("_short_in.txt", "").replace("_in.txt", ""),
        "PLQY (%)": round(result.plqy_percent, 4),
        "Absorptance (%)": round(result.absorptance_percent, 4),
        "Optical Density": round(result.optical_density, 4),
        "Peak Centre (nm)": round(result.peak_centre_nm, 2),
        "FWHM (nm)": round(result.fwhm_nm, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Batch PLQY Calculator")

    parser.add_argument(
        "-dir",
        "--directory",
        type=str,
        required=True,
        help="Path to folder containing short_in files",
    )
    parser.add_argument(
        "-st", "--short_time", default=100, type=float, help="Short integration time in ms"
    )
    parser.add_argument(
        "-lt", "--long_time", default=5000, type=float, help="Long integration time in ms"
    )
    parser.add_argument(
        "-c",
        "--common",
        action="store_true",
        default=True,
        help="Use common background (bckg.txt) and empty (empty.txt) files.",
    )
    parser.add_argument(
        "-sl",
        "--stray_light",
        action="store_true",
        default=True,
        help="Removes stray light background.",
    )
    parser.add_argument(
        "-plr",
        "--pl_range",
        nargs=2,
        default=[560, 850],
        type=float,
        help="PL detection band (min max)",
    )
    parser.add_argument(
        "-lr",
        "--laser_range",
        nargs=2,
        default=[395, 415],
        type=float,
        help="Laser band (min max)",
    )
    parser.add_argument(
        "-cal",
        "--cal_path",
        type=str,
        default="2024-08-02_PLQYCalibrationfile2.txt",
        help="Path to calibration file",
    )
    parser.add_argument(
        "-di",
        "--dark_indices",
        nargs=2,
        default=[20, 50],
        type=int,
        help="Dark count index range",
    )
    parser.add_argument(
        "-trimidxs",
        "--trim_indices",
        nargs=2,
        type=int,
        default=[4, -5],
        help="Indices to trim hot pixels",
    )
    parser.add_argument(
        "-cor",
        "--correction_factor",
        type=float,
        default=20,
        help="Fiber coupling correction factor",
    )
    parser.add_argument(
        "-o",
        "--output_csv",
        type=str,
        default="batch_plqy_results.csv",
        help="Name of summary output CSV file",
    )

    args = parser.parse_args()

    target_dir = Path(args.directory).resolve()
    if not target_dir.exists():
        logger.error("Directory not found: %s", target_dir)
        sys.exit(1)

 
    short_files = sorted(list(target_dir.glob("*short_in.txt")))

    if not short_files:
        logger.error("No valid input spectrum files found in %s", target_dir)
        sys.exit(1)

    logger.info("Found %d candidate sample file(s). Processing...", len(short_files))

    results_list = []
    skipped_files = []

    for short_file in short_files:
        try:
            summary = process_single_sample(short_file, args)
            results_list.append(summary)
        except SampleProcessingError as spe:
            logger.error("SKIPPING %s: %s", short_file.name, spe)
            skipped_files.append((short_file.name, str(spe)))
        except Exception as e:
            logger.error("UNEXPECTED ERROR on %s: %s", short_file.name, e, exc_info=True)
            skipped_files.append((short_file.name, f"Unexpected error: {e}"))

    logger.info("=" * 50)
    logger.info(
        "BATCH COMPLETE: Successfully processed %d file(s), Skipped %d file(s).",
        len(results_list),
        len(skipped_files),
    )

    if skipped_files:
        print("\nSkipped Samples Summary:")
        for name, reason in skipped_files:
            print(f" - {name}: {reason}")

    if results_list:
        df = pd.DataFrame(results_list)
        csv_path = target_dir / args.output_csv
        df.to_csv(csv_path, index=False)
        logger.info("Summary saved to CSV: %s", csv_path)
        print("\nProcessed Results:\n")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()