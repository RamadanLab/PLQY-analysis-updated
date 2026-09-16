

import logging
from pathlib import Path
import re
import sys
from gooey import Gooey, GooeyParser
import matplotlib.pyplot as plt
import numpy as np

from plqy import compute_plqy, remove_stray_light
from plotting import generate_plqy_figure
from utils import (
    combine_short_long_spectra,
    load_and_interpolate_calibration,
    load_spectrum_file,
    scale_baseline_and_time,
    trim_spectrum,
)

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.__stdout__)],
    force = True,
)
logger = logging.getLogger("PLQY Calculator")


@Gooey(
    program_name="PLQY Calculator",
    advanced=True,
    default_size=(850, 700),
    show_success_modal=False,
    return_to_config=True,
    tabbed_groups=True,
)
def main():
    parser = GooeyParser(description="PLQY Calculator")

    # Required files
    req = parser.add_argument_group("Inputs", gooey_options={"columns": 2})
    req.add_argument(
        "-sp",
        "--short_path",
        required=True,
        type=str,
        widget="FileChooser",
        help="Path to the '_short_in.txt' file (e.g. 'sample_short_in.txt')",
        gooey_options={"wildcard": "IN files (*_in.txt)|*_in.txt|All files (*.*)|*.*"},
    )

    req.add_argument(
        "-st",
        "--short_time",
        default=100,
        type=float,
        help="Short integration time in ms",
    )

    req.add_argument(
        "-lp",
        "--long_path",
        type=str,
        default="",
        widget="FileChooser",
        help="Path to long exposure 'long_in.txt' file",
    )
    req.add_argument(
        "-lt",
        "--long_time",
        default=5000,
        type=float,
        help="Integration time for long measurement in ms",
    )
  
    req.add_argument(
        "-c",
        "--common",
        default = False,
        action = 'store_true',
        help="Use common background ('bckg.txt') and empty ('empty.txt') files in directory.",
    )

    req.add_argument(
        "-sl",
        "--stray_light",
        default=False,
        action = 'store_true',
        help="Removes stray light background (Recommended).",
    )

    req.add_argument(
        "-plr",
        "--pl_range",
        nargs=2,
        default=[560, 850],
        type=float,
        help="PL detection band (min max)",
    )

    configs = parser.add_argument_group("Experimental configurations", gooey_options={"columns": 2})

    configs.add_argument(
        "-lr",
        "--laser_range",
        nargs=2,
        default=[395, 415],
        type=float,
        help="Laser band (min max)",
    )

    configs.add_argument(
        "-cal",
        "--cal_path",
        type=str,
        widget="FileChooser",
        help="Path to calibration file",
        default = '2024-08-02_PLQYCalibrationfile2.txt',
        gooey_options={"wildcard": "Text files (*.txt)|*.txt|All files (*.*)|*.*"},
    )

    configs.add_argument(
        "-di",
        "--dark_indices",
        nargs=2,
        default=[20, 50],
        type=int,
        help="Laser band (min max)",
    )

    configs.add_argument(
        "-trimidxs",
        "--trim_indices",
        nargs = 2,
        type = int,
        default = [4,-5],
        help = "Indices to trim due to hot pixels. Default options should be used for the QEPro spectrometer [08/09/2026]"

    )

    configs.add_argument(
        "-cor",
        "--correction_factor",
        type = float,
        default = 20,
        help = "Optical fibre - spectrometer coupling factor. Last measured: xx/xx/xxx"

    )

    args = parser.parse_args()

    short_in_path = Path(args.short_path).resolve()
    work_dir = short_in_path.parent
    short_name = short_in_path.name

    logger.info("Processing sample: %s", short_name)

    
    out_path = work_dir / short_name.replace("in.txt", "out.txt")
    if not out_path.exists():
        logger.warning('Could not find exact match for out measurement')
        out_path = work_dir / re.sub(r"_spot\d+", "", short_name).replace("in.txt", "out.txt")
        logger.warning("Using generic out measurement: %s", out_path)

    # File naming
    if args.common:
        bckg_path = work_dir / "bckg.txt"
        empty_path = work_dir / "empty.txt"

    else:
        bckg_path = work_dir / short_name.replace("in.txt", "bckg.txt")
        empty_path = work_dir / short_name.replace("in.txt", "empty.txt")

   
    raw_in = load_spectrum_file(short_in_path)
    raw_bckg = load_spectrum_file(bckg_path)
    raw_empty = load_spectrum_file(empty_path)
    raw_out = load_spectrum_file(out_path)

 
    wavelengths = raw_in[:, 0]

    # Integration time trim and normalise
    wavelengths, raw_in_trimmed, raw_out_trimmed, raw_empty_trimmed, raw_bckg_trimmed = [trim_spectrum(data, args.trim_indices) for data in (wavelengths, raw_in[:, 1], raw_out[:, 1], raw_empty[:, 1], raw_bckg[:, 1])]
    short_in_proc = scale_baseline_and_time(raw_in_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices)
    short_out_proc = scale_baseline_and_time(raw_out_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices)
    short_empty_proc = scale_baseline_and_time(raw_empty_trimmed - raw_bckg_trimmed, wavelengths, args.short_time, args.dark_indices)

   
    if args.long_path and Path(args.long_path).exists():
        logger.info("Splicing long integration time spectrum...")
        long_in_path = Path(args.long_path).resolve()

        long_out_path = work_dir / long_in_path.name.replace("in.txt", "out.txt")

        if not long_out_path.exists():
            logger.warning('Could not find exact match for long_out measurement')
            long_out_path = work_dir / re.sub(r"_spot\d+", "", long_in_path.name).replace("in.txt", "out.txt")
            logger.warning("Using generic long_out measurement: %s", long_out_path)

        if args.common:
            long_bckg_path = work_dir / "long_bckg.txt"
            long_empty_path = work_dir / "long_empty.txt"
        else:
            long_bckg_path = work_dir / long_in_path.name.replace("in.txt", "bckg.txt")
            long_empty_path = work_dir / long_in_path.name.replace("in.txt", "empty.txt")

        

        raw_long_in = load_spectrum_file(long_in_path)
        raw_long_bckg = load_spectrum_file(long_bckg_path)
        raw_long_empty = load_spectrum_file(long_empty_path)
        raw_long_out = load_spectrum_file(long_out_path)

        raw_long_in_trimmed, raw_long_out_trimmed, raw_long_empty_trimmed, raw_long_bckg_trimmed = [trim_spectrum(data, args.trim_indices) for data in (raw_long_in[:, 1], raw_long_out[:, 1], raw_long_empty[:, 1], raw_long_bckg[:, 1])]

        long_in_proc = scale_baseline_and_time(raw_long_in_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices)
        long_out_proc = scale_baseline_and_time(raw_long_out_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices)
        long_empty_proc = scale_baseline_and_time(raw_long_empty_trimmed - raw_long_bckg_trimmed, wavelengths, args.long_time, args.dark_indices)

        counts_in = combine_short_long_spectra(short_in_proc, long_in_proc, wavelengths, tuple(args.laser_range))
        counts_out = combine_short_long_spectra(short_out_proc, long_out_proc, wavelengths, tuple(args.laser_range))
        counts_empty = combine_short_long_spectra(short_empty_proc, long_empty_proc, wavelengths, tuple(args.laser_range))
    else:
        counts_in = short_in_proc
        counts_out = short_out_proc
        counts_empty = short_empty_proc

    # Interpolate & apply calibration
    if args.cal_path:
        cal = load_and_interpolate_calibration(args.cal_path, wavelengths)
    else:
        logger.warning("No calibration file supplied. Using uncalibrated counts.")
        cal = np.ones_like(wavelengths)

    spec_in = counts_in * cal
    spec_out = counts_out * cal
    spec_empty = counts_empty * cal

    # Stray light correction
    if args.stray_light:
        spec_in, spec_out, spec_empty = remove_stray_light(
            spec_in,
            spec_out,
            spec_empty,
            wavelengths,
            stray_range=(370.0, 390.0),
            pl_range=tuple(args.pl_range),
        )

    # Compute PLQY
    result, centre, fwhm, voigt_fit, fitlabel = compute_plqy(
        wavelengths=wavelengths,
        spec_in=spec_in,
        spec_out=spec_out,
        spec_empty=spec_empty,
        laser_range=tuple(args.laser_range),
        pl_range=tuple(args.pl_range),
        correction_factor = args.correction_factor,
    )

    # Print summary to Gooey Console
    print("\n" + "=" * 40)
    print(f"RESULTS ({short_name})")
    print("=" * 40)
    print(f"PLQY         : {result.plqy_percent:.2f} %")
    print(f"Absorptance  : {result.absorptance_percent:.2f} %")
    print(f"Optical Dens.: {result.optical_density:.2f}")
    #print(f"Laser Power  : {result.laser_power_val:.2f} ± {result.laser_power_error:.2f} {result.laser_power_unit}")
    print(f"Peak centre  : {result.peak_centre_nm:.2f} nm")
    print(f"FWHM         : {result.fwhm_nm:.2f} nm")
    print("=" * 40 + "\n")

    # Save Output plot
    fig = generate_plqy_figure(
        result=result,
        laser_range=tuple(args.laser_range),
        pl_range=tuple(args.pl_range),
        voigt_fit=voigt_fit,
        fitlabel=fitlabel,
        short_time_ms=args.short_time,
    )

    pdf_out_path = work_dir / short_name.replace("in.txt", "fig_test.pdf")
    txt_out_path = work_dir / short_name.replace("in.txt", "spectra.txt")

    fig.savefig(pdf_out_path, format="pdf", bbox_inches="tight")
    logger.info("Saved plot to %s", pdf_out_path.name)

    spec_matrix = np.c_[wavelengths, spec_empty, spec_in, spec_out, spec_in - spec_out]
    np.savetxt(
        txt_out_path,
        spec_matrix,
        delimiter="\t",
        fmt="%.5e",
        header="Wavelength\tempty\tin\tout\tproc",
        comments="",
    )
    logger.info("Saved spectrum matrix to %s", txt_out_path.name)

    plt.show()


if __name__ == "__main__":
    main()
